import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'

import tempfile
from pathlib import Path
import unittest

import pygame

from laserbeamer.model import (Acid, Acider, Boss, Bullets, Controls, PlayerLaser,
                               Saw, Sawer, Sniper, World)
from laserbeamer.app import Game, load_score, save_score


def advance(world, seconds, controls=None, fps=60):
    for _ in range(round(seconds * fps)):
        world.update(1 / fps, controls)


class GameplayTests(unittest.TestCase):
    def test_frame_rate_independent_movement_and_timers(self):
        worlds = [World(seed=1), World(seed=1), World(seed=1)]
        for world, fps in zip(worlds, (30, 60, 144)):
            advance(world, 1, Controls(thrust=True, turn=.2), fps)
        for world in worlds[1:]:
            self.assertLess(world.player.position.distance_to(worlds[0].player.position), 1e-6)
            self.assertAlmostEqual(world.time, worlds[0].time)

    def test_pause_freezes_all_state_and_cancels_charge(self):
        world = World()
        world.spawn_wave()
        advance(world, .2, Controls(fire=True))
        world.pause()
        snapshot = (world.time, world.player.position.copy(), world.enemies[0].fire_timer)
        advance(world, 5, Controls(thrust=True, fire=True))
        self.assertEqual(snapshot, (world.time, world.player.position, world.enemies[0].fire_timer))
        self.assertFalse(world.player.charging)
        world.resume()
        advance(world, .1)
        self.assertGreater(world.time, snapshot[0])

    def test_laser_hits_once_then_expires(self):
        world = World()
        enemy = Sawer((150, 0))
        world.enemies = [enemy]
        world.projectiles = [PlayerLaser((0, 0), 0)]
        advance(world, .1)
        self.assertEqual(enemy.health, 3)
        advance(world, .2)
        self.assertEqual(enemy.health, 3)
        self.assertEqual(world.projectiles, [])

    def test_charged_laser_pierces_and_scores_each_kill_once(self):
        world = World()
        world.enemies = [Sawer((100, 0)), Sniper((220, 0)), Acider((320, 0))]
        world.projectiles = [PlayerLaser((0, 0), 0, True)]
        advance(world, .1)
        self.assertEqual(world.enemies, [])
        self.assertEqual(world.score, 450)
        advance(world, .3)
        self.assertEqual(world.score, 450)

    def test_short_and_charged_fire(self):
        world = World()
        advance(world, .1, Controls(fire=True))
        advance(world, 1 / 60)
        self.assertEqual(len(world.projectiles), 1)
        self.assertFalse(world.projectiles[0].charged)
        advance(world, .4)
        advance(world, 1, Controls(fire=True))
        self.assertTrue(world.projectiles[0].charged)
        self.assertGreater(world.player.cooldown, 1)

    def test_projectile_sweeps_through_player(self):
        world = World()
        projectile = Bullets((-100, 0), 0)
        projectile.update(0.5, world)
        self.assertEqual(world.player.health, 86)
        self.assertFalse(projectile.alive)

    def test_damage_grace_period_and_game_over_at_zero(self):
        world = World()
        world.player.hurt(50)
        world.player.hurt(50)
        self.assertEqual(world.player.health, 50)
        advance(world, .7)
        world.player.hurt(50)
        advance(world, .1)
        self.assertEqual(world.player.health, 0)
        self.assertEqual(world.state, 'game_over')

    def test_projectiles_expire(self):
        world = World()
        world.projectiles = [cls((1000, 1000), 0) for cls in (Saw, Bullets, Acid)]
        world.wave_delay = 100
        advance(world, 7)
        self.assertEqual(world.projectiles, [])

    def test_enemy_weapon_types(self):
        for enemy_type, shot_type, count in ((Sawer, Saw, 1), (Sniper, Bullets, 1), (Acider, Acid, 3)):
            world = World()
            enemy_type((400, 0)).shoot(world)
            self.assertEqual(len(world.projectiles), count)
            self.assertTrue(all(isinstance(p, shot_type) for p in world.projectiles))
        boss = Boss((500, 0))
        world = World()
        for _ in range(3):
            boss.shoot(world)
        self.assertEqual(len(world.projectiles), 22)

    def test_wave_heals_and_final_wave_wins(self):
        world = World(seed=3)
        world.player.health = 60
        advance(world, 1.6)
        self.assertEqual(world.wave, 1)
        self.assertEqual(world.player.health, 60)
        world.enemies.clear()
        advance(world, 2.6)
        self.assertEqual(world.wave, 2)
        self.assertEqual(world.player.health, 72)
        world.enemies.clear()
        world.wave = 4
        world.spawn_wave()
        self.assertEqual(sum(isinstance(e, Boss) for e in world.enemies), 1)
        world.enemies.clear()
        world.wave = 10
        advance(world, .1)
        self.assertEqual(world.state, 'victory')

    def test_long_session_has_bounded_objects(self):
        world = World(seed=4)
        # Keep the player alive to exercise every enemy's firing/lifetime repeatedly.
        for _ in range(60 * 90):
            world.player.invulnerable = 1
            world.update(1 / 60, Controls(turn=.4, thrust=True, fire=True))
        self.assertLess(len(world.projectiles), 250)
        self.assertLessEqual(len(world.particles), 400)


class PresentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.game = Game(headless=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_render_all_states_and_enemies(self):
        game = self.game
        game.start()
        game.world.enemies = [cls((i * 100 - 200, -120)) for i, cls in enumerate((Sawer, Sniper, Acider, Boss))]
        for enemy in game.world.enemies:
            enemy.shoot(game.world)
        game.world.projectiles.append(PlayerLaser((0, 0), 0, True))
        for state in ('title', 'playing', 'paused', 'game_over', 'victory'):
            game.world.state = state
            game.draw()
        game.controls_help = True
        game.draw()
        game.controls_help = False
        game.confirm_restart = True
        game.draw()
        game.confirm_restart = False

    def test_restart_resets_game_and_keyboard_menu(self):
        game = self.game
        game.start()
        game.world.score = 20
        game.world.player.health = 1
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(game.world.state, 'paused')
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_KP_ENTER))
        self.assertTrue(game.confirm_restart)
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN))
        game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(game.world.state, 'playing')
        self.assertEqual(game.world.score, 0)
        self.assertEqual(game.world.player.health, 100)
        self.assertEqual(game.world.enemies, [])

    def test_focus_loss_and_resized_mouse_buttons(self):
        game = self.game
        game.start()
        game.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        self.assertEqual(game.world.state, 'paused')
        for width, height in ((440, 288), (800, 900), (1500, 500)):
            game.handle_event(pygame.event.Event(pygame.VIDEORESIZE, w=width, h=height))
            game.draw()
            point = game.buttons[0][0].center
            physical = (game.viewport.x + point[0] * game.viewport.w / 1100,
                        game.viewport.y + point[1] * game.viewport.h / 720)
            game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=physical, button=1))
            self.assertEqual(game.world.state, 'playing')
            game.world.pause()

    def test_score_handles_corrupt_data_and_roundtrips(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'record.json'
            self.assertEqual(load_score(path), 0)
            for text in ('bad json', 'null', '[]', '{"high_score": -1}', '{"high_score": true}'):
                path.write_text(text)
                self.assertEqual(load_score(path), 0)
            self.assertTrue(save_score(path, 1234))
            self.assertEqual(load_score(path), 1234)
            self.assertFalse(save_score(Path(folder), 2000))


if __name__ == '__main__':
    unittest.main()
