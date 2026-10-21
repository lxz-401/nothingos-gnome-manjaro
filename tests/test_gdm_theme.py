import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('gdm_theme', ROOT / 'gdm-theme/theme.py')
theme = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(theme)


class PreparationTests(unittest.TestCase):
    def test_selects_dark_or_light_wallpaper(self):
        with tempfile.TemporaryDirectory() as temporary:
            light, dark = Path(temporary) / 'light.png', Path(temporary) / 'dark.png'
            light.touch()
            dark.touch()
            settings = {'color-scheme': 'prefer-dark', 'picture-uri': light.as_uri(),
                        'picture-uri-dark': dark.as_uri()}
            self.assertEqual(theme.select_wallpaper(settings, None), dark)
            settings['color-scheme'] = 'default'
            self.assertEqual(theme.select_wallpaper(settings, None), light)

    def test_explicit_wallpaper_with_spaces_and_unicode(self):
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / 'mening fonim — oq.png'
            image.touch()
            self.assertEqual(theme.select_wallpaper({}, image), image)
            self.assertEqual(theme.select_wallpaper({'picture-uri': image.as_uri()}, None), image)

    def test_missing_or_nonlocal_wallpaper_rejected(self):
        for value in ['https://example.com/a.jpg', 'file://remote/a.jpg', 'file:///missing.png']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                theme.select_wallpaper({'picture-uri': value}, None)

    def test_home_only_or_missing_jetbrains_font_rejected(self):
        for output in ['JetBrains Mono\n/home/person/.local/share/fonts/mono.ttf\n',
                       'DejaVu Sans\n/usr/share/fonts/TTF/DejaVuSans.ttf\n']:
            with self.subTest(output=output), patch.object(theme, 'run', return_value=output), \
                 self.assertRaises(ValueError):
                theme.check_font()

    def test_prepare_preserves_native_css_and_high_contrast(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            resource = base / 'native.gresource'
            resource.write_bytes(b'original resource')
            image = base / 'wallpaper.png'
            image.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
            native = {name: '/* original ' + name + ' */' for name in theme.CSS_NAMES}
            with patch.object(theme, 'RESOURCE', resource), \
                 patch.object(theme, 'check_host', return_value='51.1'), \
                 patch.object(theme, 'check_font'), \
                 patch.object(theme, 'image_info', return_value={'format': 'png', 'width': 10, 'height': 10}), \
                 patch.object(theme, 'native_styles', return_value=native), \
                 patch.object(theme, 'validate_css') as validate:
                bundle = theme.prepare(base / 'bundle', image, blur=0)
            names = {p.name for p in bundle.iterdir()}
            self.assertEqual(names, {*theme.CSS_NAMES, 'wallpaper.png', 'manifest.json'})
            for name in theme.CSS_NAMES:
                css = (bundle / name).read_text()
                self.assertTrue(css.startswith(native[name]))
                self.assertIn('JetBrains Mono', css)
                self.assertIn('/usr/local/share/nothingos-gdm/wallpaper.png', css)
                self.assertNotIn('@WALLPAPER@', css)
            validate.assert_called_once()
            self.assertEqual(resource.read_bytes(), b'original resource')
            self.assertNotIn('gnome-shell-high-contrast.css', names)

    def test_blur_svg_embeds_source_and_scales_effect_to_screen_height(self):
        import base64
        source = b'\xff\xd8\xfffixture'
        svg = theme.blur_svg(source, {'width': 3840, 'height': 2160}, 32)
        self.assertIn('width="1920" height="1080"', svg)
        self.assertIn('stdDeviation="64.000000"', svg)
        self.assertIn('edgeMode="duplicate"', svg)
        self.assertIn('data:image/jpeg;base64,' + base64.b64encode(source).decode(), svg)
        self.assertNotIn('file://', svg)

    def test_invalid_blur_rejected_and_zero_keeps_exact_image_bytes(self):
        for radius in [-1, 129, float('nan'), float('inf')]:
            with self.subTest(radius=radius), self.assertRaises(ValueError):
                theme.blur_wallpaper(b'original', {'width': 1, 'height': 1}, radius)
        with patch.object(theme.subprocess, 'run') as renderer:
            self.assertEqual(theme.blur_wallpaper(b'original', {}, 0), b'original')
            renderer.assert_not_called()

    def test_default_blur_changes_only_private_derivative_and_records_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            resource = base / 'native.gresource'
            resource.write_bytes(b'native')
            image = base / 'original.jpg'
            original = b'\xff\xd8\xfffixture'
            image.write_bytes(original)
            png = b'\x89PNG\r\n\x1a\nblurred'
            with patch.object(theme, 'RESOURCE', resource), \
                 patch.object(theme, 'check_host', return_value='51.1'), \
                 patch.object(theme, 'check_font'), \
                 patch.object(theme, 'image_info', return_value={'width': 3840, 'height': 2160}), \
                 patch.object(theme, 'native_styles', return_value=dict.fromkeys(theme.CSS_NAMES, '/* native */')), \
                 patch.object(theme, 'validate_css'), \
                 patch.object(theme, 'blur_wallpaper', return_value=png) as render:
                bundle = theme.prepare(base / 'bundle', image)
            render.assert_called_once_with(original, {'width': 3840, 'height': 2160}, 32)
            self.assertEqual(image.read_bytes(), original)
            self.assertEqual((bundle / 'wallpaper.png').read_bytes(), png)
            self.assertEqual(json.loads((bundle / 'manifest.json').read_text())['wallpaper_effect']['blur_px'], 32)
            theme.read_bundle(bundle)


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'root'
        self.root.mkdir()
        self.bundle = self.base / 'bundle'
        self.bundle.mkdir()
        self.resource = self.root / theme.RESOURCE.relative_to('/')
        self.resource.parent.mkdir(parents=True)
        self.resource.write_bytes(b'native')
        self.unit = self.root / theme.UNIT.relative_to('/')
        self.unit.parent.mkdir(parents=True)
        self.unit.write_text('[Service]\nExecStart=/usr/bin/gnome-shell --mode=%i\n')
        session = self.root / theme.SESSION.relative_to('/')
        session.parent.mkdir(parents=True)
        session.write_text('[Unit]\nRequires=' + theme.SERVICE + '\n')
        payload = {**{name: b'/* validated fixture */' for name in theme.CSS_NAMES},
                   'wallpaper.png': b'\x89PNG\r\n\x1a\nfixture'}
        for name, content in payload.items():
            (self.bundle / name).write_bytes(content)
        manifest = {'format': 1, 'owner': theme.OWNER, 'shell_version': '51.1',
                    'resource_sha256': theme.digest(self.resource.read_bytes()),
                    'service': theme.SERVICE, 'files': {k: theme.digest(v) for k, v in payload.items()}}
        (self.bundle / 'manifest.json').write_text(json.dumps(manifest))
        self.addCleanup(patch.stopall)
        patch.object(theme, 'check_font').start()
        patch.object(theme, 'shell_version', return_value='51.1').start()

    @property
    def deployment(self):
        return self.root / theme.DEPLOY.relative_to('/')

    @property
    def dropin(self):
        return self.root / theme.DROPIN.relative_to('/')

    def test_install_targets_only_gdm_instance(self):
        theme.install(self.bundle, root=self.root)
        self.assertIn('G_RESOURCE_OVERLAYS=/org/gnome/shell/theme=/usr/local/share/nothingos-gdm',
                      self.dropin.read_text())
        self.assertIn('org.gnome.Shell@gdm.service.d', str(self.dropin))
        self.assertFalse((self.root / 'etc/systemd/system/gdm.service.d').exists())
        self.assertFalse((self.root / 'etc/systemd/user/org.gnome.Shell@user.service.d').exists())
        self.assertEqual(self.resource.read_bytes(), b'native')
        self.assertEqual(self.deployment.stat().st_mode & 0o777, 0o755)

    def test_greeter_paths_remain_readable_under_private_root_umask(self):
        previous = os.umask(0o077)
        try:
            theme.install(self.bundle, root=self.root)
        finally:
            os.umask(previous)
        self.assertEqual(self.dropin.parent.stat().st_mode & 0o777, 0o755)
        self.assertEqual(self.dropin.stat().st_mode & 0o777, 0o644)
        self.assertEqual((self.deployment / 'wallpaper.png').stat().st_mode & 0o777, 0o644)

    def test_conflicting_or_symlink_destinations_rejected(self):
        self.deployment.parent.mkdir(parents=True)
        self.deployment.mkdir()
        (self.deployment / 'unrelated').touch()
        with self.assertRaises(ValueError):
            theme.install(self.bundle, root=self.root)
        (self.deployment / 'unrelated').unlink()
        self.deployment.rmdir()
        target = self.base / 'foreign'
        target.mkdir()
        self.deployment.symlink_to(target)
        with self.assertRaises(ValueError):
            theme.install(self.bundle, root=self.root)
        self.assertEqual(list(target.iterdir()), [])

    def test_changed_resource_or_payload_rejected_before_write(self):
        self.resource.write_bytes(b'updated by GNOME')
        with self.assertRaises(ValueError):
            theme.install(self.bundle, root=self.root)
        self.resource.write_bytes(b'native')
        (self.bundle / 'gnome-shell-dark.css').write_text('changed')
        with self.assertRaises(ValueError):
            theme.install(self.bundle, root=self.root)
        self.assertFalse(self.deployment.exists())
        self.assertFalse(self.dropin.exists())

    def test_install_failure_restores_both_destinations(self):
        first = theme.install(self.bundle, root=self.root)
        original = {p.name: p.read_bytes() for p in self.deployment.iterdir()}
        old_dropin = self.dropin.read_bytes()
        with patch.object(theme, 'replace_dropin', side_effect=OSError('simulated write failure')):
            with self.assertRaises(OSError):
                theme.install(self.bundle, root=self.root)
        self.assertEqual({p.name: p.read_bytes() for p in self.deployment.iterdir()}, original)
        self.assertEqual(self.dropin.read_bytes(), old_dropin)
        self.assertTrue(first.exists())

    def test_restore_preserves_unrelated_dropins_and_original_absence(self):
        self.dropin.parent.mkdir(parents=True)
        other = self.dropin.parent / '10-other.conf'
        other.write_text('[Service]\nEnvironment=EXAMPLE=1\n')
        backup = theme.install(self.bundle, root=self.root)
        second = theme.install(self.bundle, root=self.root)
        theme.restore(second, root=self.root)
        self.assertTrue(self.deployment.exists())
        theme.restore(backup, root=self.root)
        self.assertFalse(self.deployment.exists())
        self.assertFalse(self.dropin.exists())
        self.assertTrue(other.exists())

    def test_failed_rollback_retains_original_tree_for_recovery(self):
        theme.install(self.bundle, root=self.root)
        original = (self.deployment / 'manifest.json').read_bytes()
        with patch.object(theme, 'replace_dropin', side_effect=OSError('write failed')), \
             patch.object(theme, 'restore', side_effect=OSError('disk unavailable')):
            with self.assertRaisesRegex(RuntimeError, 'Preserve backup'):
                theme.install(self.bundle, root=self.root)
        previous, = self.deployment.parent.glob('.nothingos-stage-*-previous')
        self.assertEqual((previous / 'manifest.json').read_bytes(), original)


if __name__ == '__main__':
    unittest.main()
