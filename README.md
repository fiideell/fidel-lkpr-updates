# Fidel LKPR Updater — refreshed header build

## Changes
- Opens maximized on launch so the bottom controls are visible immediately.
- Uses the newly supplied compact LKPR runway header image.
- Header branding: FIDEL LKPR Live / TAILSTRIKE EDITION / SCENERY UPDATER for Microsoft Flight Simulator 2024.
- Uses bundled UK and Czech flag PNGs on the language buttons (not emoji), so flags render consistently on Windows.
- Keeps the GitHub release check, download, archive validation, manifest version check and backup installation flow.

## Build
On Windows with Python and Inno Setup 6 installed, run `build_windows.bat`.
The EXE bundles `assets/lkpr_header.png`, `assets/flag_uk.png`, and `assets/flag_cz.png`.
