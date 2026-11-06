"""Nave del jugador, movimiento con colisión y proyectiles."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any

import pygame

import config


BULLET_WIDTH = 4
BULLET_HEIGHT = 12
BULLET_SPEED = 14
MAX_ACTIVE_BULLETS = 3
SHOT_COOLDOWN_FRAMES = 8
PLAYER_SPEED = 6.0
PLAYER_WIDTH = 32
PLAYER_HEIGHT = 24
SCREEN_CENTER_X = config.SCREEN_WIDTH / 2


class Bullet:
    """Proyectil vertical de 4×12 píxeles que viaja hacia la HUD."""

    def __init__(self, x: float, y: float) -> None:
        self.x = float(x)
        self.y = float(y)
        self.active = True

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - BULLET_WIDTH / 2),
            round(self.y),
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )

    def update(self) -> bool:
        self.y -= BULLET_SPEED
        self.active = self.y >= config.HUD_HEIGHT
        return self.active

    def draw(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        palette = config.obtener_paleta(estilo)
        rect = self.rect
        if config.normalizar_estilo(estilo) == config.ESTILO_RETRO:
            pygame.draw.rect(surface, palette["BALA"], rect)
        else:
            config.draw_soft_glow(surface, rect.center, palette["BALA"], 7, 60)
            pygame.draw.rect(surface, palette["BALA"], rect, border_radius=2)


@dataclass
class EngineParticle:
    x: float
    y: float
    vx: float
    vy: float
    life: int
    radius: int


class Player:
    """Controla la nave, sus vidas, el escudo de tótems y hasta tres balas."""

    def __init__(self) -> None:
        self.x = SCREEN_CENTER_X
        self.y = 540.0
        self.score = 0
        self.lives = 3
        self.totems = 0
        self.bullets: list[Bullet] = []
        self.shot_cooldown = 0
        self.invulnerability_frames = 0
        self.engine_particles: list[EngineParticle] = []
        self._engine_layer: pygame.Surface | None = None
        self._rng = random.Random()

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            round(self.x - PLAYER_WIDTH / 2),
            round(self.y - PLAYER_HEIGHT / 2),
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )

    @staticmethod
    def _is_pressed(keys: Any, key_code: int) -> bool:
        if keys is None:
            return False
        if hasattr(keys, "get"):
            return bool(keys.get(key_code, False))
        try:
            return bool(keys[key_code])
        except (IndexError, KeyError, TypeError):
            return False

    def _inside_play_area(self, rect: pygame.Rect) -> bool:
        return (
            rect.left >= 0
            and rect.right <= config.SCREEN_WIDTH
            and rect.top >= config.PLAYER_ZONE_TOP
            and rect.bottom <= config.PLAYER_ZONE_BOTTOM
        )

    def _can_occupy(self, rect: pygame.Rect, mushrooms: Any) -> bool:
        if not self._inside_play_area(rect):
            return False
        return mushrooms is None or not mushrooms.collides(rect)

    def update(self, keys: Any, mushrooms: Any) -> None:
        """Mueve la nave con WASD/flechas, normalizando la diagonal."""
        if self.shot_cooldown > 0:
            self.shot_cooldown -= 1
        if self.invulnerability_frames > 0:
            self.invulnerability_frames -= 1

        left = self._is_pressed(keys, pygame.K_LEFT) or self._is_pressed(keys, pygame.K_a)
        right = self._is_pressed(keys, pygame.K_RIGHT) or self._is_pressed(keys, pygame.K_d)
        up = self._is_pressed(keys, pygame.K_UP) or self._is_pressed(keys, pygame.K_w)
        down = self._is_pressed(keys, pygame.K_DOWN) or self._is_pressed(keys, pygame.K_s)
        move_x = float(right) - float(left)
        move_y = float(down) - float(up)

        if move_x or move_y:
            magnitude = math.hypot(move_x, move_y)
            delta_x = move_x * PLAYER_SPEED / magnitude
            delta_y = move_y * PLAYER_SPEED / magnitude

            old_x = self.x
            self.x += delta_x
            if not self._can_occupy(self.rect, mushrooms):
                self.x = old_x

            old_y = self.y
            self.y += delta_y
            if not self._can_occupy(self.rect, mushrooms):
                self.y = old_y

        self._update_engine_particles()

    def _update_engine_particles(self) -> None:
        nozzle_y = self.rect.bottom - 2
        if self._rng.random() < 0.8:
            self.engine_particles.append(
                EngineParticle(
                    x=self.x + self._rng.uniform(-3, 3),
                    y=nozzle_y,
                    vx=self._rng.uniform(-0.45, 0.45),
                    vy=self._rng.uniform(1.0, 2.3),
                    life=self._rng.randint(5, 10),
                    radius=self._rng.choice((1, 1, 2)),
                )
            )
        for particle in self.engine_particles:
            particle.x += particle.vx
            particle.y += particle.vy
            particle.life -= 1
        self.engine_particles = [p for p in self.engine_particles if p.life > 0]

    def shoot(self) -> Bullet | None:
        """Dispara si la cadencia lo permite y hay menos de tres balas activas."""
        if self.shot_cooldown > 0 or len(self.bullets) >= MAX_ACTIVE_BULLETS:
            return None
        bullet = Bullet(self.x, self.rect.top - BULLET_HEIGHT)
        self.bullets.append(bullet)
        self.shot_cooldown = SHOT_COOLDOWN_FRAMES
        return bullet

    def update_bullets(self) -> None:
        for bullet in self.bullets:
            bullet.update()
        self.bullets = [bullet for bullet in self.bullets if bullet.active]

    def reset_position(self) -> None:
        self.x = SCREEN_CENTER_X
        self.y = 540.0
        self.bullets.clear()
        self.engine_particles.clear()

    def draw(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)
        for bullet in self.bullets:
            bullet.draw(surface, style)

        if style == config.ESTILO_MODERNO:
            self._draw_engine(surface)

        # El parpadeo se activa durante los tres segundos de invulnerabilidad.
        if self.invulnerability_frames > 0 and (self.invulnerability_frames // 5) % 2 == 0:
            return

        rect = self.rect
        center_x = rect.centerx
        top_y = rect.top
        if style == config.ESTILO_RETRO:
            triangle = (
                (center_x, top_y),
                (rect.left + 1, rect.bottom - 1),
                (rect.right - 1, rect.bottom - 1),
            )
            pygame.draw.polygon(surface, (255, 255, 255), triangle)
            return

        points = (
            (center_x, top_y),
            (rect.left + 1, rect.bottom - 1),
            (center_x, rect.bottom - 6),
            (rect.right - 1, rect.bottom - 1),
        )
        config.draw_soft_glow(surface, (center_x, rect.centery), (0, 242, 254), 22, 42)
        pygame.draw.polygon(surface, palette["NAVE"], points)
        pygame.draw.polygon(surface, (220, 240, 255), points, 2)
        cockpit = [
            (center_x, top_y + 5),
            (center_x - 4, rect.bottom - 9),
            (center_x + 4, rect.bottom - 9),
        ]
        pygame.draw.polygon(surface, (0, 242, 254), cockpit)
        pygame.draw.line(surface, (255, 255, 255), (center_x, top_y + 1), (center_x, top_y + 8), 1)

    def _draw_engine(self, surface: pygame.Surface) -> None:
        if not self.engine_particles:
            return
        if self._engine_layer is None or self._engine_layer.get_size() != surface.get_size():
            self._engine_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self._engine_layer.fill((0, 0, 0, 0))
        for particle in self.engine_particles:
            alpha = max(0, min(180, particle.life * 20))
            color = (0, 180, 255, alpha)
            pygame.draw.circle(
                self._engine_layer,
                color,
                (round(particle.x), round(particle.y)),
                particle.radius,
            )
        surface.blit(self._engine_layer, (0, 0))

