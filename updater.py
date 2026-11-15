from __future__ import annotations

import json
import os
import queue
import re
import shutil
import threading
import time
import urllib.request
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

OWNER = "fiideell"
REPO = "fidel-lkpr-updates"
ADDON_FOLDER = "zzz_fidel-lkpr-live-tailstrike-edition"
ASSET_NAME = ADDON_FOLDER + ".zip"
APP_NAME = "Fidel LKPR Updater"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
USER_AGENT = "Fidel-LKPR-Updater/1.0"
APP_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FidelLKPRUpdater"
SETTINGS_FILE = APP_DATA / "settings.json"


def version_tuple(value: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", value or "")
    return tuple(int(x) for x in nums) if nums else (0,)


def read_local_version(community: Path) -> str | None:
    manifest = community / ADDON_FOLDER / "manifest.json"
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
        return str(data.get("package_version") or "")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None


def candidate_community_paths() -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    roaming = Path(os.environ.get("APPDATA", Path.home()))
    candidates = [
        local / "Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/Community",
        roaming / "Microsoft Flight Simulator 2024/Packages/Community",
        local / "Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Community",
        roaming / "Microsoft Flight Simulator/Packages/Community",
    ]

    # MSFS can use a custom package directory recorded in UserCfg.opt.
    cfg_candidates = [
        local / "Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/UserCfg.opt",
        local / "Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/UserCfg.opt",
        roaming / "Microsoft Flight Simulator 2024/UserCfg.opt",
        roaming / "Microsoft Flight Simulator/UserCfg.opt",
    ]
    for cfg in cfg_candidates:
        try:
            content = cfg.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r'InstalledPackagesPath\s+"([^"]+)"', content)
            if match:
                candidates.insert(0, Path(match.group(1)) / "Community")
        except OSError:
            pass

    result = []
    seen = set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen and path.is_dir():
            seen.add(key)
            result.append(path)
    return result


def request_json(url: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


class UpdaterApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("700x520")
        self.root.minsize(640, 480)
        self.root.configure(bg="#101827")
        self.events: queue.Queue = queue.Queue()
        self.release: dict | None = None
        self.asset: dict | None = None
        self.community = tk.StringVar()
        self.local_version = tk.StringVar(value="Nenainstalováno / nezjištěno")
        self.remote_version = tk.StringVar(value="Kontroluji…")
        self.status = tk.StringVar(value="Připojuji se ke GitHubu…")
        self.release_notes = tk.StringVar(value="Načítám informace o vydání…")
        self.install_button = None
        self.progress = None

        self._load_settings()
        self._build_ui()
        self._refresh_local_version()
        self.root.after(150, self._poll_events)
        self.check_updates()

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Horizontal.TProgressbar",
            troughcolor="#263449",
            background="#42b4e8",
            bordercolor="#263449",
            lightcolor="#42b4e8",
            darkcolor="#42b4e8",
        )

        outer = tk.Frame(self.root, bg="#101827", padx=26, pady=22)
        outer.pack(fill="both", expand=True)

        header = tk.Frame(outer, bg="#101827")
        header.pack(fill="x")
        mark = tk.Label(
            header, text="✈", font=("Segoe UI Symbol", 30),
            fg="#57c5f2", bg="#101827"
        )
        mark.pack(side="left", padx=(0, 13))
        title_box = tk.Frame(header, bg="#101827")
        title_box.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_box, text="FIDEL LKPR", font=("Segoe UI", 20, "bold"),
            fg="#f3f7fb", bg="#101827"
        ).pack(anchor="w")
        tk.Label(
            title_box, text="SCENERY UPDATER  •  MICROSOFT FLIGHT SIMULATOR",
            font=("Segoe UI", 8, "bold"), fg="#8da4bd", bg="#101827"
        ).pack(anchor="w", pady=(2, 0))

        tk.Frame(outer, bg="#2a3b51", height=1).pack(fill="x", pady=20)

        card = tk.Frame(outer, bg="#19263a", padx=18, pady=16)
        card.pack(fill="x")
        tk.Label(card, text="STAV INSTALACE", font=("Segoe UI", 9, "bold"),
                 fg="#8da4bd", bg="#19263a").pack(anchor="w")
        self._info_row(card, "Nainstalovaná verze", self.local_version)
        self._info_row(card, "Dostupná verze", self.remote_version)

        tk.Label(outer, textvariable=self.status, font=("Segoe UI", 11, "bold"),
                 fg="#57c5f2", bg="#101827", anchor="w").pack(fill="x", pady=(18, 7))

        notes_frame = tk.Frame(outer, bg="#19263a", padx=16, pady=12)
        notes_frame.pack(fill="both", expand=True)
        tk.Label(notes_frame, text="POZNÁMKY K VYDÁNÍ", font=("Segoe UI", 8, "bold"),
                 fg="#8da4bd", bg="#19263a").pack(anchor="w")
        self.notes_text = tk.Text(
            notes_frame, height=5, wrap="word", relief="flat",
            bg="#19263a", fg="#d8e3ef", insertbackground="#d8e3ef",
            font=("Segoe UI", 9), padx=0, pady=8
        )
        self.notes_text.pack(fill="both", expand=True)
        self.notes_text.insert("1.0", "Načítám informace o vydání…")
        self.notes_text.configure(state="disabled")

        path_frame = tk.Frame(outer, bg="#101827")
        path_frame.pack(fill="x", pady=(16, 0))
        tk.Label(path_frame, text="Community složka", font=("Segoe UI", 9, "bold"),
                 fg="#8da4bd", bg="#101827").pack(anchor="w", pady=(0, 6))
        path_row = tk.Frame(path_frame, bg="#101827")
        path_row.pack(fill="x")
        self.path_entry = tk.Entry(
            path_row, textvariable=self.community, relief="flat",
            bg="#19263a", fg="#e6eef7", insertbackground="#ffffff",
            font=("Segoe UI", 9)
        )
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(
            path_row, text="Vybrat…", command=self.browse_community,
            bg="#2a3b51", fg="#ffffff", activebackground="#3b526f",
            activeforeground="#ffffff", relief="flat", padx=14, pady=7,
            cursor="hand2"
        ).pack(side="left", padx=(8, 0))

        self.progress = ttk.Progressbar(outer, mode="indeterminate")
        self.progress.pack(fill="x", pady=(16, 0))

        buttons = tk.Frame(outer, bg="#101827")
        buttons.pack(fill="x", pady=(14, 0))
        tk.Button(
            buttons, text="Zkontrolovat aktualizace", command=self.check_updates,
            bg="#2a3b51", fg="#ffffff", activebackground="#3b526f",
            activeforeground="#ffffff", relief="flat", padx=16, pady=11,
            cursor="hand2"
        ).pack(side="left")
        self.install_button = tk.Button(
            buttons, text="Stáhnout a nainstalovat", command=self.install_update,
            bg="#087db4", fg="#ffffff", activebackground="#0796d8",
            activeforeground="#ffffff", relief="flat", padx=18, pady=11,
            cursor="hand2", state="disabled"
        )
        self.install_button.pack(side="right")

        tk.Label(
            outer, text="Aktualizace jsou distribuovány přes GitHub Releases.",
            font=("Segoe UI", 8), fg="#71869e", bg="#101827"
        ).pack(anchor="w", pady=(13, 0))

    @staticmethod
    def _info_row(parent, label, variable):
        row = tk.Frame(parent, bg="#19263a")
        row.pack(fill="x", pady=(10, 0))
        tk.Label(row, text=label, font=("Segoe UI", 9), fg="#aabbd0",
                 bg="#19263a").pack(side="left")
        tk.Label(row, textvariable=variable, font=("Segoe UI", 10, "bold"),
                 fg="#f3f7fb", bg="#19263a").pack(side="right")

    def _load_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            saved = data.get("community")
            if saved and Path(saved).is_dir():
                self.community.set(saved)
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        if not self.community.get():
            found = candidate_community_paths()
            if found:
                self.community.set(str(found[0]))

    def _save_settings(self):
        try:
            APP_DATA.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(
                json.dumps({"community": self.community.get()}, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    def _refresh_local_version(self):
        path = Path(self.community.get()) if self.community.get() else None
        version = read_local_version(path) if path else None
        self.local_version.set(version if version else "Nenainstalováno / nezjištěno")

    def browse_community(self):
        selected = filedialog.askdirectory(title="Vyber MSFS Community složku")
        if selected:
            self.community.set(selected)
            self._save_settings()
            self._refresh_local_version()
            self._update_button_state()

    def _set_busy(self, busy: bool):
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()

    def check_updates(self):
        self.install_button.configure(state="disabled")
        self.status.set("Kontroluji dostupnou verzi…")
        self.remote_version.set("Kontroluji…")
        self._set_busy(True)
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        try:
            release = request_json(API_URL)
            tag = str(release.get("tag_name", "")).strip()
            version = tag[1:] if tag.lower().startswith("v") else tag
            if not re.fullmatch(r"\d+(?:\.\d+){1,3}", version):
                raise ValueError(f"Neplatné číslo verze v GitHub Release: {tag!r}")
            assets = release.get("assets", [])
            asset = next((a for a in assets if a.get("name") == ASSET_NAME), None)
            if not asset:
                raise RuntimeError(
                    f"V GitHub Release {tag} chybí soubor {ASSET_NAME}."
                )
            self.events.put(("release_ok", release, asset, version))
        except Exception as exc:
            self.events.put(("error", f"Kontrola aktualizací selhala: {exc}"))

    def _update_button_state(self):
        if not self.release or not self.asset:
            self.install_button.configure(state="disabled")
            return
        local = read_local_version(Path(self.community.get())) if self.community.get() else None
        remote = self.release.get("_version", "")
        if not self.community.get():
            self.install_button.configure(state="disabled")
        elif not local or version_tuple(remote) > version_tuple(local):
            self.install_button.configure(state="normal")
        else:
            self.install_button.configure(state="disabled")

    def install_update(self):
        community = Path(self.community.get()) if self.community.get() else None
        if not community or not community.is_dir():
            messagebox.showwarning("Community složka", "Nejdřív vyber platnou Community složku.")
            return
        if not self.asset:
            messagebox.showwarning("Aktualizace", "Nejdřív zkontroluj dostupné aktualizace.")
            return
        if not messagebox.askyesno(
            "Potvrdit instalaci",
            "Před aktualizací MSFS úplně zavři.\n\n"
            "Updater nahradí pouze složku:\n"
            f"{ADDON_FOLDER}\n\n"
            "Původní verzi ponechá jako zálohu. Pokračovat?"
        ):
            return
        self.install_button.configure(state="disabled")
        self.status.set("Stahuji aktualizaci…")
        self._set_busy(True)
        threading.Thread(target=self._install_worker, args=(community,), daemon=True).start()

    def _install_worker(self, community: Path):
        try:
            APP_DATA.mkdir(parents=True, exist_ok=True)
            archive = APP_DATA / ASSET_NAME
            url = self.asset["browser_download_url"]
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as target:
                shutil.copyfileobj(response, target, length=1024 * 1024)

            expected_digest = self.asset.get("digest")
            if expected_digest and expected_digest.startswith("sha256:"):
                digest = hashlib_sha256(archive)
                if digest.lower() != expected_digest.split(":", 1)[1].lower():
                    raise RuntimeError("Kontrola SHA-256 staženého ZIPu selhala.")

            with zipfile.ZipFile(archive, "r") as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(f"ZIP je poškozený (soubor {bad}).")
                root_name = ADDON_FOLDER + "/"
                names = zf.namelist()
                if not names or any(
                    name.startswith("/") or "\\" in name or
                    ".." in PurePosixPath(name).parts or
                    not (name == ADDON_FOLDER or name.startswith(root_name))
                    for name in names
                ):
                    raise RuntimeError("ZIP nemá očekávanou bezpečnou strukturu.")
                stage = community / (".fidel-lkpr-staging-" + str(os.getpid()))
                if stage.exists():
                    shutil.rmtree(stage)
                stage.mkdir(parents=True)
                zf.extractall(stage)

            staged_addon = stage / ADDON_FOLDER
            staged_version = read_manifest_version(staged_addon / "manifest.json")
            if staged_version != self.release["_version"]:
                shutil.rmtree(stage, ignore_errors=True)
                raise RuntimeError(
                    f"Verze v ZIPu ({staged_version}) neodpovídá vydání "
                    f"({self.release['_version']})."
                )

            target = community / ADDON_FOLDER
            backup = None
            if target.exists():
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                backup = community / f"{ADDON_FOLDER}.backup-{stamp}"
                target.rename(backup)

            try:
                staged_addon.rename(target)
            except Exception:
                if backup and backup.exists() and not target.exists():
                    backup.rename(target)
                raise
            finally:
                shutil.rmtree(stage, ignore_errors=True)

            self.events.put(("install_ok", staged_version, str(backup) if backup else None))
        except Exception as exc:
            self.events.put(("error", f"Instalace selhala: {exc}"))

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                kind = event[0]
                if kind == "release_ok":
                    _, release, asset, version = event
                    release["_version"] = version
                    self.release, self.asset = release, asset
                    self.remote_version.set(version)
                    notes = release.get("body") or "K tomuto vydání nejsou připojené poznámky."
                    self.notes_text.configure(state="normal")
                    self.notes_text.delete("1.0", "end")
                    self.notes_text.insert("1.0", notes)
                    self.notes_text.configure(state="disabled")
                    self._refresh_local_version()
                    local = read_local_version(Path(self.community.get())) if self.community.get() else None
                    if not local:
                        self.status.set("Scenérie není nalezena – můžeš provést první instalaci.")
                    elif version_tuple(version) > version_tuple(local):
                        self.status.set("Je dostupná nová verze. Čas na update! ✈")
                    else:
                        self.status.set("Máš aktuální verzi scenérie.")
                    self._set_busy(False)
                    self._update_button_state()
                elif kind == "install_ok":
                    _, version, backup = event
                    self._set_busy(False)
                    self._refresh_local_version()
                    self.status.set(f"Hotovo! Scenérie byla aktualizována na {version}.")
                    self._update_button_state()
                    msg = f"Instalace verze {version} proběhla úspěšně."
                    if backup:
                        msg += f"\n\nZáloha původní verze:\n{backup}"
                    messagebox.showinfo("Instalace dokončena", msg)
                elif kind == "error":
                    _, message = event
                    self._set_busy(False)
                    self.status.set("Něco se nepovedlo.")
                    messagebox.showerror("Fidel LKPR Updater", message)
                    self._update_button_state()
        except queue.Empty:
            pass
        self.root.after(150, self._poll_events)


def read_manifest_version(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return str(data.get("package_version") or "")


def hashlib_sha256(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    root = tk.Tk()
    UpdaterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
