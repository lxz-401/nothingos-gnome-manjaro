# ✨ NothingOS GNOME – A Minimalist Manjaro Desktop Experience

This is a **NothingOS-inspired desktop build** for **Manjaro Linux (GNOME edition)**. It's designed to bring the clean, monochrome aesthetic of Nothing's design philosophy to the Linux desktop — with polished widgets, blurred transparency, and a cohesive theme setup.

---

## 📷 Screenshots

![Image](https://github.com/user-attachments/assets/e5b12125-3ab4-4e47-b541-66a3e3929132)

---

## 🚀 Features

- ⚙️ **GNOME Shell Theme** — Clean, flat, and monochrome with subtle animations  
- 🎨 **GTK Theme** — Matches the Shell theme for a unified look  
- 🖥 **Alacritty Config** — Transparency, blur, and font matching NothingOS style  
- 🧱 **Eww Widgets** — Interactive status bar with time, date, weather, system stats, music, and editable reminders
- 📈 **Conky Setup** — Optional low-resource alternative to Eww    
- 🖼 **Wallpapers** — Custom and curated Nothing-style backgrounds  

---
## 🧰 Dependencies Installation

This setup uses **Conky** (for system widgets) and **Eww** (ElKowars Wacky Widgets). Make sure both are installed before proceeding.

### 📦 Install on Different Distros

#### 🔹 Arch Linux / Manjaro
```bash
sudo pacman -S conky eww
```
#### 🔹 Debian / Ubuntu
```bash
sudo apt install conky-all
sudo apt install libgtk-3-dev libglib2.0-dev libpango1.0-dev libgdk-pixbuf2.0-dev libjson-glib-dev rustc cargo git

# Clone and build Eww
git clone https://github.com/elkowar/eww.git
cd eww
cargo build --release
sudo cp target/release/eww /usr/local/bin/
```
#### Fedora
```bash
sudo dnf install conky

# Eww dependencies
sudo dnf install gtk3-devel glib2-devel pango-devel gdk-pixbuf2-devel json-glib-devel rust cargo git

# Clone and build Eww
git clone https://github.com/elkowar/eww.git
cd eww
cargo build --release
sudo cp target/release/eww /usr/local/bin/
```
#### NixOS
```nix
environment.systemPackages = with pkgs; [
  conky
  eww
];
```
---

## 🛠 Installation

> ⚠️ **Use at your own risk.** This is a personal config and may require adjustments based on your system.

### 1. Clone the Repo

```bash
git clone https://github.com/lxz-401/nothingos-gnome-manjaro
cd nothingos-gnome-manjaro
```
### 2. Install WhiteSur icons automatically

From your GNOME desktop session, run:

```bash
./install.sh
```

This downloads the pinned official [WhiteSur icon theme](https://github.com/vinceliuice/WhiteSur-icon-theme),
installs `WhiteSur`, `WhiteSur-light`, and `WhiteSur-dark` for your user, and selects
**WhiteSur** in GNOME. Run it without `sudo`. Required commands: `git`,
`gtk-update-icon-cache`, and `gsettings` with the GNOME desktop schemas.
On Arch/Manjaro/CachyOS, install these prerequisites with:

```bash
sudo pacman -S --needed git gtk-update-icon-cache glib2 gsettings-desktop-schemas
```

Existing WhiteSur files and the previous icon selection are backed up under
`~/.local/state/nothingos/backups/` (or `$XDG_STATE_HOME`). A failed install
restores the old files and icon selection. XDG data paths and paths with spaces
are supported. Internet access is required for the download.

For provisioning without a running GNOME session:

```bash
./install.sh --no-apply
```

Then select `WhiteSur` in GNOME Tweaks after login. The installer handles the
icon component; continue with the modular desktop configuration below.

Installer safety tests: `python3 tests/test_icon_install.py`.

### 3. Copy the configs

Configs are modular. Copy only what you want:

```bash
mkdir -p ~/.config
cp -r alacritty ~/.config/
cp -r eww ~/.config/
cp -r conky ~/.config/
```
> Replace `~` with your actual home path if needed.

See [INSTALL-CACHYOS.md](INSTALL-CACHYOS.md) for the GTK/Shell directory layout,
GNOME 51 compatibility extension, and Conky service setup. Back up existing
application configs before copying them.

For the matching lockscreen clock, password field and notification styling, see
[Shell theme lockscreen setup](shell-theme/README.md#session-lockscreen).
The setup backs up current files; log out and back in once after applying it.

For GDM before login, [GDM theme setup](gdm-theme/README.md) uses your current
wallpaper and system-wide JetBrains Mono, with administrator authentication,
separate backups and no automatic logout or GDM restart.
---
### 4. Open widgets and Conky
```bash
~/.config/conky/start_conky.sh  # clock + four independently positioned blocks
# for EWW widgets
eww open name-of-widget
# example eww open day-of-month
# example conky -c ~/.conky/nothing-phone/nothing-phone-simple.conf
```
---
### 5. Apply Themes

Use **GNOME Tweaks** to apply:

- GTK Theme: `NothingOS-GTK`  
- Shell Theme: `NothingOS-Shell`  
- Icons: `WhiteSur` (selected automatically by `./install.sh`)
- Font: `Inter`, `Product Sans`, or `Roboto`  

---

## 🌦 API Keys

If you're using the weather widget (Eww or Conky), replace the placeholder in:

`eww/scripts/get-weather.sh`

With your own API key:

API_KEY="YOUR_API_KEY_HERE"


You can get a free key from:
- https://weatherapi.com  
- https://openweathermap.org  

---

## 🙋 FAQ

**Q: Will this work on other distros?**  
A: Yes, with tweaks. It's built for Manjaro GNOME but works on most GNOME-based setups.

**Q: What if Eww doesn't show up properly?**  
A: Make sure you're using X11 (not Wayland) and have `eww` installed from source or your package manager.

**Q: Can I fork or contribute?**  
A: Absolutely! Feel free to fork, open issues, or submit pull requests.

---

## ❤️ Credits

- Inspired by the **NothingOS** design language  
- Built with:  
  - [Eww](https://github.com/elkowar/eww)  
  - [Alacritty](https://github.com/alacritty/alacritty)  
  - [Conky](https://github.com/brndnmtthws/conky)  
  - [Papirus Icons](https://github.com/PapirusDevelopmentTeam)  
  - [WhiteSur Icons](https://github.com/vinceliuice/WhiteSur-icon-theme)

---

## 📢 License

This project is released under the [GPL3 License](LICENSE), unless otherwise noted.
