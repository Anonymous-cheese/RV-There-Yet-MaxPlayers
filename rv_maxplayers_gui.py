import os
import subprocess
from datetime import datetime
from typing import Tuple

import tkinter as tk
from tkinter import ttk, messagebox

MIN_PLAYERS = 4
MAX_PLAYERS = 50

SECTION_HEADER = "[/script/engine.gamesession]"
KEY = "MaxPlayers"


def run_attrib(flag: str, path: str) -> bool:
    """
    Uses Windows 'attrib' to set/unset read-only attribute reliably.
    flag: '+R' or '-R'
    """
    try:
        cmd = ["cmd.exe", "/c", "attrib", flag, path]
        completed = subprocess.run(cmd, capture_output=True, text=True)
        return completed.returncode == 0
    except Exception:
        return False


def read_text_file(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def ensure_maxplayers(contents: str, value: int) -> Tuple[str, bool]:
    """
    Returns (updated_contents, changed?)
    - Preserves existing content as much as possible.
    - Updates KEY within SECTION_HEADER if present.
    - If section missing, appends section + KEY at end.
    """
    original = contents
    text = normalize_newlines(contents)
    lines = text.split("\n")

    section_start = None
    section_end = None

    for i, line in enumerate(lines):
        if line.strip().lower() == SECTION_HEADER.lower():
            section_start = i
            break

    if section_start is not None:
        for j in range(section_start + 1, len(lines)):
            if lines[j].strip().startswith("[") and lines[j].strip().endswith("]"):
                section_end = j
                break
        if section_end is None:
            section_end = len(lines)

        key_line_idx = None
        for k in range(section_start + 1, section_end):
            stripped = lines[k].strip()
            if stripped.startswith(";") or stripped.startswith("#"):
                continue
            if stripped.lower().startswith(KEY.lower() + "="):
                key_line_idx = k
                break

        if key_line_idx is not None:
            prefix = lines[key_line_idx][:len(lines[key_line_idx]) - len(lines[key_line_idx].lstrip())]
            lines[key_line_idx] = f"{prefix}{KEY}={value}"
        else:
            lines.insert(section_end, f"{KEY}={value}")
    else:
        if len(lines) == 1 and lines[0] == "":
            lines = [SECTION_HEADER, f"{KEY}={value}"]
        else:
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.append(SECTION_HEADER)
            lines.append(f"{KEY}={value}")

    updated = "\n".join(lines).rstrip() + "\n"
    changed = normalize_newlines(original) != updated
    return updated, changed


def find_target_config_folder() -> str:
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if not localappdata:
        raise RuntimeError("LOCALAPPDATA is not set.")

    base = os.path.join(localappdata, "Ride", "Saved", "Config")
    if not os.path.isdir(base):
        raise FileNotFoundError(f"Config base folder not found: {base}")

    candidates = []
    for name in ("Windows", "WindowsGDK"):
        p = os.path.join(base, name)
        if os.path.isdir(p):
            candidates.append(p)

    if not candidates:
        candidates = [
            os.path.join(base, d)
            for d in os.listdir(base)
            if os.path.isdir(os.path.join(base, d))
        ]

    if not candidates:
        raise FileNotFoundError(f"No config subfolders found under: {base}")

    return max(candidates, key=lambda p: os.path.getmtime(p))


def backup_file(path: str, target_folder: str) -> str | None:
    if not os.path.isfile(path):
        return None
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = os.path.join(target_folder, f"{os.path.basename(path)}.bak_{ts}")
    with open(path, "rb") as r, open(backup, "wb") as w:
        w.write(r.read())
    return backup


def apply_maxplayers(value: int) -> Tuple[str, bool, str | None, bool, bool]:
    """
    Returns:
      (game_ini_path, changed, backup_path, ro_removed_ok, ro_set_ok)
    """
    target = find_target_config_folder()
    game_ini = os.path.join(target, "Game.ini")

    # Remove RO if present so we can write
    ro_removed_ok = True
    if os.path.isfile(game_ini):
        ro_removed_ok = run_attrib("-R", game_ini)

    backup_path = None
    if os.path.isfile(game_ini):
        backup_path = backup_file(game_ini, target)

    current = read_text_file(game_ini)
    updated, changed = ensure_maxplayers(current, value)

    with open(game_ini, "w", encoding="utf-8", newline="\n") as f:
        f.write(updated)

    ro_set_ok = run_attrib("+R", game_ini)
    return game_ini, changed, backup_path, ro_removed_ok, ro_set_ok


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RV There Yet - Max Players")
        self.resizable(False, False)

        pad = {"padx": 12, "pady": 10}

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, **pad)

        title = ttk.Label(frame, text="Set Max Players", font=("Segoe UI", 12, "bold"))
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(frame, text="MaxPlayers (4–50):").grid(row=1, column=0, sticky="w", padx=(0, 10))

        self.var = tk.StringVar(value="8")
        self.spin = ttk.Spinbox(
            frame,
            from_=MIN_PLAYERS,
            to=MAX_PLAYERS,
            textvariable=self.var,
            width=8,
            validate="key",
            validatecommand=(self.register(self._validate_int), "%P"),
        )
        self.spin.grid(row=1, column=1, sticky="w")

        btn = ttk.Button(frame, text="Apply", command=self.on_apply)
        btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 0))

        note = ttk.Label(
            frame,
            text="This tool edits/creates Game.ini and sets it to Read-Only.",
            wraplength=360,
        )
        note.grid(row=3, column=0, columnspan=2, sticky="w", pady=(10, 0))

    def _validate_int(self, proposed: str) -> bool:
        if proposed == "":
            return True
        if not proposed.isdigit():
            return False
        val = int(proposed)
        return 1 <= val <= 999  # range enforced on Apply

    def on_apply(self):
        raw = self.var.get().strip()
        if not raw.isdigit():
            messagebox.showerror("Invalid value", "Please enter a number.")
            return

        val = int(raw)
        if val < MIN_PLAYERS or val > MAX_PLAYERS:
            messagebox.showerror("Out of range", f"Please choose a value from {MIN_PLAYERS} to {MAX_PLAYERS}.")
            return

        try:
            game_ini, changed, backup, ro_removed_ok, ro_set_ok = apply_maxplayers(val)
        except FileNotFoundError:
            messagebox.showerror(
                "Config folder not found",
                "Could not find the game config folder.\n\nLaunch the game once, close it, then run this tool again.",
            )
            return
        except Exception as e:
            messagebox.showerror("Failed", f"Could not apply setting:\n\n{e}")
            return

        details = [
            f"Updated: {game_ini}",
            f"MaxPlayers set to: {val}",
            f"Changed: {'Yes' if changed else 'No (already set)'}",
            f"Backup: {backup if backup else 'None (file was newly created)'}",
            f"Read-Only removed to edit: {'OK' if ro_removed_ok else 'Not needed / Failed'}",
            f"Read-Only applied: {'OK' if ro_set_ok else 'Failed (set manually in Properties)'}",
            "",
            "Restart the game for changes to take effect.",
        ]
        messagebox.showinfo("Success", "\n".join(details))


if __name__ == "__main__":
    App().mainloop()
