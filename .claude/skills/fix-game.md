# Fix Game Skill

Use this skill to diagnose and fix specific game issues.

## Trigger
When the user reports a bug or issue with the game.

## Steps

1. Run specific tests related to the issue:
   - Movement bugs: `python test_cli.py --test player_movement player_jump`
   - Combat bugs: `python test_cli.py --test bullet_creation enemy_death enemy_spawn`
   - Level bugs: `python test_cli.py --test level_structure door_mechanics`
   - General crash: `python test_cli.py --test startup smoke`

2. If tests pass but user reports visual/gameplay issue:
   - Read `game.py` focusing on the relevant section
   - Check constants (GRAVITY, JUMP_FORCE, PLAYER_SPEED, etc.)
   - Check the LEVEL_1 tile map
   - Check sprite loading paths

3. Fix the issue in `game.py`
4. Re-run full test suite: `python test_cli.py`
5. Confirm fix

## Game Architecture
- `Player` class: movement, jumping, health, animation
- `Enemy` class: patrol AI, death, animation
- `Bullet` class: projectile physics
- `Door` class: level exit (opens when all enemies dead)
- `Camera` class: viewport following player
- `build_level()`: parses LEVEL_1 tile map
- `run_game()`: main game loop with headless support
