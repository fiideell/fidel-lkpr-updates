# FIDEL LKPR Live - updater

## v9 startup/layout fixes
- Starts maximized after the native Windows window is created, so the complete dashboard and footer are visible on first launch.
- Falls back to a screen-fitting window if maximize is unavailable.
- Header image is now a background child of a dedicated frame; title, airport label and language buttons are separate sibling widgets layered above it. This prevents the branding from disappearing after language changes.
- Reduced vertical spacing slightly to fit more comfortably on smaller displays.
- Keeps the runway 24 icon, flag assets, original LKPR photo, GitHub update/install and backup logic.

## Build
Run `build_windows.bat` on Windows. It cleans old `build` and `dist` directories and embeds all assets and the custom icon.
