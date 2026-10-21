"""GNOME 51 GDM resource-overlay preparation and reversible deployment."""
import ast
import base64
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
RESOURCE = Path('/usr/share/gnome-shell/gnome-shell-theme.gresource')
UNIT = Path('/usr/lib/systemd/user/org.gnome.Shell@.service')
SESSION = Path('/usr/lib/systemd/user/gnome-session@gnome-login.target.d/gnome-login.session.conf')
DEPLOY = Path('/usr/local/share/nothingos-gdm')
DROPIN = Path('/etc/systemd/user/org.gnome.Shell@gdm.service.d/60-nothingos-theme.conf')
BACKUPS = Path('/var/lib/nothingos-gdm/backups')
CSS_NAMES = ('gnome-shell-light.css', 'gnome-shell-dark.css')
OWNER = 'nothingos-gdm-v1'
SERVICE = 'org.gnome.Shell@gdm.service'
HEADER = '# Managed by NothingOS GDM v1\n'
DROPIN_TEXT = HEADER + '[Service]\nEnvironment="G_RESOURCE_OVERLAYS=/org/gnome/shell/theme=/usr/local/share/nothingos-gdm"\n'
MAX_IMAGE = 100 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(command, **kwargs):
    return subprocess.check_output(command, text=True, **kwargs)


def shell_version():
    return run(['gnome-shell', '--version']).strip().split()[-1]


def rooted(root, path):
    return root / path.relative_to('/')


def check_host(root=Path('/')):
    version = shell_version()
    if version.split('.')[0] != '51':
        raise ValueError('Only GNOME Shell 51 is validated; do not install on this release.')
    if '--mode=%i' not in rooted(root, UNIT).read_text():
        raise ValueError('Unexpected GNOME Shell service template')
    if SERVICE not in rooted(root, SESSION).read_text():
        raise ValueError('Unexpected GDM session service')
    return version


def check_font():
    rows = run(['fc-match', '-f', '%{family}\n%{file}\n', 'JetBrains Mono']).splitlines()
    if len(rows) < 2 or rows[0].split(',')[0] != 'JetBrains Mono':
        raise ValueError('Install JetBrains Mono system-wide before applying this theme.')
    font = Path(rows[1]).resolve()
    if not any(font.is_relative_to(base) for base in [Path('/usr/share/fonts'), Path('/usr/local/share/fonts')]):
        raise ValueError('JetBrains Mono must be installed system-wide, not in a private home.')


def select_wallpaper(settings, override):
    if override is not None:
        path = Path(override).expanduser()
    else:
        key = 'picture-uri-dark' if settings.get('color-scheme') == 'prefer-dark' else 'picture-uri'
        value = settings.get(key) or settings.get('picture-uri', '')
        uri = urlsplit(value)
        if uri.scheme != 'file' or uri.netloc not in ('', 'localhost') or uri.query or uri.fragment:
            raise ValueError('Wallpaper must be an existing local file URI.')
        path = Path(unquote(uri.path))
    if not path.is_file():
        raise ValueError(f'Wallpaper is missing or unreadable: {path}')
    return path.resolve()


def desktop_settings():
    result = {}
    for schema, key in [('org.gnome.desktop.interface', 'color-scheme'),
                        ('org.gnome.desktop.background', 'picture-uri'),
                        ('org.gnome.desktop.background', 'picture-uri-dark')]:
        result[key] = ast.literal_eval(run(['gsettings', 'get', schema, key]).strip())
    return result


def native_styles():
    return json.loads(run(['gjs', str(HERE / 'native-theme.js'), 'extract', str(RESOURCE)]))


def image_info(path):
    return json.loads(run(['gjs', str(HERE / 'native-theme.js'), 'image', str(path)]))


def validate_css(paths):
    environment = dict(os.environ)
    environment['GI_TYPELIB_PATH'] = '/usr/lib/gnome-shell:/usr/lib/mutter-51'
    environment['LD_LIBRARY_PATH'] = '/usr/lib/gnome-shell:/usr/lib/mutter-51'
    run(['gjs', str(HERE / 'native-theme.js'), 'validate', *map(str, paths)], env=environment)


def image_extension(data):
    if data.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'webp'
    raise ValueError('Wallpaper bytes are not JPEG, PNG or WebP.')


def blur_svg(content, info, radius):
    """Code-native SVG filter, rendered once before installation, with no file references."""
    width, height = info['width'], info['height']
    scale = min(1, 1920 / width, 1080 / height)
    rendered_width = max(1, round(width * scale))
    rendered_height = max(1, round(height * scale))
    sigma = radius * height / 1080
    mime = {'jpg': 'jpeg', 'png': 'png', 'webp': 'webp'}[image_extension(content)]
    encoded = base64.b64encode(content).decode('ascii')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{rendered_width}" height="{rendered_height}" '
            f'viewBox="0 0 {width} {height}">'
            '<defs><filter id="blur" x="0" y="0" width="100%" height="100%" '
            'color-interpolation-filters="sRGB">'
            f'<feGaussianBlur stdDeviation="{sigma:.6f}" edgeMode="duplicate"/>'
            '</filter></defs>'
            f'<image width="{width}" height="{height}" preserveAspectRatio="none" '
            f'href="data:image/{mime};base64,{encoded}" filter="url(#blur)"/></svg>')


def blur_wallpaper(content, info, radius):
    if not math.isfinite(radius) or not 0 <= radius <= 128:
        raise ValueError('Blur must be a finite number from 0 to 128 pixels.')
    if radius == 0:
        return content
    if shutil.which('rsvg-convert') is None:
        raise ValueError('rsvg-convert is required for blur; install librsvg or use --blur 0.')
    result = subprocess.run(['rsvg-convert', '--format=png'],
                            input=blur_svg(content, info, radius).encode(),
                            capture_output=True, check=True, timeout=60)
    if image_extension(result.stdout) != 'png':
        raise ValueError('Blur renderer did not return a PNG image.')
    return result.stdout


def prepare(output, wallpaper=None, *, blur=32):
    version = check_host()
    check_font()
    image = select_wallpaper(desktop_settings() if wallpaper is None else {}, wallpaper)
    if image.stat().st_size > MAX_IMAGE:
        raise ValueError('Wallpaper exceeds 100 MiB.')
    info = image_info(image)
    content = blur_wallpaper(image.read_bytes(), info, blur)
    name = 'wallpaper.' + image_extension(content)
    resource_hash = digest(RESOURCE.read_bytes())
    styles = native_styles()
    rules = (HERE / 'login.css').read_text().replace('@WALLPAPER@', (DEPLOY / name).as_uri())
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    if output.is_symlink() or any(output.iterdir()):
        raise ValueError('Choose an empty, nonsymlink output directory.')
    os.chmod(output, 0o700)
    try:
        for css in CSS_NAMES:
            (output / css).write_text(styles[css] + '\n\n' + rules)
        (output / name).write_bytes(content)
        validate_css([output / css for css in CSS_NAMES])
        if digest(RESOURCE.read_bytes()) != resource_hash:
            raise ValueError('GNOME resources changed during preparation; prepare again.')
        files = {p.name: digest(p.read_bytes()) for p in output.iterdir()}
        manifest = {'format': 1, 'owner': OWNER, 'shell_version': version,
                    'resource_sha256': resource_hash, 'service': SERVICE, 'files': files,
                    'wallpaper_effect': {'blur_px': blur, 'reference_height': 1080,
                                         'pre_rendered': True}}
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    except Exception:
        for path in output.iterdir():
            path.unlink()
        raise
    return output.resolve()


def no_symlinks(path):
    for item in [path, *path.parents]:
        if item.is_symlink():
            raise ValueError(f'Refusing symlink target: {item}')


def read_bundle(bundle):
    no_symlinks(bundle)
    if any(p.is_symlink() or not p.is_file() for p in bundle.iterdir()):
        raise ValueError('Bundle must contain only regular nonsymlink files.')
    if not (bundle / 'manifest.json').is_file():
        raise ValueError('Missing owned theme manifest.')
    manifest = json.loads((bundle / 'manifest.json').read_text())
    files = manifest.get('files', {})
    pictures = set(files) - set(CSS_NAMES)
    if (manifest.get('format') != 1 or manifest.get('owner') != OWNER or
            manifest.get('service') != SERVICE or len(pictures) != 1 or
            not pictures <= {'wallpaper.jpg', 'wallpaper.png', 'wallpaper.webp'} or
            set(files) != set(CSS_NAMES) | pictures or
            {p.name for p in bundle.iterdir()} != set(files) | {'manifest.json'}):
        raise ValueError('Unexpected bundle owner, service or file list.')
    # Read once: deployment uses these bytes, not mutable source paths.
    payload = {name: (bundle / name).read_bytes() for name in files}
    if any(digest(value) != files[name] for name, value in payload.items()):
        raise ValueError('Bundle hashes do not match.')
    picture, = pictures
    if len(payload[picture]) > MAX_IMAGE or picture != 'wallpaper.' + image_extension(payload[picture]):
        raise ValueError('Invalid wallpaper payload.')
    return manifest, payload


def check_owned(deployment, dropin):
    no_symlinks(deployment)
    no_symlinks(dropin)
    if deployment.exists():
        if not deployment.is_dir():
            raise ValueError('Deployment target is not a directory.')
        read_bundle(deployment)
    if dropin.exists() and (not dropin.is_file() or not dropin.read_text().startswith(HEADER)):
        raise ValueError('An unrelated configuration owns the drop-in target.')


def write_atomic(path, data, mode=0o644):
    no_symlinks(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.nothingos-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), mode)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def public_parents(path):
    """New service/theme parents must be readable by the unprivileged greeter."""
    no_symlinks(path)
    missing = []
    current = path
    while not current.exists():
        missing.append(current)
        current = current.parent
    for directory in reversed(missing):
        directory.mkdir(mode=0o755)
        os.chmod(directory, 0o755)


def replace_dropin(path):
    write_atomic(path, DROPIN_TEXT.encode())


def snapshot(root, deployment, dropin):
    backups = rooted(root, BACKUPS)
    no_symlinks(backups)
    backups.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%dT%H%M%S-'), dir=backups))
    state = {'owner': OWNER, 'deployment': deployment.exists(), 'dropin': dropin.exists()}
    if deployment.exists():
        shutil.copytree(deployment, backup / 'deployment')
    if dropin.exists():
        shutil.copy2(dropin, backup / 'dropin.conf')
    state['hashes'] = {str(p.relative_to(backup)): digest(p.read_bytes())
                       for p in backup.rglob('*') if p.is_file()}
    (backup / 'state.json').write_text(json.dumps(state, indent=2))
    os.chmod(backup / 'state.json', 0o600)
    return backup


def restore(backup, *, root=Path('/')):
    backup = Path(backup).absolute()
    no_symlinks(backup)
    if backup.parent != rooted(root, BACKUPS):
        raise ValueError('Restore requires a backup from the managed backup directory.')
    state = json.loads((backup / 'state.json').read_text())
    if state.get('owner') != OWNER:
        raise ValueError('Unknown backup owner.')
    if state.get('deployment'):
        read_bundle(backup / 'deployment')
    files = [p for p in backup.rglob('*') if p.is_file() and p.name != 'state.json']
    if any(p.is_symlink() for p in backup.rglob('*')):
        raise ValueError('Symlink in backup.')
    actual = {str(p.relative_to(backup)): digest(p.read_bytes()) for p in files}
    if actual != state.get('hashes'):
        raise ValueError('Backup content hashes changed.')
    deployment, dropin = rooted(root, DEPLOY), rooted(root, DROPIN)
    check_owned(deployment, dropin)
    if state['dropin']:
        previous = backup / 'dropin.conf'
        if not previous.read_text().startswith(HEADER):
            raise ValueError('Unexpected backed-up drop-in.')
    staging = None
    if state['deployment']:
        public_parents(deployment.parent)
        staging = Path(tempfile.mkdtemp(prefix='.nothingos-restore-', dir=deployment.parent))
        shutil.copytree(backup / 'deployment', staging, dirs_exist_ok=True)
        shutil.copystat(backup / 'deployment', staging)
    if deployment.exists():
        shutil.rmtree(deployment)
    if staging:
        os.replace(staging, deployment)
    if state['dropin']:
        public_parents(dropin.parent)
        write_atomic(dropin, previous.read_bytes(), stat.S_IMODE(previous.stat().st_mode))
    else:
        dropin.unlink(missing_ok=True)


def install(bundle, *, root=Path('/')):
    manifest, payload = read_bundle(Path(bundle).absolute())
    version = check_host(root)
    check_font()
    if (manifest['shell_version'] != version or
            manifest['resource_sha256'] != digest(rooted(root, RESOURCE).read_bytes())):
        raise ValueError('Prepared bundle is stale; prepare against the installed GNOME version.')
    deployment, dropin = rooted(root, DEPLOY), rooted(root, DROPIN)
    check_owned(deployment, dropin)
    public_parents(deployment.parent)
    public_parents(dropin.parent)
    backup = snapshot(root, deployment, dropin)
    staging = Path(tempfile.mkdtemp(prefix='.nothingos-stage-', dir=deployment.parent))
    old = deployment.parent / (staging.name + '-previous')
    transaction_finished = False
    try:
        for name, data in payload.items():
            (staging / name).write_bytes(data)
            os.chmod(staging / name, 0o644)
        (staging / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
        os.chmod(staging / 'manifest.json', 0o644)
        os.chmod(staging, 0o755)
        if deployment.exists():
            os.replace(deployment, old)
        os.replace(staging, deployment)
        replace_dropin(dropin)
        transaction_finished = True
    except Exception:
        try:
            restore(backup, root=root)
            transaction_finished = True
        except Exception as rollback_error:
            raise RuntimeError(f'Rollback could not finish. Preserve backup {backup} and previous tree {old}.') from rollback_error
        raise
    finally:
        if staging.exists():
            shutil.rmtree(staging)
        if transaction_finished and old.exists():
            shutil.rmtree(old)
    return backup
