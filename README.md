# Fidel LKPR Updater — Windows build

This package contains the updater source and all bundled image assets.

## Build
On Windows, run `build_windows.bat`.

The PyInstaller build includes the complete `assets` folder:
- `lkpr_header.png`
- `flag_uk.png`
- `flag_cz.png`

This is important: the executable must contain all three images, not just the header.
The app opens maximized and has English/Czech flag buttons.

The installer is produced with Inno Setup 6 when installed.
