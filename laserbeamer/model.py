"""Deterministic, display-independent gameplay. Distances are world pixels, time seconds."""
from dataclasses import dataclass
import math
import random

from pygame import Vector2


def direction(angle):
    return Vector2(1, 0).rotate(-angle)


def segment_hits(start, end, center, radius):
    delta = end - start
    t = max(0, min(1, (center - start).dot(delta) / delta.length_squared())) if delta else 0
    return (start + delta * t).distance_squared_to(center) <= radius * radius


@dataclass
class Controls:
    turn: float = 0
    thrust: bool = False
    brake: bool = False
    boost: bool = False
    fire: bool = False


class Object:
    def __init__(self, position=(0, 0), angle=0):
        self.position = Vector2(position)
        self.angle = angle
        self.alive = True


class CollisionAble(Object):
    def __init__(self, position=(0, 0), angle=0, radius=16):
        super().__init__(position, angle)
        self.radius = radius

    def touches(self, other):
        return self.position.distance_squared_to(other.position) <= (self.radius + other.radius) ** 2


class Player(CollisionAble):
    max_health = 100

    def __init__(self):
        super().__init__(radius=17)
        self.health = self.max_health
        self.velocity = Vector2()
        self.invulnerable = 0
        self.cooldown = 0
        self.boost_cooldown = 0
        self.charge = 0
        self.charging = False

    def hurt(self, damage):
        if self.invulnerable > 0 or not self.alive:
            return False
        self.health = max(0, self.health - damage)
        self.invulnerable = 0.65
        self.alive = self.health > 0
        return True

    def update(self, dt, controls, world):
        self.invulnerable = max(0, self.invulnerable - dt)
        self.cooldown = max(0, self.cooldown - dt)
        self.boost_cooldown = max(0, self.boost_cooldown - dt)
        self.angle = (self.angle + controls.turn * 210 * dt) % 360
        if controls.thrust:
            self.velocity += direction(self.angle) * 560 * dt
        if controls.boost and self.boost_cooldown == 0:
            self.velocity += direction(self.angle) * 420
            self.boost_cooldown = 2.5
        self.velocity *= math.exp(-(5 if controls.brake else 1.7) * dt)
        if self.velocity.length() > 520:
            self.velocity.scale_to_length(520)
        self.position += self.velocity * dt

        if controls.fire and self.cooldown == 0:
            self.charging = True
            self.charge = min(1, self.charge + dt)
        if self.charging and (not controls.fire or self.charge >= 1 - 1e-9):
            charged = self.charge >= 0.95
            world.projectiles.append(PlayerLaser(self.position, self.angle, charged))
            self.cooldown = 1.25 if charged else 0.22
            self.charging = False
            self.charge = 0


class Projectile(CollisionAble):
    color = (255, 180, 95)

    def __init__(self, position, angle, speed, damage, radius=5, lifetime=5):
        super().__init__(position, angle, radius)
        self.previous = self.position.copy()
        self.velocity = direction(angle) * speed
        self.damage = damage
        self.lifetime = lifetime

    def update(self, dt, world):
        self.previous = self.position.copy()
        self.position += self.velocity * dt
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return
        player = world.player
        if segment_hits(self.previous, self.position, player.position, self.radius + player.radius):
            if player.hurt(self.damage):
                world.burst(player.position, (255, 90, 110))
            self.alive = False


class Bullets(Projectile):
    def __init__(self, position, angle):
        super().__init__(position, angle, 330, 14)


class Saw(Projectile):
    color = (255, 195, 95)

    def __init__(self, position, angle):
        super().__init__(position, angle, 210, 18, 12, 4)


class Acid(Projectile):
    color = (135, 245, 115)

    def __init__(self, position, angle):
        super().__init__(position, angle, 165, 10, 9, 6)


class PlayerLaser(Projectile):
    """A short-lived beam attached to the ship; each enemy takes damage once."""
    def __init__(self, position, angle, charged=False):
        super().__init__(position, angle, 0, 7 if charged else 2, 11 if charged else 4, 0.22)
        self.charged = charged
        self.length = 650 if charged else 440
        self.hit = set()
        self.end = self.position + direction(angle) * self.length

    def update(self, dt, world):
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.alive = False
            return
        self.angle = world.player.angle
        self.position = world.player.position + direction(self.angle) * 23
        self.end = self.position + direction(self.angle) * self.length
        for enemy in world.enemies:
            if enemy.alive and enemy not in self.hit and segment_hits(self.position, self.end, enemy.position, enemy.radius + self.radius):
                self.hit.add(enemy)
                enemy.health = max(0, enemy.health - self.damage)
                world.burst(enemy.position, enemy.color, 5)
                if enemy.health == 0:
                    enemy.alive = False
                    world.score += enemy.points
                    world.burst(enemy.position, enemy.color, 18)


class Enemy(CollisionAble):
    color = (255, 170, 80)
    points = 100
    health = 5
    speed = 85
    fire_interval = 2.8
    preferred_range = 0
    projectile_type = Saw

    def __init__(self, position, angle=0):
        super().__init__(position, angle, 21)
        self.health = type(self).health
        self.max_health = self.health
        self.fire_timer = 1.2

    def shoot(self, world):
        world.projectiles.append(self.projectile_type(self.position, self.angle))

    def update(self, dt, world):
        target = world.player.position - self.position
        distance = target.length()
        if distance:
            target_angle = -math.degrees(math.atan2(target.y, target.x))
            turn = (target_angle - self.angle + 180) % 360 - 180
            self.angle = (self.angle + max(-150 * dt, min(150 * dt, turn))) % 360
            movement = 1 if distance > self.preferred_range + 30 else (-0.65 if distance < self.preferred_range - 30 else 0)
            self.position += direction(self.angle) * self.speed * movement * dt
        self.fire_timer -= dt
        if self.fire_timer <= 0 and distance < 850:
            self.shoot(world)
            self.fire_timer = self.fire_interval
        if self.touches(world.player) and world.player.hurt(20):
            world.burst(world.player.position, (255, 90, 110))
            if distance:
                world.player.velocity += target.normalize() * 180


class Sawer(Enemy):
    pass


class Sniper(Enemy):
    color = (255, 105, 155)
    health = 4
    speed = 100
    points = 150
    fire_interval = 2.0
    preferred_range = 340
    projectile_type = Bullets


class Acider(Enemy):
    color = (135, 245, 115)
    health = 7
    speed = 65
    points = 200
    fire_interval = 3.2
    preferred_range = 230
    projectile_type = Acid

    def shoot(self, world):
        for spread in (-16, 0, 16):
            world.projectiles.append(Acid(self.position, self.angle + spread))


class Boss(Enemy):
    color = (195, 140, 255)
    health = 65
    speed = 60
    points = 1500
    fire_interval = 1.2
    preferred_range = 300

    def __init__(self, position, angle=0):
        super().__init__(position, angle)
        self.radius = 48
        self.attack = 0

    def shoot(self, world):
        self.attack += 1
        if self.attack % 3 == 0:
            for angle in range(0, 360, 30):
                world.projectiles.append(Saw(self.position, angle + self.angle))
        else:
            for spread in (-20, -10, 0, 10, 20):
                world.projectiles.append(Bullets(self.position, self.angle + spread))


@dataclass
class Particle:
    position: Vector2
    velocity: Vector2
    color: tuple
    lifetime: float = 0.5


class Menu(Object):
    """Menu selection belongs to the object hierarchy, independent of rendering."""
    def __init__(self):
        super().__init__()
        self.selected = 0

    def move(self, delta, count):
        self.selected = (self.selected + delta) % count


class World:
    final_wave = 10
    fixed_dt = 1 / 120

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.player = Player()
        self.enemies = []
        self.projectiles = []
        self.particles = []
        self.score = 0
        self.wave = 0
        self.time = 0
        self.wave_delay = 1.5
        self.state = "playing"
        self.accumulator = 0

    def burst(self, position, color, count=10):
        for _ in range(count):
            self.particles.append(Particle(Vector2(position), direction(self.rng.uniform(0, 360)) * self.rng.uniform(35, 170), color))
        self.particles = self.particles[-400:]

    def spawn_wave(self):
        self.wave += 1
        pool = [Sawer]
        if self.wave >= 2:
            pool.append(Sniper)
        if self.wave >= 3:
            pool.append(Acider)
        count = 2 + self.wave
        for i in range(count):
            angle = i * 360 / count + self.rng.uniform(-12, 12)
            position = self.player.position + direction(angle) * self.rng.uniform(620, 760)
            enemy = self.rng.choice(pool)(position, angle + 180)
            enemy.fire_timer += self.rng.uniform(0, 1)
            self.enemies.append(enemy)
        if self.wave % 5 == 0:
            boss = Boss(self.player.position + Vector2(740, 0), 180)
            boss.health = boss.max_health = 65 if self.wave == 5 else 100
            self.enemies.append(boss)

    def update(self, elapsed, controls=None):
        if self.state != "playing":
            return
        self.accumulator += max(0, min(elapsed, 0.25))
        while self.accumulator + 1e-10 >= self.fixed_dt and self.state == "playing":
            self.accumulator -= self.fixed_dt
            self.step(self.fixed_dt, controls or Controls())

    def step(self, dt, controls):
        self.time += dt
        self.player.update(dt, controls, self)
        for enemy in self.enemies:
            if enemy.alive:
                enemy.update(dt, self)
        for projectile in self.projectiles:
            if projectile.alive:
                projectile.update(dt, self)
        self.enemies[:] = [enemy for enemy in self.enemies if enemy.alive]
        self.projectiles[:] = [projectile for projectile in self.projectiles if projectile.alive]
        for particle in self.particles:
            particle.position += particle.velocity * dt
            particle.lifetime -= dt
        self.particles[:] = [particle for particle in self.particles if particle.lifetime > 0]
        if not self.player.alive:
            self.state = "game_over"
            self.player.charging = False
            return
        if not self.enemies:
            if self.wave == self.final_wave:
                self.state = "victory"
                return
            self.wave_delay -= dt
            if self.wave_delay <= 0:
                if self.wave:
                    self.player.health = min(self.player.max_health, self.player.health + 12)
                self.projectiles[:] = [p for p in self.projectiles if isinstance(p, PlayerLaser)]
                self.spawn_wave()
                self.wave_delay = 2.5

    def pause(self):
        if self.state == "playing":
            self.state = "paused"
            self.player.charging = False
            self.player.charge = 0

    def resume(self):
        if self.state == "paused":
            self.state = "playing"
