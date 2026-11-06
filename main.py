"""Punto de entrada y coordinación del juego Centipede."""

from __future__ import annotations

from typing import Any

import pygame

import config
from blocks import MushroomField
from enemy import CentipedeSystem
from interface import HUD, MenuManager
from player import Player


class CentipedeGame:
    """Orquesta estados, colisiones y módulos sin dependencias circulares."""

    def __init__(self, surface: pygame.Surface) -> None:
        self.surface = surface
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = config.GameState.MENU
        self.level = 1
        self.high_score = 0
        self.hud = HUD()
        self.menu = MenuManager()
        self._create_world()

    def _create_world(self) -> None:
        self.player = Player()
        self.mushrooms = MushroomField()
        self.centipedes = CentipedeSystem(self.level)

    def start_new_game(self) -> None:
        self.level = 1
        self._create_world()
        self.state = config.GameState.PLAYING

    @staticmethod
    def _key_pressed(keys: Any, key_code: int) -> bool:
        if keys is None:
            return False
        if hasattr(keys, "get"):
            return bool(keys.get(key_code, False))
        try:
            return bool(keys[key_code])
        except (IndexError, KeyError, TypeError):
            return False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_t:
            config.toggle_style()
            return

        if self.state == config.GameState.MENU:
            action = self.menu.handle_main_menu_event(event)
            if action == "start":
                self.start_new_game()
            elif action == "exit":
                self.running = False
            return

        if event.type != pygame.KEYDOWN:
            return

        pause_keys = (pygame.K_p, pygame.K_LSHIFT, pygame.K_RSHIFT, pygame.K_ESCAPE)
        if self.state == config.GameState.PLAYING:
            if event.key in pause_keys:
                self.state = config.GameState.PAUSED
            elif event.key == pygame.K_SPACE:
                self.player.shoot()
        elif self.state == config.GameState.PAUSED:
            if event.key in pause_keys:
                self.state = config.GameState.PLAYING
        elif self.state == config.GameState.GAME_OVER and event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.start_new_game()

    def update(self, keys: Any = None) -> None:
        if self.state != config.GameState.PLAYING:
            return
        if keys is None:
            keys = pygame.key.get_pressed()

        self.mushrooms.update()
        self.player.update(keys, self.mushrooms)
        if self._key_pressed(keys, pygame.K_SPACE):
            self.player.shoot()
        self.player.update_bullets()
        self.centipedes.update(self.mushrooms)
        self._resolve_bullet_collisions()
        self._collect_totems()
        self._resolve_player_collision()

        if self.state == config.GameState.PLAYING and self.centipedes.is_empty:
            self._advance_wave()
        self.high_score = max(self.high_score, self.player.score)

    def _resolve_bullet_collisions(self) -> None:
        for bullet in tuple(self.player.bullets):
            hit = self.centipedes.segment_at_rect(bullet.rect)
            if hit is not None:
                chain, index, _segment = hit
                result = self.centipedes.handle_segment_hit(chain, index, self.mushrooms)
                if result is not None:
                    self.player.score += result.points
                    if bullet in self.player.bullets:
                        self.player.bullets.remove(bullet)
                    continue

            if self.mushrooms.damage_at_rect(bullet.rect):
                if bullet in self.player.bullets:
                    self.player.bullets.remove(bullet)

    def _collect_totems(self) -> None:
        for item in tuple(self.centipedes.totem_items):
            if self.player.rect.colliderect(item.rect) and self.centipedes.collect_totem(item):
                self.player.totems += 1

    def _resolve_player_collision(self) -> None:
        if self.player.invulnerability_frames > 0:
            return
        if not any(segment.rect.colliderect(self.player.rect) for segment in self.centipedes.segments):
            return

        if self.player.totems > 0:
            self.player.totems -= 1
            self.player.invulnerability_frames = 180
            return

        self.player.lives -= 1
        self.high_score = max(self.high_score, self.player.score)
        self.player.reset_position()
        if self.player.lives <= 0:
            self.state = config.GameState.GAME_OVER
            return

        # La oleada se reinicia arriba; los hongos dañados persisten en el campo.
        self.centipedes.start_level(self.level)

    def _advance_wave(self) -> None:
        self.level += 1
        self.mushrooms.generate_field()
        self.player.bullets.clear()
        self.centipedes.start_level(self.level)

    def draw(self) -> None:
        style = config.ESTILO_ACTUAL
        config.draw_background(self.surface, style)
        if self.state == config.GameState.MENU:
            self.menu.draw_main_menu(self.surface, style)
            return

        self.mushrooms.draw(self.surface, style)
        self.centipedes.draw(self.surface, style)
        self.player.draw(self.surface, style)
        self.hud.draw(self.surface, self.player, self.level, style, self.high_score)

        if self.state == config.GameState.PAUSED:
            self.menu.draw_pause(self.surface, style)
        elif self.state == config.GameState.GAME_OVER:
            self.menu.draw_game_over(self.surface, self.player.score, style)

    def run(self) -> None:
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)
            if self.state == config.GameState.PLAYING:
                self.update(pygame.key.get_pressed())
            self.draw()
            pygame.display.flip()
            self.clock.tick(config.FPS)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Centipede — Arcade Remix")
    screen = pygame.display.set_mode(
        (config.SCREEN_WIDTH, config.SCREEN_HEIGHT),
        pygame.DOUBLEBUF,
    )
    try:
        CentipedeGame(screen).run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
