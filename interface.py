"""HUD, menús y superposiciones de estado."""

from __future__ import annotations

import math

import pygame

import config


class HUD:
    def __init__(self) -> None:
        self._fonts: dict[tuple[str, int, bool], pygame.font.Font] = {}

    def _font(self, estilo: str, size: int, bold: bool = False) -> pygame.font.Font:
        key = (estilo, size, bold)
        if key not in self._fonts:
            family = "monospace" if estilo == config.ESTILO_RETRO else "dejavusans"
            self._fonts[key] = pygame.font.SysFont(family, size, bold=bold)
        return self._fonts[key]

    def _text(
        self,
        surface: pygame.Surface,
        text: str,
        position: tuple[int, int],
        color: tuple[int, int, int],
        estilo: str,
        size: int = 14,
        bold: bool = False,
    ) -> None:
        font = self._font(estilo, size, bold)
        rendered = font.render(text, estilo == config.ESTILO_MODERNO, color)
        surface.blit(rendered, position)

    def draw(
        self,
        surface: pygame.Surface,
        player,
        wave: int,
        estilo: str | None = None,
        high_score: int = 0,
    ) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)
        hud_color = palette["FONDO"]
        pygame.draw.rect(surface, hud_color, (0, 0, config.SCREEN_WIDTH, config.HUD_HEIGHT))

        if style == config.ESTILO_RETRO:
            primary = (255, 255, 255)
            secondary = (180, 180, 180)
            self._text(surface, f"1UP {player.score:06d}", (8, 3), primary, style, 14, True)
            self._text(surface, f"HIGH SCORE {high_score:06d}", (8, 21), secondary, style, 10)
            self._text(surface, f"STAGE {wave:02d}", (350, 12), primary, style, 14, True)
        else:
            primary = (225, 238, 255)
            secondary = (105, 133, 160)
            self._text(surface, "SCORE", (12, 2), secondary, style, 10, True)
            self._text(surface, f"{player.score:07d}", (12, 14), primary, style, 15, True)
            self._text(surface, f"BEST {high_score:07d}", (135, 14), secondary, style, 11)
            self._text(surface, f"WAVE  {wave:02d}", (345, 10), palette["CABEZA"], style, 15, True)
            pygame.draw.rect(surface, (25, 37, 53), (0, 37, config.SCREEN_WIDTH, 3))
            pygame.draw.rect(surface, palette["CABEZA"], (0, 37, 170, 3))
            pygame.draw.rect(surface, palette["TOTEM"], (345, 37, 110, 3))

        lives_start = 560
        if player.lives <= 0:
            self._text(surface, "0", (lives_start, 11), palette["NAVE"], style, 14, True)
        else:
            for index in range(min(player.lives, 5)):
                x = lives_start + index * 20
                points = ((x + 6, 8), (x, 25), (x + 6, 21), (x + 12, 25))
                pygame.draw.polygon(surface, palette["NAVE"], points)
            if player.lives > 5:
                self._text(surface, f"x{player.lives}", (lives_start + 104, 10), palette["NAVE"], style, 12, True)

        saucer_x = 728
        saucer_y = 18
        saucer_color = palette["TOTEM"] if player.totems else secondary
        pygame.draw.ellipse(surface, saucer_color, (saucer_x, saucer_y - 3, 22, 8))
        pygame.draw.arc(surface, saucer_color, (saucer_x + 5, saucer_y - 9, 12, 13), math.pi, math.tau, 2)
        pygame.draw.line(surface, saucer_color, (saucer_x + 3, saucer_y + 5), (saucer_x + 19, saucer_y + 5), 1)
        self._text(surface, f"x{player.totems}", (saucer_x + 27, 9), primary, style, 13, True)

        divider = (230, 230, 230) if style == config.ESTILO_RETRO else (31, 213, 232)
        pygame.draw.line(surface, divider, (0, config.HUD_DIVIDER_Y), (config.SCREEN_WIDTH, config.HUD_DIVIDER_Y), 1 if style == config.ESTILO_RETRO else 2)


class MenuManager:
    """Eventos y renderizado para menú principal, pausa y fin de partida."""

    OPTIONS = ("Start Game", "Exit")

    def __init__(self) -> None:
        self.selected_option = 0
        self.option_rects: list[pygame.Rect] = []
        self._fonts: dict[tuple[str, int, bool], pygame.font.Font] = {}

    def _font(self, estilo: str, size: int, bold: bool = False) -> pygame.font.Font:
        key = (estilo, size, bold)
        if key not in self._fonts:
            family = "monospace" if estilo == config.ESTILO_RETRO else "dejavusans"
            self._fonts[key] = pygame.font.SysFont(family, size, bold=bold)
        return self._fonts[key]

    def _render_centered(
        self,
        surface: pygame.Surface,
        text: str,
        y: int,
        color: tuple[int, int, int],
        estilo: str,
        size: int,
        bold: bool = False,
    ) -> pygame.Rect:
        image = self._font(estilo, size, bold).render(
            text,
            estilo == config.ESTILO_MODERNO,
            color,
        )
        rect = image.get_rect(center=(config.SCREEN_WIDTH // 2, y))
        surface.blit(image, rect)
        return rect

    def handle_main_menu_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_KP1):
                return "start"
            if event.key in (pygame.K_2, pygame.K_KP2):
                return "exit"
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_option = (self.selected_option - 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_option = (self.selected_option + 1) % len(self.OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return "start" if self.selected_option == 0 else "exit"
        elif event.type == pygame.MOUSEMOTION:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_option = index
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for index, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_option = index
                    return "start" if index == 0 else "exit"
        return None

    def draw_main_menu(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        palette = config.obtener_paleta(style)
        ticks = pygame.time.get_ticks()
        pulse = 0.65 + 0.35 * math.sin(ticks / 360.0)
        title_color = palette["CABEZA"]
        if style == config.ESTILO_MODERNO:
            title_color = tuple(min(255, int(channel * (0.72 + 0.28 * pulse))) for channel in title_color)
            shadow = self._font(style, 56, True).render("CENTIPEDE", True, (183, 50, 255))
            shadow_rect = shadow.get_rect(center=(config.SCREEN_WIDTH // 2 + 3, 174))
            surface.blit(shadow, shadow_rect)

        self._render_centered(surface, "CENTIPEDE", 170, title_color, style, 54 if style == config.ESTILO_RETRO else 56, True)
        subtitle = "ARCADE REMIX  ·  1981 / 2081"
        self._render_centered(surface, subtitle, 220, (145, 164, 185), style, 15, True)
        self._render_centered(surface, "Flechas / WASD para mover  ·  T para cambiar estilo", 278, (177, 190, 210), style, 16)

        self.option_rects = []
        for index, option in enumerate(self.OPTIONS):
            rect = pygame.Rect(270, 328 + index * 64, 260, 48)
            self.option_rects.append(rect)
            selected = index == self.selected_option
            color = palette["CABEZA"] if selected else (100, 115, 135)
            if style == config.ESTILO_RETRO:
                pygame.draw.rect(surface, color, rect, 2 if selected else 1)
                text_color = (255, 255, 255) if selected else (145, 145, 145)
            else:
                fill = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(fill, (*color, 24 if selected else 8), fill.get_rect(), border_radius=8)
                surface.blit(fill, rect)
                pygame.draw.rect(surface, color, rect, 2 if selected else 1, border_radius=8)
                text_color = (235, 248, 255) if selected else (145, 159, 180)
            image = self._font(style, 21, selected).render(
                f"{index + 1}. {option}", style == config.ESTILO_MODERNO, text_color
            )
            surface.blit(image, image.get_rect(center=rect.center))

        hint = "ENTER / 1 para comenzar     2 para salir"
        self._render_centered(surface, hint, 492, (135, 148, 168), style, 14)
        style_label = f"ESTILO: {style}  [T]"
        self._render_centered(surface, style_label, 554, palette["TOTEM"], style, 14, True)

    def draw_pause(self, surface: pygame.Surface, estilo: str | None = None) -> None:
        style = config.normalizar_estilo(estilo)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 175))
        surface.blit(overlay, (0, 0))
        palette = config.obtener_paleta(style)
        self._render_centered(surface, "PAUSA", 250, palette["CABEZA"], style, 48, True)
        self._render_centered(surface, "Presiona P o SHIFT para reanudar", 310, (235, 240, 250), style, 20)

    def draw_game_over(
        self,
        surface: pygame.Surface,
        score: int,
        estilo: str | None = None,
    ) -> None:
        style = config.normalizar_estilo(estilo)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 205))
        surface.blit(overlay, (0, 0))
        palette = config.obtener_paleta(style)
        self._render_centered(surface, "GAME OVER", 220, palette["HONGO_3"], style, 46, True)
        self._render_centered(surface, f"PUNTUACION FINAL  {score}", 290, (245, 245, 255), style, 22, True)
        self._render_centered(surface, "ENTER para volver a jugar", 360, palette["CABEZA"], style, 18)
