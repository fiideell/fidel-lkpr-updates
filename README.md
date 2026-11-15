# FIDEL LKPR Live - updater

## v16 Community cleanup
- The updater downloads, validates and extracts the new scenery before touching the installed version.
- During replacement, the old scenery folder is moved temporarily out of the way.
- After the new scenery folder is installed successfully, the old version is permanently deleted.
- The Community folder is left with only `zzz_fidel-lkpr-live-tailstrike-edition` (no timestamped backup folders).
- If replacing the folder fails, the updater attempts to restore the previous version.
- If deleting the old version fails, it attempts to roll back to the original version and reports the error.

## Build
Run `build_windows.bat` on Windows and install the newly generated Setup EXE.
