# FIDEL LKPR Live - updater

## v10
- Opens as a normal, non-maximized window at 1018 × 820 client pixels (approximately 1018 × 850 including the Windows title bar), matching the supplied reference size.
- Window is intentionally fixed-size so the entire dashboard remains visible without manual resizing.
- Uses a refreshed multi-resolution runway 24 ICO for the EXE, app window, installer and shortcuts.
- EXE renamed to `FidelLKPRLiveUpdater.exe` to avoid Windows reusing the previous generic-icon executable/shortcut cache.
- Language switching and header overlay layout from v9 retained.

## Build
Run `build_windows.bat` on Windows. It removes old build outputs and embeds the complete assets folder and `assets\app_icon.ico`.
