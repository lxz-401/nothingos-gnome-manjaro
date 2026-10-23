# NothingOS for Neovim

A local, dependency-free colorscheme matching the desktop and Alacritty palette:
`#111111` editor, charcoal panels, white text and `#45ffbc` mint accents.
Syntax and diagnostic colors remain distinct. Includes highlights for Tree-sitter,
LSP, Telescope, nvim-tree, bufferline, dashboard and nvim-notify, plus a lualine theme.
No plugins are installed, updated or removed.

## Install into an existing configuration

From the repository root, back up the **resolved** configuration directory first
(the configuration may be a symlink to private dotfiles). Keep the backup outside
the configuration directory. Then copy only the theme runtime files:

```sh
mkdir -p ~/.config/nvim/colors ~/.config/nvim/lua/nothingos ~/.config/nvim/lua/lualine/themes
cp neovim/colors/nothingos.lua ~/.config/nvim/colors/
cp neovim/lua/nothingos/theme.lua ~/.config/nvim/lua/nothingos/
cp neovim/lua/lualine/themes/nothingos.lua ~/.config/nvim/lua/lualine/themes/
```

Activate with `:colorscheme nothingos`, or add `vim.cmd.colorscheme("nothingos")`
after the existing theme setup in `init.lua`. Existing themes remain available.
Lualine's `theme = 'auto'` automatically uses the included theme.

## NitroVim integration

`nitrovim.patch` adapts the NitroVim configuration inspected for this task:

- Adds NothingOS to `:ThemeSwitch`, which saves the selected theme in `theme.json`.
- Keeps nvim-tree's old hardcoded colors from overwriting NothingOS at startup.
- Moves unconditional transparency clearing into the transparency callback so
  opaque panels retain their backgrounds. The transparency toggle still works.
- Sets `showtabline = 2` (always show the buffer bar).

After copying the runtime files, check compatibility before applying the patch.
Run these commands from the existing NitroVim configuration directory, replacing
`/absolute/path/to/repo` with your checkout:

```sh
patch --dry-run -p1 < /absolute/path/to/repo/neovim/nitrovim.patch
patch -p1 < /absolute/path/to/repo/neovim/nitrovim.patch
```

Do not reapply if already integrated. Restart Neovim and select
`nothingos (dark)` in `:ThemeSwitch`. Other configurations need only the runtime
files, not this NitroVim-specific patch.

`:TransparentDisable` restores solid editor/panel backgrounds;
`:TransparentEnable` reveals the terminal background. NitroVim's existing
transparency preference is preserved. Alacritty opacity and the terminal font
are controlled by Alacritty, not by a Neovim colorscheme.

## Customize and restore

Edit `lua/nothingos/theme.lua` to change the palette; reload with
`:colorscheme nothingos`. The statusline theme uses the same palette.

To revert only the design, select the previous theme with `:ThemeSwitch`
(the inspected configuration used `onedark (darker)`). For a full rollback,
close Neovim and restore the files changed by `nitrovim.patch` plus `theme.json`
from your backup; remove the three newly added runtime files if desired.
Preserve the configuration symlink and any later unrelated edits.

## Verification

Verified on Neovim 0.12.6 with the installed NitroVim plugins: startup,
NothingOS selection, opaque and transparent backgrounds, mint active buffer
and statusline, opening nvim-tree and Telescope, and switching to OneDark and
back. No extra background process, timer or plugin is added by this theme.

The installed nvim-tree version leaves a suppressed `E216: No such group or
event: FileExplorer *` in `v:errmsg` while removing netrw autocommands. The
backed-up OneDark configuration reproduces it too; theme reload itself leaves
`v:errmsg` empty. This pre-existing plugin behavior does not block the explorer.
