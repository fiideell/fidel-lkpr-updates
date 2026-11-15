# Fidel LKPR Updater 2.0

Modern dark aviation-themed updater for `zzz_fidel-lkpr-live-tailstrike-edition`.

## What's new
- Uses your supplied LKPR night screenshot as the wide header image.
- English / Czech language switch (saved between launches).
- Updated dashboard layout with version cards, release notes, Community folder and clear status.
- Existing GitHub Releases update flow, ZIP validation, manifest version check and timestamped backup are retained.

## Build on Windows
Requirements: Windows 10/11, Python 3.11+, Inno Setup 6 (for the installer).

Run `build_windows.bat`. It creates:
- `dist\FidelLKPRUpdater.exe`
- `installer\Fidel_LKPR_Updater_Setup.exe` (if Inno Setup 6 is installed)

The header image is bundled into the executable; end users do not need a separate image file.

## Release requirements
The latest GitHub Release must include the exact asset name:
`zzz_fidel-lkpr-live-tailstrike-edition.zip`

The ZIP must contain one root folder named `zzz_fidel-lkpr-live-tailstrike-edition` and its `manifest.json` package_version must match the release tag.
