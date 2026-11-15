# Fidel LKPR Updater

Windows updater for the MSFS scenery package:

`zzz_fidel-lkpr-live-tailstrike-edition`

GitHub repository: https://github.com/fiideell/fidel-lkpr-updates

## How updates are published

The updater reads the latest **published GitHub Release** from this repository.

For every scenery update:

1. Create a GitHub Release with a tag such as `v3.0.1` or `v3.0.2`.
2. Attach the scenery ZIP as a release asset. The asset filename must be exactly:
   `zzz_fidel-lkpr-live-tailstrike-edition.zip`
3. Put user-facing change notes in the Release description.
4. Publish the Release (not draft).

The scenery ZIP must contain one top-level folder named
`zzz_fidel-lkpr-live-tailstrike-edition`, with `manifest.json` inside it.
The `package_version` in that manifest must match the release tag.

## Build on Windows

Requirements:
- Windows 10 or 11
- Python 3.11+ (check “Add Python to PATH” during installation)
- Inno Setup 6 (only if you want to build the Setup installer)

Run `build_windows.bat`. It creates:
- `dist\FidelLKPRUpdater.exe` — portable standalone updater
- `installer\Fidel_LKPR_Updater_Setup.exe` — installer, if Inno Setup 6 is installed

The app uses Python's built-in Tkinter and standard library; no runtime Python install is needed by users.

## Safety behaviour

- The app only replaces the exact scenery folder named above.
- It validates the ZIP structure and checks the scenery manifest version before replacing anything.
- It creates a timestamped backup of the previous scenery folder.
- If the final folder rename fails, it attempts to restore the backup.
- Close Microsoft Flight Simulator before installing an update.
- The first run may require the user to select the MSFS Community folder manually.

## Important

The first public GitHub Release still needs to be created manually and the scenery ZIP attached.
Do not publish a Release until the attached ZIP and manifest version have been checked.
