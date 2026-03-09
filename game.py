#!/usr/bin/env python3
"""Platformer Game - Level 1"""

import os
import sys
import random
import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TILE = 64
SCREEN_W, SCREEN_H = 3440, 1440
FPS = 60
GRAVITY = 0.7
PLAYER_SPEED = 5
JUMP_FORCE = -14
BULLET_SPEED = 12
ENEMY_SPEED = 2
NUM_ENEMIES = 10

ASSETS = os.path.join(os.path.dirname(__file__), "assets", "Sprites")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_img(path, scale=None):
    img = pygame.image.load(os.path.join(ASSETS, path)).convert_alpha()
    if scale:
        img = pygame.transform.scale(img, scale)
    return img


def tile_background(surface, bg_img):
    bw, bh = bg_img.get_size()
    for x in range(0, surface.get_width(), bw):
        for y in range(0, surface.get_height(), bh):
            surface.blit(bg_img, (x, y))


# ---------------------------------------------------------------------------
# Level definition  (tile‑map, row by row)
# ---------------------------------------------------------------------------
# Legend:
#   . = empty
#   G = grass top
#   D = dirt/fill
#   S = door bottom (exit)
#   T = door top
#   P = player spawn
#   E = floating platform (grass top)

LEVEL_1 = [
    #  0         1         2         3         4         5         6         7         8
    #  0123456789012345678901234567890123456789012345678901234567890123456789012345678901
    "..................................................................................",  # row 0
    "..................................................................................",  # row 1
    "..................................................................................",  # row 2
    "..................................................................................",  # row 3
    "..................................................................................",  # row 4
    "..................................................................................",  # row 5
    "..................................................................................",  # row 6
    "..................................................................................",  # row 7
    "..................................................................................",  # row 8
    "..................................................................................",  # row 9
    "..................................................................................",  # row 10
    "..................................................................................",  # row 11
    "..................................................................................",  # row 12
    "..................................................................................",  # row 13
    "...EEEE.......EEEE.......EEEE....GGGGG.....EEEE.......EEEE.......EEEE....GGGGG..",  # row 14
    "..................................................................................",  # row 15
    "........EEEE.......EEEE.......EEEE..........EEEE.......EEEE.......EEEE...........",  # row 16
    "..................................................................................",  # row 17
    "...EEEE.......EEEE.......EEEE..........EEEE.......EEEE.......EEEE................",  # row 18
    "P...............................................................................T.",  # row 19
    "................................................................................S.",  # row 20
    "GGGGGGGGGG..GGGGGGGGG..GGGGGGGGGGGGGGGGGGGGGGGGGGG..GGGGGGGGG..GGGGGGGGGGGGGGGGGG",  # row 21
    "DDDDDDDDDD..DDDDDDDDD..DDDDDDDDDDDDDDDDDDDDDDDDD..DDDDDDDDD..DDDDDDDDDDDDDDDD",  # row 22
]

LEVEL_W = max(len(row) for row in LEVEL_1) * TILE
LEVEL_H = len(LEVEL_1) * TILE


# ---------------------------------------------------------------------------
# Sprite Classes
# ---------------------------------------------------------------------------

class Camera:
    def __init__(self, level_w, level_h):
        self.offset_x = 0
        self.offset_y = 0
        self.level_w = level_w
        self.level_h = level_h

    def update(self, target_rect):
        self.offset_x = target_rect.centerx - SCREEN_W // 2
        self.offset_y = target_rect.centery - SCREEN_H // 2
        self.offset_x = max(0, min(self.offset_x, self.level_w - SCREEN_W))
        self.offset_y = max(0, min(self.offset_y, self.level_h - SCREEN_H))

    def apply(self, rect):
        return rect.move(-self.offset_x, -self.offset_y)


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.sprites_idle = [load_img("Characters/Default/character_yellow_idle.png", (TILE, TILE))]
        self.sprites_walk = [
            load_img("Characters/Default/character_yellow_walk_a.png", (TILE, TILE)),
            load_img("Characters/Default/character_yellow_walk_b.png", (TILE, TILE)),
        ]
        self.sprite_jump = load_img("Characters/Default/character_yellow_jump.png", (TILE, TILE))
        self.sprite_hit = load_img("Characters/Default/character_yellow_hit.png", (TILE, TILE))

        self.image = self.sprites_idle[0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.facing_right = True
        self.anim_index = 0
        self.anim_timer = 0
        self.alive = True
        self.hit_timer = 0
        self.health = 3
        self.jumps_left = 2
        self.jump_pressed = False

    def take_hit(self):
        if self.hit_timer <= 0:
            self.health -= 1
            self.hit_timer = 60  # invincibility frames
            if self.health <= 0:
                self.alive = False

    def update(self, platforms):
        if not self.alive:
            return

        if self.hit_timer > 0:
            self.hit_timer -= 1

        keys = pygame.key.get_pressed()
        self.vel_x = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        jump_key = keys[pygame.K_UP] or keys[pygame.K_w]
        if jump_key and not self.jump_pressed and self.jumps_left > 0:
            self.vel_y = JUMP_FORCE
            self.on_ground = False
            self.jumps_left -= 1
        self.jump_pressed = jump_key

        # gravity
        self.vel_y += GRAVITY
        if self.vel_y > 18:
            self.vel_y = 18

        # horizontal movement + collision
        self.rect.x += self.vel_x
        self._collide_x(platforms)
        # clamp to level bounds
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > LEVEL_W:
            self.rect.right = LEVEL_W

        # vertical movement + collision
        self.rect.y += self.vel_y
        self._collide_y(platforms)

        # fell off bottom of map
        if self.rect.top > LEVEL_H + 200:
            self.alive = False

        # animation
        self._animate()

    def _collide_x(self, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right

    def _collide_y(self, platforms):
        self.on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_y > 0:
                    self.rect.bottom = p.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                    self.jumps_left = 2
                elif self.vel_y < 0:
                    self.rect.top = p.rect.bottom
                    self.vel_y = 0

    def _animate(self):
        if not self.on_ground:
            img = self.sprite_jump
        elif self.vel_x != 0:
            self.anim_timer += 1
            if self.anim_timer >= 8:
                self.anim_timer = 0
                self.anim_index = (self.anim_index + 1) % len(self.sprites_walk)
            img = self.sprites_walk[self.anim_index]
        else:
            img = self.sprites_idle[0]

        if self.hit_timer > 0:
            img = self.sprite_hit

        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        self.image = img


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        super().__init__()
        self.image = pygame.Surface((20, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image, (255, 30, 30), (0, 0, 20, 10))
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = BULLET_SPEED * direction
        self.lifetime = 90

    def update(self):
        self.rect.x += self.speed
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.sprites_walk = [
            load_img("Enemies/Default/slime_normal_walk_a.png"),
            load_img("Enemies/Default/slime_normal_walk_b.png"),
        ]
        self.sprite_flat = load_img("Enemies/Default/slime_normal_flat.png")
        self.image = self.sprites_walk[0]
        self.rect = self.image.get_rect(topleft=(x, y))
        self.vel_x = ENEMY_SPEED
        self.anim_index = 0
        self.anim_timer = 0
        self.alive = True
        self.death_timer = 0

    def update(self, platforms, spawn_safe_x=0):
        if not self.alive:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.kill()
            return

        # turn around at player spawn safe zone
        if self.rect.left < spawn_safe_x and self.vel_x < 0:
            self.rect.left = spawn_safe_x
            self.vel_x = ENEMY_SPEED

        # move
        self.rect.x += self.vel_x

        # collision with platforms (turn around)
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.vel_x > 0:
                    self.rect.right = p.rect.left
                    self.vel_x = -ENEMY_SPEED
                elif self.vel_x < 0:
                    self.rect.left = p.rect.right
                    self.vel_x = ENEMY_SPEED

        # apply gravity
        self.rect.y += 4
        on_ground = False
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if self.rect.bottom > p.rect.top:
                    self.rect.bottom = p.rect.top
                    on_ground = True

        # edge detection - turn around near platform edges
        if on_ground:
            # check if there's ground ahead
            test_x = self.rect.centerx + (TILE if self.vel_x > 0 else -TILE)
            ground_ahead = False
            for p in platforms:
                if p.rect.left <= test_x <= p.rect.right and p.rect.top == self.rect.bottom:
                    ground_ahead = True
                    break
            if not ground_ahead:
                self.vel_x = -self.vel_x

        # animate
        self.anim_timer += 1
        if self.anim_timer >= 10:
            self.anim_timer = 0
            self.anim_index = (self.anim_index + 1) % len(self.sprites_walk)
        img = self.sprites_walk[self.anim_index]
        if self.vel_x < 0:
            img = pygame.transform.flip(img, True, False)
        self.image = img

    def die(self):
        self.alive = False
        self.image = self.sprite_flat
        self.death_timer = 30


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y, img):
        super().__init__()
        self.image = img
        self.rect = self.image.get_rect(topleft=(x, y))


class Door:
    def __init__(self, x, y):
        self.closed_top = load_img("Tiles/Default/door_closed_top.png")
        self.closed_bot = load_img("Tiles/Default/door_closed.png")
        self.open_top = load_img("Tiles/Default/door_open_top.png")
        self.open_bot = load_img("Tiles/Default/door_open.png")
        self.rect_top = self.closed_top.get_rect(topleft=(x, y))
        self.rect_bot = self.closed_bot.get_rect(topleft=(x, y + TILE))
        self.rect = pygame.Rect(x, y, TILE, TILE * 2)
        self.opened = False

    def draw(self, surface, camera):
        if self.opened:
            surface.blit(self.open_top, camera.apply(self.rect_top))
            surface.blit(self.open_bot, camera.apply(self.rect_bot))
        else:
            surface.blit(self.closed_top, camera.apply(self.rect_top))
            surface.blit(self.closed_bot, camera.apply(self.rect_bot))


# ---------------------------------------------------------------------------
# Build Level
# ---------------------------------------------------------------------------

def build_level(level_data):
    platforms = pygame.sprite.Group()
    player_pos = (0, 0)
    door = None
    enemy_zones = []  # valid positions for enemy spawning

    grass_top = load_img("Tiles/Default/terrain_grass_block_top.png")
    dirt_fill = load_img("Tiles/Default/terrain_grass_block.png")

    for row_i, row in enumerate(level_data):
        for col_i, ch in enumerate(row):
            x, y = col_i * TILE, row_i * TILE
            if ch == "G" or ch == "E":
                platforms.add(Tile(x, y, grass_top))
            elif ch == "D":
                platforms.add(Tile(x, y, dirt_fill))
            elif ch == "P":
                player_pos = (x, y)
            elif ch == "T":
                door = Door(x, y)  # door top placed here; bottom is next row
            elif ch == "S":
                pass  # door bottom handled by Door class

    # Determine enemy spawn zones: on top of platform tiles
    for p in platforms:
        # enemy spawns on top of each platform tile
        spawn_x = p.rect.x
        spawn_y = p.rect.y - TILE  # on top of platform
        # don't spawn on player start or door area
        if door and abs(spawn_x - door.rect.x) < TILE * 2:
            continue
        if abs(spawn_x - player_pos[0]) < TILE * 5:
            continue
        enemy_zones.append((spawn_x, spawn_y))

    return platforms, player_pos, door, enemy_zones


def spawn_enemies(enemy_zones, count):
    enemies = pygame.sprite.Group()
    if not enemy_zones:
        return enemies
    positions = random.sample(enemy_zones, min(count, len(enemy_zones)))
    for x, y in positions:
        enemies.add(Enemy(x, y))
    return enemies


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------

def draw_hud(surface, player, enemies_left):
    font = pygame.font.SysFont("Arial", 24)
    # health
    hp_text = font.render(f"HP: {'<3 ' * player.health}", True, (255, 255, 255))
    surface.blit(hp_text, (10, 10))
    # enemies remaining
    en_text = font.render(f"Enemies: {enemies_left}", True, (255, 255, 255))
    surface.blit(en_text, (10, 40))


# ---------------------------------------------------------------------------
# Main Game
# ---------------------------------------------------------------------------

def run_game(headless=False, max_frames=0, test_callback=None):
    """
    Run the game.
    headless: if True, use dummy video driver (no window)
    max_frames: if >0, quit after this many frames
    test_callback: called each frame with game state dict
    """
    if headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"

    pygame.init()

    if headless:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    else:
        screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("Platformer - Level 1")

    clock = pygame.time.Clock()
    bg_color = (255, 255, 240)  # very light yellow

    # Build level
    platforms, player_pos, door, enemy_zones = build_level(LEVEL_1)
    player = Player(player_pos[0], player_pos[1])
    enemies = spawn_enemies(enemy_zones, NUM_ENEMIES)
    bullets = pygame.sprite.Group()
    spawn_safe_x = player_pos[0] + TILE * 5
    camera = Camera(LEVEL_W, LEVEL_H)

    shoot_cooldown = 0
    frame_count = 0
    game_state = "playing"  # playing, won, dead

    running = True
    while running:
        dt = clock.tick(FPS)
        frame_count += 1

        if max_frames > 0 and frame_count > max_frames:
            running = False
            break

        # Events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r and game_state != "playing":
                    # restart
                    platforms, player_pos, door, enemy_zones = build_level(LEVEL_1)
                    player = Player(player_pos[0], player_pos[1])
                    enemies = spawn_enemies(enemy_zones, NUM_ENEMIES)
                    spawn_safe_x = player_pos[0] + TILE * 5
                    bullets = pygame.sprite.Group()
                    shoot_cooldown = 0
                    game_state = "playing"

        keys = pygame.key.get_pressed()

        # Shooting
        if keys[pygame.K_SPACE] and shoot_cooldown <= 0 and game_state == "playing" and player.alive:
            direction = 1 if player.facing_right else -1
            bx = player.rect.right if direction == 1 else player.rect.left
            by = player.rect.centery
            bullets.add(Bullet(bx, by, direction))
            shoot_cooldown = 15

        if shoot_cooldown > 0:
            shoot_cooldown -= 1

        if game_state == "playing":
            # Update player
            player.update(platforms)

            # Update enemies
            for e in enemies:
                e.update(platforms, spawn_safe_x)

            # Update bullets
            for b in list(bullets):
                b.update()
                # check bullet hits enemy
                for e in enemies:
                    if e.alive and b.rect.colliderect(e.rect):
                        e.die()
                        b.kill()
                        break
                # check bullet hits platform
                for p in platforms:
                    if b.rect.colliderect(p.rect):
                        b.kill()
                        break

            # Player-enemy collision
            for e in enemies:
                if e.alive and player.rect.colliderect(e.rect) and player.hit_timer <= 0:
                    # check if stomping (player falling on top)
                    if player.vel_y > 0 and player.rect.bottom < e.rect.centery:
                        e.die()
                        player.vel_y = JUMP_FORCE * 0.6
                    else:
                        player.take_hit()

            # Check door
            if door:
                enemies_alive = sum(1 for e in enemies if e.alive)
                if enemies_alive == 0:
                    door.opened = True
                if door.opened and player.rect.colliderect(door.rect):
                    game_state = "won"

            if not player.alive:
                game_state = "dead"

        # Draw
        screen.fill(bg_color)

        # platforms
        for p in platforms:
            screen.blit(p.image, camera.apply(p.rect))

        # door
        if door:
            door.draw(screen, camera)

        # enemies
        for e in enemies:
            screen.blit(e.image, camera.apply(e.rect))

        # bullets
        for b in bullets:
            screen.blit(b.image, camera.apply(b.rect))

        # player (blink when hit)
        if player.alive and not (player.hit_timer > 0 and player.hit_timer % 4 < 2):
            screen.blit(player.image, camera.apply(player.rect))

        camera.update(player.rect)

        # HUD
        enemies_alive = sum(1 for e in enemies if e.alive)
        draw_hud(screen, player, enemies_alive)

        if game_state == "won":
            font = pygame.font.SysFont("Arial", 64)
            text = font.render("LEVEL COMPLETE!", True, (255, 255, 0))
            rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            screen.blit(text, rect)
            sub_font = pygame.font.SysFont("Arial", 28)
            sub_pos = (SCREEN_W // 2, SCREEN_H // 2 + 50)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    outline = sub_font.render("Press R to restart or ESC to quit", True, (0, 0, 0))
                    screen.blit(outline, outline.get_rect(center=(sub_pos[0] + dx, sub_pos[1] + dy)))
            sub = sub_font.render("Press R to restart or ESC to quit", True, (255, 255, 255))
            screen.blit(sub, sub.get_rect(center=sub_pos))

        elif game_state == "dead":
            font = pygame.font.SysFont("Arial", 64)
            text = font.render("GAME OVER", True, (255, 0, 0))
            rect = text.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2))
            screen.blit(text, rect)
            sub_font = pygame.font.SysFont("Arial", 28)
            sub_pos = (SCREEN_W // 2, SCREEN_H // 2 + 50)
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    outline = sub_font.render("Press R to restart or ESC to quit", True, (0, 0, 0))
                    screen.blit(outline, outline.get_rect(center=(sub_pos[0] + dx, sub_pos[1] + dy)))
            sub = sub_font.render("Press R to restart or ESC to quit", True, (255, 255, 255))
            screen.blit(sub, sub.get_rect(center=sub_pos))

        pygame.display.flip()

        # Test callback
        if test_callback:
            state = {
                "frame": frame_count,
                "game_state": game_state,
                "player_x": player.rect.x,
                "player_y": player.rect.y,
                "player_alive": player.alive,
                "player_health": player.health,
                "player_on_ground": player.on_ground,
                "enemies_alive": sum(1 for e in enemies if e.alive),
                "enemies_total": len(enemies.sprites()),
                "bullets_count": len(bullets.sprites()),
                "door_opened": door.opened if door else False,
                "player_vel_y": player.vel_y,
            }
            result = test_callback(state)
            if result == "quit":
                running = False

    pygame.quit()
    return game_state


if __name__ == "__main__":
    run_game()
