from __future__ import annotations

import json
import os
import queue
import re
import shutil
import threading
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
APP_NAME = "FIDEL LKPR Live - updater"
API_URL = f"https://api.github.com/repos/{OWNER}/{REPO}/releases/latest"
USER_AGENT = "Fidel-LKPR-Updater/2.0"
APP_DATA = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "FidelLKPRUpdater"
SETTINGS_FILE = APP_DATA / "settings.json"
BG = "#0b1220"
PANEL = "#121e30"
PANEL2 = "#17263b"
BORDER = "#263951"
TEXT = "#f2f6fb"
MUTED = "#9aacc2"
CYAN = "#56c8f2"
GREEN = "#50d6a0"


def resource_path(relative: str) -> Path:
    import sys
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / relative


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


def safe_is_dir(path: Path) -> bool:
    try:
        return path.is_dir()
    except (OSError, PermissionError):
        return False


def candidate_community_paths() -> list[Path]:
    local = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    roaming = Path(os.environ.get("APPDATA", Path.home()))
    candidates = [
        local / "Packages/Microsoft.Limitless_8wekyb3d8bbwe/LocalCache/Packages/Community",
        roaming / "Microsoft Flight Simulator 2024/Packages/Community",
        local / "Packages/Microsoft.FlightSimulator_8wekyb3d8bbwe/LocalCache/Packages/Community",
        roaming / "Microsoft Flight Simulator/Packages/Community",
    ]
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
    result, seen = [], set()
    for path in candidates:
        key = str(path).lower()
        if key not in seen and safe_is_dir(path):
            seen.add(key)
            result.append(path)
    return result


def request_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=25) as response:
        return json.loads(response.read().decode("utf-8"))


class UpdaterApp:
    STRINGS = {
        "en": {
            "tagline": "SCENERY UPDATER  •  MICROSOFT FLIGHT SIMULATOR",
            "airport": "VÁCLAV HAVEL AIRPORT PRAGUE  •  LKPR",
            "overview": "OVERVIEW", "status_title": "SCENERY STATUS",
            "installed": "Installed version", "latest": "Latest version",
            "checking": "Checking…", "not_installed": "Not installed",
            "connected": "Connected to GitHub Releases",
            "loading": "Loading release information…",
            "notes": "LATEST RELEASE",
            "community": "COMMUNITY FOLDER", "browse": "Browse…",
            "check": "Check for Updates", "install": "Download and Install",
            "footer": "FIDEL LKPR  |  MSFS 2020 / 2024  |  by Fidel",
            "startup": "Connecting to GitHub…",
            "checking_status": "Checking for the latest version…",
            "no_addon": "Scenery not found — ready for a first installation.",
            "update": "A new version is available. Time to update! ✈",
            "uptodate": "You are up to date.",
            "done": "Done! Scenery updated to {version}.",
            "failed_status": "Something went wrong.",
            "check_failed": "Update check failed: {error}",
            "bad_version": "Invalid version number in GitHub Release: {tag!r}",
            "missing_asset": "GitHub Release {tag} is missing {asset}.",
            "community_title": "Community folder",
            "choose_valid": "Please select a valid Community folder first.",
            "update_title": "Update",
            "check_first": "Check for updates first.",
            "confirm_title": "Confirm installation",
            "confirm": "Please completely close MSFS before continuing.\n\n"
                       "The updater will replace only this scenery folder:\n{folder}\n\n"
                       "Your previous version will be kept as a backup. Continue?",
            "zip_bad": "The ZIP archive is damaged (file {name}).",
            "zip_structure": "The ZIP does not have the expected safe folder structure.",
            "version_mismatch": "The version in the ZIP ({actual}) does not match the release ({expected}).",
            "install_failed": "Installation failed: {error}",
            "success_title": "Installation complete",
            "success": "Version {version} was installed successfully.",
            "backup": "\n\nBackup of the previous version:\n{path}",
            "no_notes": "No release notes were provided.",
            "status_ok": "You are up to date",
            "status_new": "Update available",
            "status_missing": "Ready for first install",
            "select_title": "Select the MSFS Community folder",
        },
        "cs": {
            "tagline": "AKTUALIZÁTOR SCENÉRIE  •  MICROSOFT FLIGHT SIMULATOR",
            "airport": "LETIŠTĚ VÁCLAVA HAVLA PRAHA  •  LKPR",
            "overview": "PŘEHLED", "status_title": "STAV SCENÉRIE",
            "installed": "Nainstalovaná verze", "latest": "Nejnovější verze",
            "checking": "Kontroluji…", "not_installed": "Nenainstalováno",
            "connected": "Připojeno ke GitHub Releases",
            "loading": "Načítám informace o vydání…",
            "notes": "POSLEDNÍ VYDÁNÍ",
            "community": "SLOŽKA COMMUNITY", "browse": "Vybrat…",
            "check": "Zkontrolovat aktualizace", "install": "Stáhnout a nainstalovat",
            "footer": "FIDEL LKPR  |  MSFS 2020 / 2024  |  vytvořil Fidel",
            "startup": "Připojuji se ke GitHubu…",
            "checking_status": "Kontroluji nejnovější verzi…",
            "no_addon": "Scenérie nebyla nalezena — připravena k první instalaci.",
            "update": "Je dostupná nová verze. Čas na update! ✈",
            "uptodate": "Máš aktuální verzi scenérie.",
            "done": "Hotovo! Scenérie byla aktualizována na {version}.",
            "failed_status": "Něco se nepovedlo.",
            "check_failed": "Kontrola aktualizací selhala: {error}",
            "bad_version": "Neplatné číslo verze v GitHub Release: {tag!r}",
            "missing_asset": "V GitHub Release {tag} chybí soubor {asset}.",
            "community_title": "Složka Community",
            "choose_valid": "Nejdřív vyber platnou složku Community.",
            "update_title": "Aktualizace",
            "check_first": "Nejdřív zkontroluj dostupné aktualizace.",
            "confirm_title": "Potvrdit instalaci",
            "confirm": "Před pokračováním úplně zavři MSFS.\n\n"
                       "Updater nahradí pouze tuto složku scenérie:\n{folder}\n\n"
                       "Původní verzi ponechá jako zálohu. Pokračovat?",
            "zip_bad": "ZIP archiv je poškozený (soubor {name}).",
            "zip_structure": "ZIP nemá očekávanou bezpečnou strukturu.",
            "version_mismatch": "Verze v ZIPu ({actual}) neodpovídá vydání ({expected}).",
            "install_failed": "Instalace selhala: {error}",
            "success_title": "Instalace dokončena",
            "success": "Instalace verze {version} proběhla úspěšně.",
            "backup": "\n\nZáloha původní verze:\n{path}",
            "no_notes": "K tomuto vydání nejsou připojené poznámky.",
            "status_ok": "Máš aktuální verzi",
            "status_new": "Dostupná aktualizace",
            "status_missing": "Připraveno k první instalaci",
            "select_title": "Vyber MSFS složku Community",
        },
    }

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_NAME)
        # Open in a normal, fixed-size window matching the user's reference screenshot.
        # 820px client height leaves room for the Windows title bar within ~850px total.
        self.root.geometry("1018x790")
        self.root.minsize(900, 700)
        self.root.resizable(True, True)
        self.root.configure(bg=BG)
        try:
            self.app_icon = tk.PhotoImage(file=str(resource_path("assets/app_icon.png")))
            self.root.iconphoto(True, self.app_icon)
        except (tk.TclError, OSError):
            self.app_icon = None
        try:
            ico_file = str(resource_path("assets/app_icon.ico"))
            self.root.iconbitmap(ico_file)
            self.root.wm_iconbitmap(ico_file)
        except (tk.TclError, OSError):
            pass
        self.root.state("normal")
        self.events: queue.Queue = queue.Queue()
        self.release = None
        self.asset = None
        self.community = tk.StringVar()
        self.language = tk.StringVar(value="en")
        self.lang_code = "en"
        self.local_version = tk.StringVar(value="—")
        self.remote_version = tk.StringVar(value="—")
        self.status = tk.StringVar(value=self.t("startup"))
        self.install_button = None
        self.card_label_widgets = {}
        self._load_settings()
        self._build_ui()
        self._refresh_local_version()
        self.root.after(150, self._poll_events)
        self.check_updates()

    def t(self, key: str) -> str:
        return self.STRINGS[self.lang_code].get(key, key)

    def _load_settings(self):
        try:
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            saved = data.get("community")
            if saved and safe_is_dir(Path(saved)):
                self.community.set(saved)
            lang = data.get("language")
            if lang in ("en", "cs"):
                self.language.set(lang)
                self.lang_code = lang
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
        if not self.community.get():
            found = candidate_community_paths()
            if found:
                self.community.set(str(found[0]))

    def _save_settings(self):
        try:
            APP_DATA.mkdir(parents=True, exist_ok=True)
            SETTINGS_FILE.write_text(json.dumps({
                "community": self.community.get(), "language": self.language.get()
            }, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TProgressbar", troughcolor="#203047",
                        background=CYAN, bordercolor="#203047",
                        lightcolor=CYAN, darkcolor=CYAN)

        shell = tk.Frame(self.root, bg=BG, padx=16, pady=10)
        shell.pack(fill="both", expand=True)

        # Header is a Frame with a separate background-image Label. Text and controls
        # are sibling widgets above the image, so switching language cannot cover them.
        self.banner_photo = tk.PhotoImage(file=str(resource_path("assets/lkpr_header.png")))
        banner = tk.Frame(shell, bg=BG, height=self.banner_photo.height(),
                          width=self.banner_photo.width(), bd=0, highlightthickness=0)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        self.banner_background = tk.Label(banner, image=self.banner_photo,
                                           bd=0, bg=BG, highlightthickness=0)
        self.banner_background.place(x=0, y=0, relwidth=1, relheight=1)
        self.banner_overlay = tk.Frame(banner, bg="#091321", bd=0,
                                        highlightthickness=0)
        self.banner_overlay.place(x=22, y=22)
        overlay = self.banner_overlay
        title_row = tk.Frame(overlay, bg="#091321")
        title_row.pack(anchor="w")
        self.brand_fidel = tk.Label(title_row, text="FIDEL", font=("Segoe UI", 25, "bold"),
                 fg=TEXT, bg="#091321")
        self.brand_fidel.pack(side="left")
        self.brand_lkpr = tk.Label(title_row, text=" LKPR", font=("Segoe UI", 25, "bold"),
                 fg=CYAN, bg="#091321")
        self.brand_lkpr.pack(side="left")
        self.brand_live = tk.Label(title_row, text=" Live", font=("Segoe UI", 25, "bold"),
                 fg=TEXT, bg="#091321")
        self.brand_live.pack(side="left")
        self.edition_label = tk.Label(overlay, text="TAILSTRIKE EDITION",
                 font=("Segoe UI", 12, "bold"), fg="#ffffff", bg="#091321")
        self.edition_label.pack(anchor="w", pady=(1, 3))
        self.tagline_label = tk.Label(overlay,
                 text="SCENERY UPDATER for Microsoft Flight Simulator 2024",
                 font=("Segoe UI", 8, "bold"), fg="#d2deeb", bg="#091321")
        self.tagline_label.pack(anchor="w")
        self.airport_label = tk.Label(banner, text=self.t("airport"),
                 font=("Segoe UI", 9, "bold"), fg=TEXT, bg="#142033",
                 padx=11, pady=7)
        self.airport_label.place(relx=1.0, x=-16, y=16, anchor="ne")

        # Compact flag buttons instead of the native ttk combobox.
        self.lang_frame = tk.Frame(banner, bg="#101b2b",
                                   highlightthickness=1, highlightbackground="#50647d")
        self.lang_frame.place(relx=1.0, rely=1.0, x=-16, y=-12, anchor="se")
        self.flag_uk_photo = tk.PhotoImage(file=str(resource_path("assets/flag_uk.png")))
        self.flag_cz_photo = tk.PhotoImage(file=str(resource_path("assets/flag_cz.png")))
        self.lang_en = tk.Button(self.lang_frame, text="  EN",
                 image=self.flag_uk_photo, compound="left",
                 command=lambda: self._set_language("en"), font=("Segoe UI", 9, "bold"),
                 relief="flat", bd=0, padx=7, pady=4, cursor="hand2")
        self.lang_cs = tk.Button(self.lang_frame, text="  CZ",
                 image=self.flag_cz_photo, compound="left",
                 command=lambda: self._set_language("cs"), font=("Segoe UI", 9, "bold"),
                 relief="flat", bd=0, padx=7, pady=4, cursor="hand2")
        self.lang_en.pack(side="left")
        self.lang_cs.pack(side="left")
        self._style_language_buttons()
        self.banner_background.lower()
        self.banner_overlay.lift()
        self.airport_label.lift()
        self.lang_frame.lift()

        heading = tk.Frame(shell, bg=BG)
        heading.pack(fill="x", pady=(3, 8))
        tk.Label(heading, text="▤", font=("Segoe UI Symbol", 18),
                 fg=CYAN, bg=BG).pack(side="left", padx=(0, 9))
        self.heading_label = tk.Label(heading, text=self.t("status_title"), font=("Segoe UI", 12, "bold"),
                 fg=TEXT, bg=BG)
        self.heading_label.pack(side="left")

        cards = tk.Frame(shell, bg=BG)
        cards.pack(fill="x")
        self.installed_card = self._version_card(cards, "installed", self.local_version)
        self.installed_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.latest_card = self._version_card(cards, "latest", self.remote_version)
        self.latest_card.pack(side="left", fill="both", expand=True, padx=(8, 0))

        self.status_panel = tk.Frame(shell, bg=PANEL, highlightthickness=1,
                                     highlightbackground=BORDER, padx=16, pady=12)
        self.status_panel.pack(fill="x", pady=(7, 7))
        self.status_icon = tk.Label(self.status_panel, text="●", font=("Segoe UI", 18, "bold"),
                                    fg=CYAN, bg=PANEL)
        self.status_icon.pack(side="left", padx=(0, 12))
        self.status_label = tk.Label(self.status_panel, textvariable=self.status,
                                     font=("Segoe UI", 11, "bold"), fg=CYAN,
                                     bg=PANEL, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)

        notes = tk.Frame(shell, bg=PANEL, highlightthickness=1,
                         highlightbackground=BORDER, padx=16, pady=12)
        notes.pack(fill="both", expand=True, pady=(0, 0))
        self.notes_heading = tk.Label(notes, text=self.t("notes"), font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=PANEL)
        self.notes_heading.pack(anchor="w")
        self.notes_text = tk.Text(notes, height=3, wrap="word", relief="flat",
                                  bg=PANEL, fg="#d8e3ef", insertbackground=TEXT,
                                  font=("Segoe UI", 9), padx=0, pady=8,
                                  highlightthickness=0)
        self.notes_text.pack(fill="both", expand=True)
        self.notes_text.insert("1.0", self.t("loading"))
        self.notes_text.configure(state="disabled")

        pathbox = tk.Frame(shell, bg=BG)
        pathbox.pack(fill="x", pady=(7, 0))
        self.community_heading = tk.Label(pathbox, text=self.t("community"), font=("Segoe UI", 8, "bold"),
                 fg=MUTED, bg=BG)
        self.community_heading.pack(anchor="w", pady=(0, 6))
        row = tk.Frame(pathbox, bg=BG)
        row.pack(fill="x")
        self.path_entry = tk.Entry(row, textvariable=self.community, relief="flat",
                                   bg=PANEL2, fg=TEXT, insertbackground=TEXT,
                                   font=("Segoe UI", 9), bd=0)
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.browse_button = tk.Button(row, text=self.t("browse"), command=self.browse_community,
                                       bg=PANEL2, fg=TEXT, activebackground=BORDER,
                                       activeforeground=TEXT, relief="flat", padx=16,
                                       pady=8, cursor="hand2")
        self.browse_button.pack(side="left", padx=(8, 0))

        progress_row = tk.Frame(shell, bg=BG)
        progress_row.pack(fill="x", pady=(7, 0))
        self.progress = ttk.Progressbar(progress_row, mode="determinate",
                                        maximum=100, value=0)
        self.progress.pack(side="left", fill="x", expand=True)
        self.progress_percent = tk.Label(progress_row, text="",
                                          font=("Segoe UI", 8, "bold"),
                                          fg=CYAN, bg=BG, width=5, anchor="e")
        self.progress_percent.pack(side="right", padx=(8, 0))
        actions = tk.Frame(shell, bg=BG)
        actions.pack(fill="x", pady=(7, 0))
        self.check_button = tk.Button(actions, text=self.t("check"), command=self.check_updates,
                                      bg=PANEL2, fg=TEXT, activebackground=BORDER,
                                      activeforeground=TEXT, relief="flat", padx=18,
                                      pady=12, cursor="hand2")
        self.check_button.pack(side="left")
        self.install_button = tk.Button(actions, text=self.t("install"),
                                        command=self.install_update, bg="#087db4",
                                        fg="#ffffff", activebackground="#0796d8",
                                        activeforeground="#ffffff", relief="flat",
                                        padx=20, pady=12, cursor="hand2", state="disabled")
        self.install_button.pack(side="right")
        foot = tk.Frame(shell, bg=BG)
        foot.pack(side="bottom", fill="x", pady=(7, 0))
        self.connection_label = tk.Label(foot, text="●  " + self.t("connected"),
                                         font=("Segoe UI", 8), fg=GREEN, bg=BG)
        self.connection_label.pack(side="left")
        self.footer_label = tk.Label(foot, text=self.t("footer"),
                                     font=("Segoe UI", 8), fg="#70839b", bg=BG)
        self.footer_label.pack(side="right")

    def _version_card(self, parent, label_key, variable):
        card = tk.Frame(parent, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER, padx=16, pady=13)
        label_widget = tk.Label(card, text=self.t(label_key), font=("Segoe UI", 8, "bold"),
                                fg=MUTED, bg=PANEL)
        label_widget.pack(anchor="w")
        self.card_label_widgets[label_key] = label_widget
        tk.Label(card, textvariable=variable, font=("Segoe UI", 23, "bold"),
                 fg=TEXT, bg=PANEL).pack(anchor="w", pady=(4, 0))
        return card

    def _set_language(self, code: str):
        self.lang_code = code
        self.language.set(code)
        self._save_settings()
        self._style_language_buttons()
        self._rebuild_labels()

    def _style_language_buttons(self):
        selected_bg, idle_bg = "#087fb5", "#17263b"
        for code, button in (("en", self.lang_en), ("cs", self.lang_cs)):
            active = self.lang_code == code
            button.configure(
                bg=selected_bg if active else idle_bg,
                fg="#ffffff" if active else "#b7c7d9",
                activebackground="#0796d8" if active else "#263951",
                activeforeground="#ffffff",
            )

    def _rebuild_labels(self):
        # Rebuild only visible labels/buttons; state and background workers remain untouched.
        self.root.title(APP_NAME)
        self._style_language_buttons()
        self.tagline_label.configure(
            text="SCENERY UPDATER for Microsoft Flight Simulator 2024")
        # Tk can occasionally redraw the photo label over placed children on Windows.
        # Explicitly restore the header overlays after a language switch.
        self.banner_background.lower()
        self.banner_overlay.lift()
        self.airport_label.lift()
        self.lang_frame.lift()
        self.airport_label.configure(text=self.t("airport"))
        self.heading_label.configure(text=self.t("status_title"))
        self.notes_heading.configure(text=self.t("notes"))
        self.community_heading.configure(text=self.t("community"))
        for key, widget in self.card_label_widgets.items():
            widget.configure(text=self.t(key))
        self._refresh_local_version()
        if self.release:
            self.notes_text.configure(state="normal")
            self.notes_text.delete("1.0", "end")
            self.notes_text.insert("1.0", self.release.get("body") or self.t("no_notes"))
            self.notes_text.configure(state="disabled")
        self.browse_button.configure(text=self.t("browse"))
        self.check_button.configure(text=self.t("check"))
        self.install_button.configure(text=self.t("install"))
        self.status_label.configure(text=self.status.get())
        self.connection_label.configure(text="●  " + self.t("connected"))
        self.footer_label.configure(text=self.t("footer"))
        # Update static section headings by walking their known widgets.
        for widget in self.root.winfo_children():
            self._translate_tree(widget)

    def _translate_tree(self, widget):
        # Labels are tagged by their original English/Czech-independent role at creation.
        key = getattr(widget, "_translation_key", None)
        if key:
            widget.configure(text=self.t(key))
        for child in widget.winfo_children():
            self._translate_tree(child)

    def _load_settings_after_selection(self):
        self._save_settings()
        self._refresh_local_version()
        self._update_button_state()

    def browse_community(self):
        selected = filedialog.askdirectory(title=self.t("select_title"))
        if selected:
            self.community.set(selected)
            self._load_settings_after_selection()

    def _refresh_local_version(self):
        path = Path(self.community.get()) if self.community.get() else None
        version = read_local_version(path) if path else None
        self.local_version.set(version if version else self.t("not_installed"))

    def _set_busy(self, busy: bool):
        if busy:
            self.progress.configure(mode="indeterminate")
            self.progress_percent.configure(text="")
            self.progress.start(10)
        else:
            self.progress.stop()
            self.progress.configure(mode="determinate")
            self.progress["value"] = 0
            self.progress_percent.configure(text="")

    def _set_download_progress(self, percent: int):
        percent = max(0, min(100, int(percent)))
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = percent
        self.progress_percent.configure(text=f"{percent}%")

    def check_updates(self):
        self.install_button.configure(state="disabled")
        self.status.set(self.t("checking_status"))
        self.status_label.configure(fg=CYAN)
        self.remote_version.set(self.t("checking"))
        self._set_busy(True)
        threading.Thread(target=self._check_worker, daemon=True).start()

    def _check_worker(self):
        try:
            release = request_json(API_URL)
            tag = str(release.get("tag_name", "")).strip()
            version = tag[1:] if tag.lower().startswith("v") else tag
            if not re.fullmatch(r"\d+(?:\.\d+){1,3}", version):
                raise ValueError(self.t("bad_version").format(tag=tag))
            assets = release.get("assets", [])
            asset = next((a for a in assets if a.get("name") == ASSET_NAME), None)
            if not asset:
                raise RuntimeError(self.t("missing_asset").format(tag=tag, asset=ASSET_NAME))
            self.events.put(("release_ok", release, asset, version))
        except Exception as exc:
            self.events.put(("error", self.t("check_failed").format(error=exc)))

    def _update_button_state(self):
        if not self.release or not self.asset:
            self.install_button.configure(state="disabled")
            return
        local = read_local_version(Path(self.community.get())) if self.community.get() else None
        remote = self.release.get("_version", "")
        enabled = bool(self.community.get()) and (not local or version_tuple(remote) > version_tuple(local))
        self.install_button.configure(state="normal" if enabled else "disabled")

    def install_update(self):
        community = Path(self.community.get()) if self.community.get() else None
        if not community or not safe_is_dir(community):
            messagebox.showwarning(self.t("community_title"), self.t("choose_valid"))
            return
        if not self.asset:
            messagebox.showwarning(self.t("update_title"), self.t("check_first"))
            return
        if not messagebox.askyesno(self.t("confirm_title"),
                self.t("confirm").format(folder=ADDON_FOLDER)):
            return
        self.install_button.configure(state="disabled")
        self.status.set(self.t("checking_status"))
        self.progress.stop()
        self.progress.configure(mode="determinate")
        self.progress["value"] = 0
        self.progress_percent.configure(text="0%")
        threading.Thread(target=self._install_worker, args=(community,), daemon=True).start()

    def _install_worker(self, community: Path):
        try:
            APP_DATA.mkdir(parents=True, exist_ok=True)
            archive = APP_DATA / ASSET_NAME
            req = urllib.request.Request(self.asset["browser_download_url"],
                                         headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=60) as response, archive.open("wb") as target:
                total = int(response.headers.get("Content-Length") or 0)
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 256)
                    if not chunk:
                        break
                    target.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = min(99, int(downloaded * 100 / total))
                        self.events.put(("download_progress", pct))
                self.events.put(("download_progress", 100))
            expected_digest = self.asset.get("digest")
            if expected_digest and expected_digest.startswith("sha256:"):
                if hashlib_sha256(archive).lower() != expected_digest.split(":", 1)[1].lower():
                    raise RuntimeError("SHA-256 verification failed.")
            with zipfile.ZipFile(archive, "r") as zf:
                bad = zf.testzip()
                if bad:
                    raise RuntimeError(self.t("zip_bad").format(name=bad))
                root_name = ADDON_FOLDER + "/"
                names = zf.namelist()
                if not names or any(name.startswith("/") or "\\" in name or
                    ".." in PurePosixPath(name).parts or
                    not (name == ADDON_FOLDER or name.startswith(root_name)) for name in names):
                    raise RuntimeError(self.t("zip_structure"))
                stage = community / (".fidel-lkpr-staging-" + str(os.getpid()))
                if stage.exists():
                    shutil.rmtree(stage)
                stage.mkdir(parents=True)
                zf.extractall(stage)
            staged_addon = stage / ADDON_FOLDER
            staged_version = read_manifest_version(staged_addon / "manifest.json")
            if staged_version != self.release["_version"]:
                shutil.rmtree(stage, ignore_errors=True)
                raise RuntimeError(self.t("version_mismatch").format(
                    actual=staged_version, expected=self.release["_version"]))
            target, backup = community / ADDON_FOLDER, None
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
            self.events.put(("error", self.t("install_failed").format(error=exc)))

    def _poll_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                if event[0] == "download_progress":
                    self._set_download_progress(event[1])
                elif event[0] == "release_ok":
                    _, release, asset, version = event
                    release["_version"] = version
                    self.release, self.asset = release, asset
                    self.remote_version.set(version)
                    notes = release.get("body") or self.t("no_notes")
                    self.notes_text.configure(state="normal")
                    self.notes_text.delete("1.0", "end")
                    self.notes_text.insert("1.0", notes)
                    self.notes_text.configure(state="disabled")
                    self._refresh_local_version()
                    local = read_local_version(Path(self.community.get())) if self.community.get() else None
                    if not local:
                        self.status.set(self.t("no_addon"))
                        self.status_label.configure(fg=CYAN)
                    elif version_tuple(version) > version_tuple(local):
                        self.status.set(self.t("update"))
                        self.status_label.configure(fg="#f4bd63")
                    else:
                        self.status.set(self.t("uptodate"))
                        self.status_label.configure(fg=GREEN)
                    self._set_busy(False)
                    self._update_button_state()
                elif event[0] == "install_ok":
                    _, version, backup = event
                    self.progress.stop()
                    self.progress.configure(mode="determinate")
                    self.progress["value"] = 100
                    self.progress_percent.configure(text="100%")
                    self._refresh_local_version()
                    self.status.set(self.t("done").format(version=version))
                    self.status_label.configure(fg=GREEN)
                    self._update_button_state()
                    msg = self.t("success").format(version=version)
                    if backup:
                        msg += self.t("backup").format(path=backup)
                    messagebox.showinfo(self.t("success_title"), msg)
                elif event[0] == "error":
                    _, message = event
                    self._set_busy(False)
                    self.status.set(self.t("failed_status"))
                    self.status_label.configure(fg="#ff8c8c")
                    messagebox.showerror(APP_NAME, message)
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
