"""Configuración compartida, paletas y coordenadas del juego.

La cuadrícula del mundo comienza justo debajo de la línea de la HUD: su fila
lógica 0 se dibuja en Y=40. Así el ciempiés puede iniciar en la fila 0 sin
ocultar la interfaz; las posiciones del jugador siguen expresándose en píxeles
absolutos de pantalla.
"""

from __future__ import annotations

from enum import Enum

import pygame

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CELL_SIZE = 20
GRID_COLUMNS = SCREEN_WIDTH // CELL_SIZE
GRID_ROWS = SCREEN_HEIGHT // CELL_SIZE
FPS = 60

HUD_HEIGHT = 40
HUD_DIVIDER_Y = 40
WORLD_ROW_OFFSET = HUD_HEIGHT // CELL_SIZE
WORLD_MAX_ROW = GRID_ROWS - WORLD_ROW_OFFSET - 1  # fila física 29
PLAYER_ZONE_TOP = 400
PLAYER_ZONE_BOTTOM = SCREEN_HEIGHT
PLAYER_ZONE_FIRST_WORLD_ROW = PLAYER_ZONE_TOP // CELL_SIZE - WORLD_ROW_OFFSET
MUSHROOM_MIN_ROW = 3
MUSHROOM_MAX_ROW = 26
# Las coordenadas de hongos son filas físicas; la fila 20 inicia la zona segura.
MUSHROOM_MAX_SAFE_ROW = min(MUSHROOM_MAX_ROW, PLAYER_ZONE_TOP // CELL_SIZE - 1)

ESTILO_RETRO = "RETRO_80S"
ESTILO_MODERNO = "MODERNO"
ESTILOS = (ESTILO_RETRO, ESTILO_MODERNO)
ESTILO_ACTUAL = ESTILO_RETRO


class GameState(str, Enum):
    MENU = "MENU"
    PLAYING = "JUGANDO"
    PAUSED = "PAUSA"
    GAME_OVER = "GAMEOVER"


PALETAS = {
    ESTILO_RETRO: {
        "FONDO": (0, 0, 0),
        "CABEZA": (0, 255, 0),
        "CUERPO": (0, 200, 0),
        "HONGO_3": (255, 0, 0),
        "HONGO_2": (255, 255, 0),
        "HONGO_1": (255, 255, 255),
        "NAVE": (255, 255, 255),
        "BALA": (255, 255, 0),
        "TOTEM": (255, 0, 255),
    },
    ESTILO_MODERNO: {
        "FONDO": (15, 16, 22),
        "CABEZA": (0, 242, 254),
        "CUERPO": (0, 170, 255),
        "HONGO_3": (255, 0, 127),
        "HONGO_2": (255, 100, 0),
        "HONGO_1": (255, 210, 0),
        "NAVE": (168, 172, 190),
        "BALA": (0, 255, 66),
        "TOTEM": (186, 85, 211),
    },
}


def normalizar_estilo(estilo: str | Enum | None = None) -> str:
    """Devuelve un nombre de estilo válido, usando el estilo global por defecto."""
    if estilo is None:
        estilo = ESTILO_ACTUAL
    if isinstance(estilo, Enum):
        estilo = str(estilo.value)
    estilo = str(estilo)
    if estilo not in PALETAS:
        raise ValueError(f"Estilo visual desconocido: {estilo!r}")
    return estilo


def obtener_paleta(estilo: str | Enum | None = None) -> dict[str, tuple[int, int, int]]:
    return PALETAS[normalizar_estilo(estilo)]


def toggle_style() -> str:
    """Conmuta el estilo global y devuelve el estilo recién activado."""
    global ESTILO_ACTUAL
    ESTILO_ACTUAL = (
        ESTILO_MODERNO if ESTILO_ACTUAL == ESTILO_RETRO else ESTILO_RETRO
    )
    return ESTILO_ACTUAL


def set_style(estilo: str) -> None:
    """Activa explícitamente un estilo válido."""
    global ESTILO_ACTUAL
    ESTILO_ACTUAL = normalizar_estilo(estilo)


def grid_to_screen_rect(
    grid_x: int,
    grid_y: int,
    width: int = CELL_SIZE,
    height: int = CELL_SIZE,
) -> pygame.Rect:
    """Convierte una celda de la cuadrícula física de pantalla a un rectángulo."""
    return pygame.Rect(
        int(grid_x) * CELL_SIZE,
        int(grid_y) * CELL_SIZE,
        int(width),
        int(height),
    )


def world_to_screen_rect(
    grid_x: int,
    world_y: int,
    width: int = CELL_SIZE,
    height: int = CELL_SIZE,
) -> pygame.Rect:
    """Convierte una fila relativa al campo (fila 0 bajo la HUD) a pantalla."""
    return grid_to_screen_rect(grid_x, int(world_y) + WORLD_ROW_OFFSET, width, height)


_GLOW_CACHE: dict[tuple[tuple[int, int, int], int, int], pygame.Surface] = {}


def draw_soft_glow(
    surface: pygame.Surface,
    center: tuple[int, int],
    color: tuple[int, int, int],
    radius: int,
    max_alpha: int = 64,
) -> None:
    """Blitea un resplandor radial suave reutilizando superficies cacheadas."""
    radius = max(1, int(radius))
    max_alpha = max(0, min(255, int(max_alpha)))
    key = (tuple(color), radius, max_alpha)
    glow = _GLOW_CACHE.get(key)
    if glow is None:
        size = radius * 2 + 2
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        glow_center = (radius + 1, radius + 1)
        for current_radius in range(radius, 0, -1):
            distance = (radius - current_radius + 1) / radius
            alpha = int(max_alpha * distance * distance)
            pygame.draw.circle(glow, (*color, alpha), glow_center, current_radius)
        _GLOW_CACHE[key] = glow
    surface.blit(glow, (int(center[0]) - radius - 1, int(center[1]) - radius - 1))


def draw_background(surface: pygame.Surface, estilo: str | None = None) -> None:
    """Dibuja el fondo plano retro o la cuadrícula cyberpunk moderna."""
    style = normalizar_estilo(estilo)
    palette = PALETAS[style]
    surface.fill(palette["FONDO"])
    if style == ESTILO_MODERNO:
        draw_soft_glow(surface, (SCREEN_WIDTH // 2, (HUD_HEIGHT + SCREEN_HEIGHT) // 2), (38, 20, 55), 270, 12)
        grid_color = (27, 30, 40)
        for x in range(0, SCREEN_WIDTH + 1, CELL_SIZE):
            pygame.draw.line(surface, grid_color, (x, HUD_HEIGHT), (x, SCREEN_HEIGHT))
        for y in range(HUD_HEIGHT, SCREEN_HEIGHT + 1, CELL_SIZE):
            pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y))
