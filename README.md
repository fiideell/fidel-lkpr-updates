# FIDEL LKPR Live - updater

## v8 fixes
- Keeps the FIDEL LKPR Live / TAILSTRIKE EDITION / simulator subtitle visible after switching language.
- Explicitly raises the header text and language controls above the banner image after redraw.
- Applies the runway 24 icon to the Tk window and embeds it in the Windows EXE and installer.
- Bundles the complete assets folder.

## Important clean rebuild
Close the updater. Run `build_windows.bat`; it deletes old `build` and `dist` folders before rebuilding.
Install the newly generated `installer\Fidel_LKPR_Updater_Setup.exe` to replace the previous build.
