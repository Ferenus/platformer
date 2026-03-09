# Debug Game Skill

Use this skill to debug the platformer game end-to-end.

## Trigger
When the user says "debug game", "test game", "check game", or wants to verify the game works.

## Steps

1. Activate the virtual environment: `source venv/bin/activate`
2. Run the full test suite: `python test_cli.py --json`
3. Analyze the JSON output for any failures
4. If tests fail:
   - Read the traceback in the failed test details
   - Identify the root cause in `game.py`
   - Fix the issue
   - Re-run tests to confirm the fix
5. If all tests pass, run the smoke test for extra validation: `python test_cli.py --smoke`
6. Report results to the user

## Key Files
- `game.py` - Main game code
- `test_cli.py` - CLI testing tool
- `assets/Sprites/` - Game assets

## Common Issues
- Sprite loading errors: check asset paths in `game.py` constants
- Physics bugs: check GRAVITY, JUMP_FORCE, PLAYER_SPEED constants
- Level layout: check LEVEL_1 tile map in `game.py`
- Enemy spawning: check `build_level()` enemy zone calculation
