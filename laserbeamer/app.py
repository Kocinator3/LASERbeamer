"""Pygame presentation and input. Importing this module does not open a window."""
import argparse
import json
import math
import os
from pathlib import Path
import random
import sys
import tempfile

import pygame

from .model import Acid, Boss, Controls, Menu, PlayerLaser, Saw, Sawer, World, direction

SIZE = (1100, 720)
BG = (8, 12, 24)
WHITE = (230, 239, 255)
MUTED = (135, 153, 183)
CYAN = (80, 226, 245)


def asset_path(name):
    if getattr(sys, "frozen", False):
        override = Path(sys.executable).parent / "assets" / name
        if override.is_file():
            return override
        return Path(sys._MEIPASS) / "assets" / name
    return Path(__file__).resolve().parent.parent / "assets" / name


def score_path():
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "LASERbeamer" / "score.json"


def load_score(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["high_score"]
        return value if type(value) is int and value >= 0 else 0
    except (OSError, ValueError, KeyError, TypeError):
        return 0


def save_score(path, score):
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix="score-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(json.dumps({"high_score": score}))
        temporary.replace(path)
        return True
    except OSError:
        return False
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


class Game:
    def __init__(self, *, headless=False):
        pygame.display.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode(SIZE, pygame.RESIZABLE)
        pygame.display.set_caption("LASERbeamer")
        self.canvas = pygame.Surface(SIZE)
        self.clock = pygame.time.Clock()
        self.fonts = {size: pygame.font.Font(str(asset_path("fonts/press_start.ttf")), size)
                      for size in (10, 12, 14, 18, 26, 44)}
        self.images = {}
        self.load_image("player", "ship/ship1/Spaceship.png", 54)
        for index in range(1, 6):
            self.load_image(f"forward{index}", f"ship/ship1/Forward{index}.png", 54)
        self.load_image("sawer", "enemies/sawer/sawer.png", 64)
        for index in range(12):
            self.load_image(f"saw{index}", f"enemies/sawer/saws/pixil-frame-{index}.png", 30)
        pygame.display.set_icon(self.images["player"])
        self.world = World()
        self.world.state = "title"
        self.menu = Menu()
        self.running = True
        self.debug = False
        self.fullscreen = False
        self.window_size = SIZE
        self.buttons = []
        self.confirm_restart = False
        self.controls_help = False
        self.headless = headless
        self.record_path = score_path()
        self.high_score = 0 if headless else load_score(self.record_path)
        self.save_failed = False
        rng = random.Random(42)
        self.stars = [(rng.randrange(SIZE[0]), rng.randrange(SIZE[1]), rng.uniform(.15, .7)) for _ in range(150)]
        self.viewport = pygame.Rect((0, 0), SIZE)

    def load_image(self, name, path, width):
        original = pygame.image.load(str(asset_path(path))).convert_alpha()
        height = max(1, round(original.get_height() * width / original.get_width()))
        self.images[name] = pygame.transform.scale(original, (width, height))

    def start(self):
        self.world = World()
        self.menu.selected = 0
        self.confirm_restart = False
        self.controls_help = False

    def record_score(self):
        if self.world.score > self.high_score:
            self.high_score = self.world.score
            if not self.headless:
                self.save_failed = not save_score(self.record_path, self.high_score)

    def choices(self):
        if self.controls_help:
            return [("ZPET", "help_back")]
        if self.confirm_restart:
            return [("NE, POKRACOVAT", "cancel"), ("ANO, NOVA HRA", "start")]
        if self.world.state == "title":
            return [("NOVA HRA", "start"), ("OVLADANI", "help"), ("UKONCIT", "quit")]
        if self.world.state == "paused":
            return [("POKRACOVAT", "resume"), ("NOVA HRA", "confirm"), ("OVLADANI", "help"), ("UKONCIT", "quit")]
        return [("HRAT ZNOVU", "start"), ("HLAVNI MENU", "title"), ("UKONCIT", "quit")]

    def activate(self, action):
        if action == "start":
            self.record_score()
            self.start()
        elif action == "resume":
            self.world.resume()
        elif action == "confirm":
            self.confirm_restart = True
        elif action == "cancel":
            self.confirm_restart = False
        elif action == "help":
            self.controls_help = True
        elif action == "help_back":
            self.controls_help = False
        elif action == "title":
            self.record_score()
            self.world.state = "title"
        elif action == "quit":
            self.record_score()
            self.running = False
        self.menu.selected = 0
        self.buttons = []

    def logical_mouse(self, point):
        if not self.viewport.collidepoint(point):
            return None
        return ((point[0] - self.viewport.x) * SIZE[0] / self.viewport.w,
                (point[1] - self.viewport.y) * SIZE[1] / self.viewport.h)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.activate("quit")
        elif event.type == pygame.WINDOWFOCUSLOST:
            self.world.pause()
        elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
            self.window_size = (max(440, event.w), max(288, event.h))
            self.screen = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:
                self.fullscreen = not self.fullscreen
                self.screen = pygame.display.set_mode((0, 0) if self.fullscreen else self.window_size,
                                                       pygame.FULLSCREEN if self.fullscreen else pygame.RESIZABLE)
            elif event.key == pygame.K_F3:
                self.debug = not self.debug
            elif event.key == pygame.K_ESCAPE:
                if self.controls_help:
                    self.activate("help_back")
                elif self.confirm_restart:
                    self.activate("cancel")
                elif self.world.state == "playing":
                    self.world.pause()
                    self.menu.selected = 0
                elif self.world.state == "paused":
                    self.world.resume()
            elif self.world.state != "playing":
                choices = self.choices()
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.menu.move(-1, len(choices))
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.menu.move(1, len(choices))
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self.activate(choices[self.menu.selected][1])
        elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN) and self.world.state != "playing":
            point = self.logical_mouse(event.pos)
            if point:
                for i, (rect, action) in enumerate(self.buttons):
                    if rect.collidepoint(point):
                        self.menu.selected = i
                        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                            self.activate(action)
                        break

    def controls(self):
        keys = pygame.key.get_pressed()
        return Controls(turn=int(keys[pygame.K_a] or keys[pygame.K_LEFT]) - int(keys[pygame.K_d] or keys[pygame.K_RIGHT]),
                        thrust=keys[pygame.K_w] or keys[pygame.K_UP],
                        brake=keys[pygame.K_s] or keys[pygame.K_DOWN],
                        boost=keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] or keys[pygame.K_b],
                        fire=keys[pygame.K_SPACE])

    def text(self, label, position, size=14, color=WHITE, center=False):
        surface = self.fonts[size].render(label, True, color)
        rect = surface.get_rect(center=position) if center else surface.get_rect(topleft=position)
        self.canvas.blit(surface, rect)
        return rect

    def screen_position(self, position):
        return position - self.world.player.position + pygame.Vector2(SIZE) / 2

    def sprite(self, key, position, angle):
        image = pygame.transform.rotate(self.images[key], angle)
        self.canvas.blit(image, image.get_rect(center=position))

    def draw_world(self):
        world = self.world
        self.canvas.fill(BG)
        for x, y, depth in self.stars:
            point = ((x - world.player.position.x * depth) % SIZE[0],
                     (y - world.player.position.y * depth) % SIZE[1])
            pygame.draw.circle(self.canvas, (int(100 + depth * 140),) * 3, point, 1 if depth < .5 else 2)
        for enemy in world.enemies:
            point = self.screen_position(enemy.position)
            if not self.canvas.get_rect().inflate(150, 150).collidepoint(point):
                offset = point - pygame.Vector2(SIZE) / 2
                scale = min((SIZE[0] / 2 - 30) / max(abs(offset.x), .01),
                            (SIZE[1] / 2 - 95) / max(abs(offset.y), .01))
                marker = pygame.Vector2(SIZE) / 2 + offset * scale
                pygame.draw.circle(self.canvas, enemy.color, marker, 5)
                continue
            if isinstance(enemy, Sawer):
                self.sprite("sawer", point, enemy.angle)
                self.sprite(f"saw{int(world.time * 15) % 12}", point + direction(enemy.angle) * 23, enemy.angle)
            else:
                radius = enemy.radius
                vertices = [(point + direction(enemy.angle + a) * r) for a, r in
                            ((0, radius * 1.3), (130, radius), (180, radius * .55), (230, radius))]
                pygame.draw.polygon(self.canvas, (24, 30, 48), vertices)
                pygame.draw.polygon(self.canvas, enemy.color, vertices, 3)
                pygame.draw.circle(self.canvas, enemy.color, point, 6 if not isinstance(enemy, Boss) else 14, 2)
            if enemy.health < enemy.max_health:
                rect = pygame.Rect(point.x - 22, point.y - enemy.radius - 12, 44, 4)
                pygame.draw.rect(self.canvas, (45, 50, 70), rect)
                pygame.draw.rect(self.canvas, enemy.color, (rect.x, rect.y, rect.w * enemy.health / enemy.max_health, 4))
            if self.debug:
                pygame.draw.circle(self.canvas, CYAN, point, enemy.radius, 1)
        for projectile in world.projectiles:
            point = self.screen_position(projectile.position)
            if isinstance(projectile, PlayerLaser):
                end = self.screen_position(projectile.end)
                color = CYAN if projectile.charged else (255, 90, 115)
                pygame.draw.line(self.canvas, color, point, end, projectile.radius * 2)
                pygame.draw.line(self.canvas, WHITE, point, end, max(2, projectile.radius // 2))
            elif isinstance(projectile, Saw):
                self.sprite(f"saw{int(world.time * 18) % 12}", point, projectile.angle)
            else:
                pygame.draw.circle(self.canvas, projectile.color, point, projectile.radius)
                pygame.draw.circle(self.canvas, WHITE, point, 2)
        center = pygame.Vector2(SIZE) / 2
        player = world.player
        key = f"forward{int(world.time * 12) % 5 + 1}" if player.velocity.length() > 50 else "player"
        if player.invulnerable == 0 or int(world.time * 20) % 2:
            self.sprite(key, center, player.angle)
        if player.charging:
            pygame.draw.circle(self.canvas, CYAN, center, 32 + int(player.charge * 12), 2)
        if self.debug:
            pygame.draw.circle(self.canvas, CYAN, center, player.radius, 1)
        for particle in world.particles:
            pygame.draw.circle(self.canvas, particle.color, self.screen_position(particle.position), max(1, round(particle.lifetime * 6)))
        if world.state == "playing":
            self.draw_hud()

    def draw_hud(self):
        world = self.world
        pygame.draw.rect(self.canvas, (13, 20, 36), (0, 0, SIZE[0], 64))
        self.text("LASER", (24, 17), 26)
        self.text("BEAMER", (166, 29), 12, CYAN)
        self.text(f"VLNA {world.wave:02d} / 10", (390, 26), 14)
        self.text(f"SKORE {world.score:06d}", (730, 26), 14, CYAN)
        pygame.draw.rect(self.canvas, (13, 20, 36), (0, 650, SIZE[0], 70))
        self.text("STIT", (24, 669), 12, MUTED)
        pygame.draw.rect(self.canvas, (45, 50, 70), (94, 668, 190, 14), border_radius=4)
        pygame.draw.rect(self.canvas, CYAN if world.player.health > 25 else (255, 90, 115),
                         (94, 668, 190 * world.player.health / 100, 14), border_radius=4)
        self.text(str(world.player.health), (298, 669), 12)
        ready = "PRIPRAVEN" if world.player.cooldown == 0 else f"{world.player.cooldown:.1f}s"
        self.text("LASER " + (f"{int(world.player.charge * 100)}%" if world.player.charging else ready), (390, 669), 12, CYAN)
        self.text("BOOST " + ("OK" if world.player.boost_cooldown == 0 else f"{world.player.boost_cooldown:.1f}s"), (720, 669), 12)
        self.text("ESC PAUZA", (926, 669), 12, MUTED)
        if not world.enemies and world.state == "playing":
            self.text(f"VLNA {world.wave + 1} ZA {max(1, math.ceil(world.wave_delay))}", (550, 155), 18, CYAN, True)
        boss = next((e for e in world.enemies if isinstance(e, Boss)), None)
        if boss:
            self.text("BOSS", (550, 90), 12, boss.color, True)
            pygame.draw.rect(self.canvas, (45, 50, 70), (350, 108, 400, 7))
            pygame.draw.rect(self.canvas, boss.color, (350, 108, 400 * boss.health / boss.max_health, 7))
        if self.debug:
            self.text(f"FPS {int(self.clock.get_fps())}  ENEMIES {len(world.enemies)}  SHOTS {len(world.projectiles)}", (24, 620), 10, MUTED)

    def draw_menu(self):
        shade = pygame.Surface(SIZE, pygame.SRCALPHA)
        shade.fill((4, 8, 18, 225))
        self.canvas.blit(shade, (0, 0))
        titles = {"title": "LASERBEAMER", "paused": "PAUZA", "game_over": "GAME OVER", "victory": "VITEZSTVI"}
        title = "OVLADANI" if self.controls_help else ("NOVA HRA?" if self.confirm_restart else titles[self.world.state])
        self.text("// SECTOR 10 - SURVIVAL CAMPAIGN", (550, 124), 12, CYAN, True)
        self.text(title, (550, 195), 44, WHITE, True)
        if self.controls_help:
            lines = ["W / SIPKA NAHORU   POHYB VPRED", "A D / SIPKY        OTACENI", "S / SIPKA DOLU     BRZDA", "SHIFT / B          BOOST",
                     "MEZERNIK           PUST = LASER", "DRZ MEZERNIK 1s    NABITY LASER", "ESC PAUZA   F11 FULLSCREEN   F3 DEBUG"]
            for index, line in enumerate(lines):
                self.text(line, (550, 270 + index * 30), 12, MUTED, True)
            top = 520
        else:
            subtitle = "PREZIJ 10 VLN. ZNIC OBA BOSSY." if self.world.state == "title" else f"SKORE {self.world.score:06d}   REKORD {max(self.high_score, self.world.score):06d}"
            if self.confirm_restart:
                subtitle = "Aktualni rozehrana hra bude ukoncena."
            self.text(subtitle, (550, 260), 14, MUTED, True)
            top = 316
        self.buttons = []
        for index, (label, action) in enumerate(self.choices()):
            rect = pygame.Rect(330, top + index * 58, 440, 46)
            selected = index == self.menu.selected
            pygame.draw.rect(self.canvas, (23, 52, 68) if selected else (17, 25, 43), rect, border_radius=8)
            pygame.draw.rect(self.canvas, CYAN if selected else (45, 58, 78), rect, 2, border_radius=8)
            self.text(label, rect.center, 18, CYAN if selected else WHITE, True)
            self.buttons.append((rect, action))
        self.text("SIPKY + ENTER / MYS", (550, 615), 10, MUTED, True)
        self.text("W POHYB   A/D OTACENI   MEZERNIK LASER   SHIFT BOOST", (550, 670), 10, MUTED, True)
        if self.save_failed:
            self.text("REKORD SE NEPODARILO ULOZIT", (550, 695), 10, (255, 120, 120), True)

    def draw(self):
        self.draw_world()
        if self.world.state != "playing":
            self.draw_menu()
        width, height = self.screen.get_size()
        scale = min(width / SIZE[0], height / SIZE[1])
        target = (max(1, round(SIZE[0] * scale)), max(1, round(SIZE[1] * scale)))
        self.viewport = pygame.Rect((0, 0), target)
        self.viewport.center = (width // 2, height // 2)
        self.screen.fill((0, 0, 0))
        self.screen.blit(pygame.transform.scale(self.canvas, target), self.viewport)
        pygame.display.flip()

    def run(self, max_frames=None):
        frames = 0
        try:
            while self.running:
                elapsed = self.clock.tick(60) / 1000
                for event in pygame.event.get():
                    self.handle_event(event)
                if not self.running:
                    break
                before = self.world.state
                self.world.update(elapsed, self.controls())
                if before == "playing" and self.world.state in ("game_over", "victory"):
                    self.record_score()
                    self.menu.selected = 0
                self.draw()
                frames += 1
                if max_frames is not None and frames >= max_frames:
                    break
        finally:
            pygame.quit()


def main():
    parser = argparse.ArgumentParser(description="LASERbeamer - Pygame space survival")
    parser.add_argument("--smoke-test", action="store_true", help="Render 10 gameplay frames without a real display or saving data")
    args = parser.parse_args()
    if args.smoke_test:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    game = Game(headless=args.smoke_test)
    if args.smoke_test:
        game.start()
        game.world.spawn_wave()
    game.run(max_frames=10 if args.smoke_test else None)
