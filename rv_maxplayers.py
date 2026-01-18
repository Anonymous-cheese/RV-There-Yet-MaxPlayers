import os
import sys
from datetime import datetime

MIN_PLAYERS = 4
MAX_PLAYERS = 40

def pause():
    try:
        input("\nPress Enter to close...")
    except Exception:
        pass

def get_max_players() -> int:
    while True:
        raw = input(f"Enter MaxPlayers ({MIN_PLAYERS}-{MAX_PLAYERS}): ").strip()
        if not raw:
            print(f"[ERROR] Please enter a number between {MIN_PLAYERS} and {MAX_PLAYERS}.")
            continue
        if not raw.isdigit():
            print("[ERROR] Invalid input. Numbers only.")
            continue
        val = int(raw)
        if val < MIN_PLAYERS or val > MAX_PLAYERS:
            print(f"[ERROR] Out of range. Must be {MIN_PLAYERS}-{MAX_PLAYERS}.")
            continue
        return val

def main():
    localappdata = os.environ.get("LOCALAPPDATA", "")
    if not localappdata:
        print("[ERROR] LOCALAPPDATA is not set.")
        pause()
        return 1

    base = os.path.join(localappdata, "Ride", "Saved", "Config")
    if not os.path.isdir(base):
        print(f"[ERROR] Config base folder not found:\n        {base}")
        print("[INFO] Launch the game at least once, then run this again.")
        pause()
        return 1

    # Prefer Windows/WindowsGDK if present; otherwise use any subfolder under Config
    candidates = []
    for name in ("Windows", "WindowsGDK"):
        p = os.path.join(base, name)
        if os.path.isdir(p):
            candidates.append(p)

    if not candidates:
        try:
            candidates = [
                os.path.join(base, d)
                for d in os.listdir(base)
                if os.path.isdir(os.path.join(base, d))
            ]
        except Exception as e:
            print(f"[ERROR] Failed to list directories under:\n        {base}\n        {e}")
            pause()
            return 1

    if not candidates:
        print(f"[ERROR] No config subfolders found under:\n        {base}")
        pause()
        return 1

    # Choose most recently modified folder
    target = max(candidates, key=lambda p: os.path.getmtime(p))
    game_ini = os.path.join(target, "Game.ini")

    max_players = get_max_players()

    content = "[/script/engine.gamesession]\n" f"MaxPlayers={max_players}\n"

    # Backup if it exists
    if os.path.isfile(game_ini):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = os.path.join(target, f"Game.ini.bak_{ts}")
        try:
            with open(game_ini, "rb") as r, open(backup, "wb") as w:
                w.write(r.read())
            print(f"\n[OK] Backup created:\n     {backup}")
        except Exception as e:
            print(f"\n[WARN] Could not create backup:\n       {e}")

    # Write Game.ini (UTF-8, newline normalized)
    try:
        with open(game_ini, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except Exception as e:
        print(f"\n[ERROR] Failed to write Game.ini:\n        {game_ini}\n        {e}")
        pause()
        return 1

    # Confirm
    if os.path.isfile(game_ini):
        print("\n[OK] SUCCESS: Game.ini was placed/updated here:")
        print(f"     {game_ini}")
        print("[INFO] Current contents:")
        try:
            with open(game_ini, "r", encoding="utf-8") as f:
                print(f.read().rstrip())
        except Exception:
            pass
        print("[OK] Restart RV There Yet for changes to take effect.")
        pause()
        return 0

    print("\n[ERROR] Write finished but Game.ini was not found (unexpected).")
    pause()
    return 1

if __name__ == "__main__":
    sys.exit(main())
