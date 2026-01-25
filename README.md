# RV There Yet — MaxPlayers Config Tool (Windows)

A small Windows tool that updates the game’s `Game.ini` to set:

```
[/script/engine.gamesession]
MaxPlayers=<4..40>
```

It automatically finds the correct config folder under `%LOCALAPPDATA%`, creates a backup of any existing `Game.ini`, writes the new value, and confirms success.

---

## Features

- Works on **Windows 10 / 11**
- Sets **MaxPlayers (4–40)**
- Automatically locates the game config folder:
  - `%LOCALAPPDATA%\Ride\Saved\Config\Windows\Game.ini`
  - `%LOCALAPPDATA%\Ride\Saved\Config\WindowsGDK\Game.ini`
  - Falls back to the most recently modified subfolder under `...\Ride\Saved\Config\`
- Creates a timestamped backup if `Game.ini` already exists:
  - `Game.ini.bak_YYYYMMDD_HHMMSS`
- Prints a clear confirmation and shows the final file contents

---

## How It Works

1. Prompts you to enter `MaxPlayers` from **4 to 40**
2. Finds the game config directory under `%LOCALAPPDATA%\Ride\Saved\Config`
3. Chooses the best target folder (Windows / WindowsGDK preferred; otherwise most recently modified)
4. Backs up any existing `Game.ini`
5. Writes a new `Game.ini` containing:
   ```
   [/script/engine.gamesession]
   MaxPlayers=<your value>
   ```
6. Confirms success with the exact path and prints the file contents

---

## Notes on Compatibility

- The EXE is architecture-specific:
  - Build on 64-bit Windows → `x64` EXE (most common)
  - For 32-bit systems (rare), build using 32-bit Python
- Unsigned EXEs may trigger Windows SmartScreen on some PCs. This is normal for custom-built executables.

---

## Troubleshooting

### “Config base folder not found”
The tool checks for:

`%LOCALAPPDATA%\Ride\Saved\Config`

If it does not exist, launch the game once, then run the tool again.

### “No config subfolders found”
The tool expects at least one subfolder under `...\Ride\Saved\Config` (commonly `Windows` or `WindowsGDK`). Launch the game once, then retry.

---

## Safety

- The tool only modifies `Game.ini` inside the game’s local config folder.
- It creates a backup before overwriting.

---
## Download From Releases on Right Side
---
