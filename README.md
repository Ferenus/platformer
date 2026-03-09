# Platformer Game

A platform game built with Pygame featuring shooting mechanics, enemies, and level progression.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install pygame
```

## Run the Game

```bash
source venv/bin/activate
python game.py
```

## Controls

| Key | Action |
|-----|--------|
| Arrow Left / A | Move left |
| Arrow Right / D | Move right |
| Arrow Up / W | Jump |
| SPACEBAR | Shoot |
| Arrow Up / W at door | Enter door (finish level) |
| R | Restart (after win/death) |
| ESC | Quit |

## Gameplay

- Kill all 6 enemies (slimes) to open the exit door
- Enter the open door with Up/W to complete Level 1
- You have 3 HP - enemies deal 1 damage on contact
- You can stomp enemies by jumping on them
- Enemies patrol platforms and turn at edges

## Testing (CLI)

```bash
source venv/bin/activate

# Run all tests
python test_cli.py

# Run specific test
python test_cli.py --test startup player_movement

# Quick smoke test
python test_cli.py --smoke

# List all tests
python test_cli.py --list

# JSON output
python test_cli.py --json
```

## Project Structure

```
platformer/
├── game.py          # Main game
├── test_cli.py      # CLI testing tool
├── README.md
├── venv/            # Python virtual environment
├── assets/Sprites/  # Game assets (Kenney)
│   ├── Characters/  # Player sprites
│   ├── Enemies/     # Enemy sprites
│   ├── Tiles/       # Platform, door, terrain tiles
│   └── Backgrounds/ # Background images
└── .claude/skills/  # Claude debugging skills
    ├── debug-game.md
    ├── run-game.md
    └── fix-game.md
```
