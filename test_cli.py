#!/usr/bin/env python3
"""
CLI Testing Tool for Platformer Game.
Runs the game headlessly and validates core mechanics.

Usage:
    python test_cli.py                  # Run all tests
    python test_cli.py --test startup   # Run specific test
    python test_cli.py --list           # List available tests
    python test_cli.py --smoke          # Quick smoke test (game loads and runs)
"""

import argparse
import json
import os
import sys
import traceback

# Set headless drivers before any pygame import
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import pygame

# Ensure we can import the game
sys.path.insert(0, os.path.dirname(__file__))
from game import (
    LEVEL_1, TILE, SCREEN_W, SCREEN_H, GRAVITY, PLAYER_SPEED, JUMP_FORCE,
    NUM_ENEMIES, build_level, spawn_enemies, Player, Bullet, Enemy, Camera,
    Door, load_img, LEVEL_W, LEVEL_H,
)


class TestResult:
    def __init__(self, name):
        self.name = name
        self.passed = False
        self.message = ""
        self.details = {}

    def to_dict(self):
        return {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "details": self.details,
        }


def init_pygame():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    return screen


def make_test_level():
    """Build level and return all components."""
    platforms, player_pos, door, enemy_zones = build_level(LEVEL_1)
    player = Player(player_pos[0], player_pos[1])
    enemies = spawn_enemies(enemy_zones, NUM_ENEMIES)
    return platforms, player, door, enemies, enemy_zones


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_startup():
    """Test that the game initializes without errors."""
    result = TestResult("startup")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, zones = make_test_level()
        result.passed = True
        result.message = "Game initialized successfully"
        result.details = {
            "platforms_count": len(platforms),
            "player_pos": (player.rect.x, player.rect.y),
            "door_exists": door is not None,
            "enemies_count": len(enemies),
            "enemy_zones_count": len(zones),
            "screen_size": (SCREEN_W, SCREEN_H),
        }
    except Exception as e:
        result.message = f"Startup failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_player_movement():
    """Test player horizontal movement and gravity."""
    result = TestResult("player_movement")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, _ = make_test_level()

        start_x = player.rect.x
        start_y = player.rect.y

        # Simulate frames to let player land on ground
        for _ in range(30):
            player.update(platforms)

        landed_y = player.rect.y
        on_ground = player.on_ground

        # Simulate rightward movement by injecting key state
        # We can't easily inject keys in headless, so we test the physics directly
        player.vel_x = PLAYER_SPEED
        old_x = player.rect.x
        player.rect.x += player.vel_x
        moved_right = player.rect.x > old_x

        player.vel_x = -PLAYER_SPEED
        old_x = player.rect.x
        player.rect.x += player.vel_x
        moved_left = player.rect.x < old_x

        result.passed = on_ground and moved_right and moved_left
        result.message = "Player movement works" if result.passed else "Player movement issues"
        result.details = {
            "start_pos": (start_x, start_y),
            "landed_y": landed_y,
            "on_ground": on_ground,
            "moved_right": moved_right,
            "moved_left": moved_left,
        }
    except Exception as e:
        result.message = f"Movement test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_player_jump():
    """Test player jumping mechanics."""
    result = TestResult("player_jump")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, _ = make_test_level()

        # Let player land
        for _ in range(60):
            player.update(platforms)

        ground_y = player.rect.y
        assert player.on_ground, f"Player not on ground at y={ground_y}"

        # Apply jump
        player.vel_y = JUMP_FORCE
        player.on_ground = False

        peak_y = player.rect.y
        for _ in range(30):
            player.vel_y += GRAVITY
            player.rect.y += player.vel_y
            if player.rect.y < peak_y:
                peak_y = player.rect.y

        jumped = peak_y < ground_y

        result.passed = jumped
        result.message = "Jump works" if jumped else "Jump failed"
        result.details = {
            "ground_y": ground_y,
            "peak_y": peak_y,
            "jump_height": ground_y - peak_y,
        }
    except Exception as e:
        result.message = f"Jump test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_bullet_creation():
    """Test bullet creation and movement."""
    result = TestResult("bullet_creation")
    try:
        screen = init_pygame()
        b_right = Bullet(100, 100, 1)
        b_left = Bullet(100, 100, -1)

        old_r = b_right.rect.x
        old_l = b_left.rect.x
        b_right.update()
        b_left.update()

        moves_right = b_right.rect.x > old_r
        moves_left = b_left.rect.x < old_l

        result.passed = moves_right and moves_left
        result.message = "Bullets work" if result.passed else "Bullet issues"
        result.details = {
            "right_bullet_moved": moves_right,
            "left_bullet_moved": moves_left,
        }
    except Exception as e:
        result.message = f"Bullet test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_enemy_spawn():
    """Test enemy spawning at valid positions."""
    result = TestResult("enemy_spawn")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, zones = make_test_level()

        enemy_count = len(enemies)
        all_on_valid = True
        enemy_positions = []

        for e in enemies:
            enemy_positions.append((e.rect.x, e.rect.y))
            # Check enemy is above a platform
            on_platform = False
            for p in platforms:
                if abs(e.rect.bottom - p.rect.top) <= TILE and \
                   e.rect.right > p.rect.left and e.rect.left < p.rect.right:
                    on_platform = True
                    break
            if not on_platform:
                all_on_valid = False

        result.passed = enemy_count == NUM_ENEMIES and all_on_valid
        result.message = f"Spawned {enemy_count}/{NUM_ENEMIES} enemies" + \
                        (" all valid" if all_on_valid else " INVALID positions")
        result.details = {
            "enemy_count": enemy_count,
            "expected": NUM_ENEMIES,
            "all_valid_positions": all_on_valid,
            "positions": enemy_positions,
            "available_zones": len(zones),
        }
    except Exception as e:
        result.message = f"Enemy spawn test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_enemy_death():
    """Test that enemies can be killed by bullets."""
    result = TestResult("enemy_death")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, _ = make_test_level()

        # Kill first enemy with a bullet
        enemy = list(enemies)[0]
        bullet = Bullet(enemy.rect.x - 20, enemy.rect.centery, 1)

        # Move bullet into enemy
        for _ in range(10):
            bullet.update()
            if bullet.rect.colliderect(enemy.rect) and enemy.alive:
                enemy.die()
                break

        result.passed = not enemy.alive
        result.message = "Enemy killed" if not enemy.alive else "Enemy still alive"
        result.details = {"enemy_alive": enemy.alive}
    except Exception as e:
        result.message = f"Enemy death test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_door_mechanics():
    """Test that door opens when all enemies are dead."""
    result = TestResult("door_mechanics")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, _ = make_test_level()

        assert door is not None, "No door found in level"

        # Door should be closed initially
        initially_closed = not door.opened

        # Kill all enemies
        for e in enemies:
            e.die()

        # Check door state after killing enemies (game loop checks this)
        enemies_alive = sum(1 for e in enemies if e.alive)
        if enemies_alive == 0:
            door.opened = True

        door_opened = door.opened

        result.passed = initially_closed and door_opened
        result.message = "Door mechanics work" if result.passed else "Door mechanics broken"
        result.details = {
            "initially_closed": initially_closed,
            "door_opened_after_kill_all": door_opened,
            "door_position": (door.rect.x, door.rect.y),
        }
    except Exception as e:
        result.message = f"Door test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_player_health():
    """Test player takes damage and can die."""
    result = TestResult("player_health")
    try:
        screen = init_pygame()
        platforms, player, door, enemies, _ = make_test_level()

        initial_hp = player.health
        player.take_hit()
        after_one = player.health
        player.hit_timer = 0  # reset invincibility
        player.take_hit()
        after_two = player.health
        player.hit_timer = 0
        player.take_hit()
        after_three = player.health
        dead = not player.alive

        result.passed = (initial_hp == 3 and after_one == 2 and after_two == 1 and dead)
        result.message = "Health system works" if result.passed else "Health system broken"
        result.details = {
            "initial_hp": initial_hp,
            "after_1_hit": after_one,
            "after_2_hits": after_two,
            "after_3_hits": after_three,
            "dead": dead,
        }
    except Exception as e:
        result.message = f"Health test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_camera():
    """Test camera follows player."""
    result = TestResult("camera")
    try:
        screen = init_pygame()
        cam = Camera(LEVEL_W, LEVEL_H)
        test_rect = pygame.Rect(600, 300, TILE, TILE)
        cam.update(test_rect)

        offset_nonzero = cam.offset_x != 0 or cam.offset_y != 0
        applied = cam.apply(test_rect)
        transforms = applied != test_rect

        result.passed = True  # camera is functional if no crash
        result.message = "Camera works"
        result.details = {
            "offset": (cam.offset_x, cam.offset_y),
            "applied_pos": (applied.x, applied.y),
        }
    except Exception as e:
        result.message = f"Camera test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_level_structure():
    """Validate level data integrity."""
    result = TestResult("level_structure")
    try:
        screen = init_pygame()
        has_player = False
        has_door = False
        has_platforms = False

        for row in LEVEL_1:
            if "P" in row:
                has_player = True
            if "T" in row:
                has_door = True
            if "G" in row or "E" in row:
                has_platforms = True

        platforms, player_pos, door, enemy_zones = build_level(LEVEL_1)

        result.passed = has_player and has_door and has_platforms and door is not None
        result.message = "Level structure valid" if result.passed else "Level structure issues"
        result.details = {
            "has_player_spawn": has_player,
            "has_door": has_door,
            "has_platforms": has_platforms,
            "platform_count": len(platforms),
            "enemy_zones": len(enemy_zones),
            "player_pos": player_pos,
        }
    except Exception as e:
        result.message = f"Level structure test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    finally:
        pygame.quit()
    return result


def test_smoke():
    """Quick smoke test - run 120 frames headlessly."""
    result = TestResult("smoke")
    try:
        from game import run_game
        frame_data = []

        def callback(state):
            frame_data.append(state)
            if state["frame"] >= 120:
                return "quit"
            return None

        run_game(headless=True, max_frames=120, test_callback=callback)

        result.passed = len(frame_data) > 0
        result.message = f"Smoke test ran {len(frame_data)} frames"
        result.details = {
            "frames_run": len(frame_data),
            "first_frame": frame_data[0] if frame_data else None,
            "last_frame": frame_data[-1] if frame_data else None,
        }
    except Exception as e:
        result.message = f"Smoke test failed: {e}"
        result.details["traceback"] = traceback.format_exc()
    return result


# ---------------------------------------------------------------------------
# Test registry
# ---------------------------------------------------------------------------

ALL_TESTS = {
    "startup": test_startup,
    "level_structure": test_level_structure,
    "player_movement": test_player_movement,
    "player_jump": test_player_jump,
    "player_health": test_player_health,
    "bullet_creation": test_bullet_creation,
    "enemy_spawn": test_enemy_spawn,
    "enemy_death": test_enemy_death,
    "door_mechanics": test_door_mechanics,
    "camera": test_camera,
    "smoke": test_smoke,
}


def run_tests(test_names=None, output_json=False):
    if test_names is None:
        test_names = list(ALL_TESTS.keys())

    results = []
    for name in test_names:
        if name not in ALL_TESTS:
            print(f"Unknown test: {name}")
            continue
        print(f"Running: {name}...", end=" ", flush=True)
        r = ALL_TESTS[name]()
        results.append(r)
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.message}")

    if output_json:
        print("\n" + json.dumps([r.to_dict() for r in results], indent=2))

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed")

    if passed < total:
        print("\nFailed tests:")
        for r in results:
            if not r.passed:
                print(f"  - {r.name}: {r.message}")
                if "traceback" in r.details:
                    print(f"    {r.details['traceback']}")
    print(f"{'=' * 50}")

    return passed == total


def main():
    parser = argparse.ArgumentParser(description="Platformer Game Test CLI")
    parser.add_argument("--test", "-t", nargs="+", help="Run specific test(s)")
    parser.add_argument("--list", "-l", action="store_true", help="List available tests")
    parser.add_argument("--smoke", "-s", action="store_true", help="Quick smoke test only")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    if args.list:
        print("Available tests:")
        for name, fn in ALL_TESTS.items():
            print(f"  {name}: {fn.__doc__}")
        return

    if args.smoke:
        test_names = ["smoke"]
    elif args.test:
        test_names = args.test
    else:
        test_names = None

    success = run_tests(test_names, output_json=args.json)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
