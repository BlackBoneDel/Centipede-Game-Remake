"""Ciempiés divididos, movimiento por cuadrícula y objetos coleccionables."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

import pygame

import config
from blocks import MushroomField


NORMAL = "NORMAL"
MUTANTE = "MUTANTE"
LEGENDARIO = "LEGENDARIO"
TIPOS_CIEMPIES = (NORMAL, MUTANTE, LEGENDARIO)
BASE_MOVE_INTERVAL = 8.0
LEGENDARY_TOTEM_DROP_CHANCE = 0.4


@dataclass
class CentipedeSegment:
    """Un segmento en coordenadas de cuadrícula lógica del mundo."""

    x: int
    y: int
    dx: int = 1
    dy: int = 1
    is_head: bool = False
    kind: str = NORMAL

    def __post_init__(self) -> None:
        self.x = int(self.x)
        self.y = int(self.y)
        self.dx = 1 if self.dx >= 0 else -1
        self.dy = 1 if self.dy >= 0 else -1
        if self.kind not in TIPOS_CIEMPIES:
            raise ValueError(f"Tipo de ciempiés desconocido: {self.kind!r}")

    @property
    def rect(self) -> pygame.Rect:
        return config.world_to_screen_rect(self.x, self.y)


@dataclass
class CentipedeChain:
    """Lista independiente de segmentos ordenada desde la cabeza a la cola."""

    segments: list[CentipedeSegment]
    kind: str
    movement_credit: float = 0.0


@dataclass
class CentipedeHit:
    segment: CentipedeSegment
    points: int
    dropped_totem: bool


class TotemItem:
    """Tótem flotante que aparece en el suelo de la zona de juego."""

    def __init__(
        self,
        grid_x: int,
        grid_y: int = config.GRID_ROWS - 1,
        rng: random.Random | None = None,
    ) -> None:
        self.grid_x = max(0, min(config.GRID_COLUMNS - 1, int(grid_x)))
        self.grid_y = max(0, min(config.GRID_ROWS - 1, int(grid_y)))
        self.base_x = self.grid_x * config.CELL_SIZE + config.CELL_SIZE / 2
        self.base_y = self.grid_y * config.CELL_SIZE + config.CELL_SIZE / 2
        self.phase = (rng if rng is not None else random.Random()).uniform(0, math.tau)
        self.collected = False

    @property
    def rect(self) -> pygame.Rect:
        bob = math.sin(self.phase) * 3.5
        return pygame.Rect(round(self.base_x - 10), round(self.base_y + bob - 9), 20, 18)

    def update(self) -> None:
        self.phase = (self.phase + 0.11) % math.tau

    def draw(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)
        rect = self.rect
        center_x, center_y = rect.center
        color = palette["TOTEM"]
        if style == config.ESTILO_RETRO:
            pygame.draw.polygon(
                surface,
                color,
                ((center_x, rect.top), (rect.right - 2, center_y), (center_x, rect.bottom - 1), (rect.left + 2, center_y)),
            )
            pygame.draw.rect(surface, palette["FONDO"], (center_x - 2, center_y - 2, 4, 4))
            return

        config.draw_soft_glow(surface, (center_x, center_y), color, 14, 65)
        diamond = (
            (center_x, rect.top),
            (rect.right - 1, center_y),
            (center_x, rect.bottom - 1),
            (rect.left + 1, center_y),
        )
        pygame.draw.polygon(surface, color, diamond)
        pygame.draw.polygon(surface, (245, 225, 255), diamond, 1)
        pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), 2)


class CentipedeSystem:
    """Administra cadenas independientes, divisiones, tipos y tótems."""

    def __init__(self, level: int = 1, rng: random.Random | None = None) -> None:
        self.rng = rng if rng is not None else random.Random()
        self.level = max(1, int(level))
        self.chains: list[CentipedeChain] = []
        self.totem_items: list[TotemItem] = []
        self.start_level(self.level)

    @property
    def segments(self) -> list[CentipedeSegment]:
        """Vista plana de los segmentos vivos, útil para colisiones e interfaz."""
        return [segment for chain in self.chains for segment in chain.segments]

    @property
    def is_empty(self) -> bool:
        return not self.chains

    def _roll_kind(self) -> str:
        roll = self.rng.random()
        if roll < 0.15:
            return MUTANTE
        if roll < 0.25:
            return LEGENDARIO
        return NORMAL

    def start_level(self, level: int) -> None:
        self.level = max(1, int(level))
        self.chains.clear()
        self.totem_items.clear()
        kind = self._roll_kind()
        length = min(10 + self.level - 1, 20)
        head_x = length - 1
        segments = [
            CentipedeSegment(
                x=head_x - index,
                y=0,
                dx=1,
                dy=1,
                is_head=index == 0,
                kind=kind,
            )
            for index in range(length)
        ]
        self.chains.append(CentipedeChain(segments=segments, kind=kind))

    def update(self, mushrooms: MushroomField) -> None:
        interval = max(3.0, BASE_MOVE_INTERVAL - (self.level - 1) * 0.25)
        for chain in tuple(self.chains):
            if not chain.segments:
                self.chains = [current for current in self.chains if current is not chain]
                continue
            chain.movement_credit += 1.5 if chain.kind == MUTANTE else 1.0
            while chain.movement_credit >= interval:
                chain.movement_credit -= interval
                self._move_chain(chain, mushrooms)

        for totem in self.totem_items:
            totem.update()

    def _move_chain(self, chain: CentipedeChain, mushrooms: MushroomField) -> None:
        if not chain.segments:
            return
        old_positions = [
            (segment.x, segment.y, segment.dx, segment.dy)
            for segment in chain.segments
        ]
        head = chain.segments[0]
        next_x = head.x + head.dx
        blocked = (
            next_x < 0
            or next_x >= config.GRID_COLUMNS
            or mushrooms.blocks_cell(next_x, head.y + config.WORLD_ROW_OFFSET)
        )

        if blocked:
            head.dx = -head.dx
            next_y = head.y + head.dy
            if next_y > config.WORLD_MAX_ROW:
                head.y = config.WORLD_MAX_ROW
                head.dy = -1
            elif head.y >= config.PLAYER_ZONE_FIRST_WORLD_ROW and next_y <= config.PLAYER_ZONE_FIRST_WORLD_ROW:
                head.y = config.PLAYER_ZONE_FIRST_WORLD_ROW
                head.dy = 1
            elif next_y < 0:
                head.y = 0
                head.dy = 1
            else:
                head.y = next_y
                if head.y == config.WORLD_MAX_ROW:
                    head.dy = -1
                elif head.y == config.PLAYER_ZONE_FIRST_WORLD_ROW:
                    head.dy = 1
        else:
            head.x = next_x

        # Cada segmento ocupa la posición que tenía delante en este mismo tick.
        for index in range(1, len(chain.segments)):
            segment = chain.segments[index]
            previous_x, previous_y, previous_dx, previous_dy = old_positions[index - 1]
            segment.x = previous_x
            segment.y = previous_y
            segment.dx = previous_dx
            segment.dy = previous_dy

    def segment_at_rect(
        self,
        rect: pygame.Rect,
    ) -> tuple[CentipedeChain, int, CentipedeSegment] | None:
        for chain in self.chains:
            for index, segment in enumerate(chain.segments):
                if segment.rect.colliderect(rect):
                    return chain, index, segment
        return None

    def handle_segment_hit(
        self,
        chain: CentipedeChain,
        index: int,
        mushrooms: MushroomField,
    ) -> CentipedeHit | None:
        """Elimina un segmento, divide la cadena y promueve la cola a cabeza."""
        if not any(current is chain for current in self.chains):
            return None
        if not 0 <= index < len(chain.segments):
            return None

        old_segments = chain.segments
        hit_segment = old_segments[index]
        front = old_segments[:index]
        rear = old_segments[index + 1 :]
        if index > 0:
            mushrooms.add_mushroom(
                hit_segment.x,
                hit_segment.y + config.WORLD_ROW_OFFSET,
                health=3,
            )

        self.chains = [current for current in self.chains if current is not chain]
        chain.segments = []
        if front:
            self._set_chain_head(front)
            self.chains.append(CentipedeChain(front, chain.kind, chain.movement_credit))
        if rear:
            self._set_chain_head(rear)
            self.chains.append(CentipedeChain(rear, chain.kind, chain.movement_credit))

        dropped = False
        if hit_segment.kind == LEGENDARIO and self.rng.random() < LEGENDARY_TOTEM_DROP_CHANCE:
            item = TotemItem(hit_segment.x, config.GRID_ROWS - 1, self.rng)
            self.totem_items.append(item)
            dropped = True

        base_points = 100 if hit_segment.is_head else 10
        type_bonus = 50 if hit_segment.kind == LEGENDARIO else 20 if hit_segment.kind == MUTANTE else 0
        return CentipedeHit(hit_segment, base_points + type_bonus, dropped)

    @staticmethod
    def _set_chain_head(segments: list[CentipedeSegment]) -> None:
        for index, segment in enumerate(segments):
            segment.is_head = index == 0

    def collect_totem(self, item: TotemItem) -> bool:
        for index, current in enumerate(self.totem_items):
            if current is item:
                current.collected = True
                del self.totem_items[index]
                return True
        return False

    def draw(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)
        for chain in self.chains:
            for segment in chain.segments:
                rect = segment.rect
                color = self._segment_color(segment, style, palette)
                if style == config.ESTILO_RETRO:
                    inset = 1 if segment.is_head else 2
                    pygame.draw.rect(
                        surface,
                        color,
                        (rect.x + inset, rect.y + inset, rect.width - inset * 2, rect.height - inset * 2),
                    )
                    if segment.is_head:
                        pygame.draw.rect(surface, (0, 0, 0), (rect.x + 5, rect.y + 6, 3, 3))
                        pygame.draw.rect(surface, (0, 0, 0), (rect.x + 12, rect.y + 6, 3, 3))
                    else:
                        pygame.draw.rect(surface, palette["FONDO"], (rect.x + 8, rect.y + 8, 4, 4))
                else:
                    center = rect.center
                    radius = 9 if segment.is_head else 8
                    config.draw_soft_glow(surface, center, color, radius + 5, 42)
                    pygame.draw.circle(surface, color, center, radius)
                    pygame.draw.circle(surface, (225, 250, 255), center, radius, 1)
                    if segment.is_head:
                        pygame.draw.circle(surface, (8, 16, 26), (center[0] - 3, center[1] - 2), 2)
                        pygame.draw.circle(surface, (8, 16, 26), (center[0] + 3, center[1] - 2), 2)
        for item in self.totem_items:
            item.draw(surface, style)

    @staticmethod
    def _segment_color(
        segment: CentipedeSegment,
        estilo: str,
        palette: dict[str, tuple[int, int, int]],
    ) -> tuple[int, int, int]:
        if segment.kind == MUTANTE:
            return (255, 0, 200) if estilo == config.ESTILO_RETRO else (255, 65, 210)
        if segment.kind == LEGENDARIO:
            return (255, 255, 0) if estilo == config.ESTILO_RETRO else (255, 196, 55)
        return palette["CABEZA"] if segment.is_head else palette["CUERPO"]
