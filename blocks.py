"""Campo de hongos destructibles y esporas ambientales."""

from __future__ import annotations

from dataclasses import dataclass
import random

import pygame

import config


@dataclass
class Mushroom:
    """Hongo en una celda física de pantalla con tres impactos de durabilidad."""

    grid_x: int
    grid_y: int
    health: int = 3

    def __post_init__(self) -> None:
        self.grid_x = int(self.grid_x)
        self.grid_y = int(self.grid_y)
        self.health = max(1, min(3, int(self.health)))

    @property
    def rect(self) -> pygame.Rect:
        return config.grid_to_screen_rect(self.grid_x, self.grid_y)


@dataclass
class Spore:
    x: float
    y: float
    speed: float
    radius: int
    alpha: int


class MushroomField:
    """Administra hongos, colisiones y quince esporas para el estilo moderno."""

    def __init__(self, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.Random()
        self.mushrooms: list[Mushroom] = []
        self.spores = [self._new_spore() for _ in range(15)]
        self._spores_layer: pygame.Surface | None = None
        self.generate_field()

    def _new_spore(self, x: float | None = None, y: float | None = None) -> Spore:
        return Spore(
            x=self.rng.uniform(0, config.SCREEN_WIDTH) if x is None else x,
            y=self.rng.uniform(config.HUD_HEIGHT, config.SCREEN_HEIGHT) if y is None else y,
            speed=self.rng.uniform(0.18, 0.7),
            radius=self.rng.choice((1, 1, 2)),
            alpha=self.rng.randint(30, 95),
        )

    def generate_field(self) -> None:
        """Crea 30–40 hongos únicos, fuera de la HUD y de la zona del jugador."""
        self.mushrooms.clear()
        rows = range(config.MUSHROOM_MIN_ROW, config.MUSHROOM_MAX_SAFE_ROW + 1)
        candidates = [
            (gx, gy)
            for gy in rows
            for gx in range(1, config.GRID_COLUMNS - 1)
        ]
        count = self.rng.randint(30, 40)
        for gx, gy in self.rng.sample(candidates, count):
            self.mushrooms.append(Mushroom(gx, gy, health=3))

    def find(self, grid_x: int, grid_y: int) -> Mushroom | None:
        for mushroom in self.mushrooms:
            if mushroom.grid_x == grid_x and mushroom.grid_y == grid_y:
                return mushroom
        return None

    def add_mushroom(self, grid_x: int, grid_y: int, health: int = 3) -> Mushroom | None:
        """Coloca un hongo en una celda física; refuerza uno ya existente."""
        gx, gy = int(grid_x), int(grid_y)
        if not (0 <= gx < config.GRID_COLUMNS and 0 <= gy < config.GRID_ROWS):
            return None
        existing = self.find(gx, gy)
        if existing is not None:
            existing.health = max(existing.health, max(1, min(3, int(health))))
            return existing
        mushroom = Mushroom(gx, gy, health)
        self.mushrooms.append(mushroom)
        return mushroom

    def damage_mushroom(self, gx: int, gy: int) -> bool:
        """Inflige un punto de daño y elimina el hongo al llegar a cero."""
        mushroom = self.find(int(gx), int(gy))
        if mushroom is None:
            return False
        mushroom.health -= 1
        if mushroom.health <= 0:
            self.mushrooms.remove(mushroom)
        return True

    def mushroom_at_rect(self, rect: pygame.Rect) -> Mushroom | None:
        for mushroom in self.mushrooms:
            if mushroom.rect.colliderect(rect):
                return mushroom
        return None

    def damage_at_rect(self, rect: pygame.Rect) -> bool:
        mushroom = self.mushroom_at_rect(rect)
        if mushroom is None:
            return False
        return self.damage_mushroom(mushroom.grid_x, mushroom.grid_y)

    def collides(self, rect: pygame.Rect) -> bool:
        return self.mushroom_at_rect(rect) is not None

    def blocks_cell(self, grid_x: int, grid_y: int) -> bool:
        return self.find(int(grid_x), int(grid_y)) is not None

    def update(self) -> None:
        """Hace flotar las esporas; el conjunto se mantiene en quince unidades."""
        for index, spore in enumerate(self.spores):
            spore.y -= spore.speed
            if spore.y < config.HUD_HEIGHT:
                self.spores[index] = self._new_spore(
                    x=self.rng.uniform(0, config.SCREEN_WIDTH),
                    y=config.SCREEN_HEIGHT + self.rng.uniform(0, 24),
                )

    @staticmethod
    def _health_color(health: int, palette: dict[str, tuple[int, int, int]]) -> tuple[int, int, int]:
        if health >= 3:
            return palette["HONGO_3"]
        if health == 2:
            return palette["HONGO_2"]
        return palette["HONGO_1"]

    def draw(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)

        if style == config.ESTILO_MODERNO:
            if self._spores_layer is None or self._spores_layer.get_size() != surface.get_size():
                self._spores_layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._spores_layer.fill((0, 0, 0, 0))
            for spore in self.spores:
                pygame.draw.circle(
                    self._spores_layer,
                    (80, 220, 255, spore.alpha),
                    (round(spore.x), round(spore.y)),
                    spore.radius,
                )
            surface.blit(self._spores_layer, (0, 0))

        for mushroom in self.mushrooms:
            rect = mushroom.rect
            color = self._health_color(mushroom.health, palette)
            if style == config.ESTILO_RETRO:
                # Silueta escalonada de seta: píxeles rectangulares y sin suavizado.
                pygame.draw.rect(surface, color, (rect.x + 4, rect.y + 4, 12, 8))
                pygame.draw.rect(surface, color, (rect.x + 7, rect.y + 11, 6, 5))
                pygame.draw.rect(surface, palette["FONDO"], (rect.x + 6, rect.y + 6, 2, 2))
                pygame.draw.rect(surface, palette["FONDO"], (rect.x + 12, rect.y + 6, 2, 2))
            else:
                center = rect.center
                radius = 5 + mushroom.health
                config.draw_soft_glow(surface, center, color, radius + 5, 34)
                pygame.draw.circle(surface, color, center, radius)
                highlight = {
                    3: (255, 240, 248),
                    2: (255, 245, 190),
                    1: (225, 255, 255),
                }[mushroom.health]
                pygame.draw.circle(surface, highlight, (center[0] - 2, center[1] - 2), mushroom.health)
                pygame.draw.circle(surface, (80, 25, 48), (center[0] + 2, center[1] + 2), 2)
