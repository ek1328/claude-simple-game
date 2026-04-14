import math
import pygame
from settings import *
from game import GameState


class Renderer:

    def __init__(self, screen):
        self.screen = screen
        self.font_large = pygame.font.SysFont("monospace", 28, bold=True)
        self.font_med   = pygame.font.SysFont("monospace", 18, bold=True)
        self.font_small = pygame.font.SysFont("monospace", 14)
        self.time = 0.0

    def draw(self, game, dt=0.016):
        self.time += dt
        self.screen.fill(BLACK)

        if game.state == GameState.START:
            self._draw_maze(game.maze, flash=False)
            self._draw_start_screen()
        elif game.state == GameState.READY:
            self._draw_maze(game.maze, flash=False)
            self._draw_pacman(game.pacman)
            for g in game.ghosts:
                g.draw(self.screen)
            self._draw_hud(game)
            self._draw_ready()
        elif game.state == GameState.PLAYING:
            self._draw_maze(game.maze, flash=False)
            self._draw_pacman(game.pacman)
            for g in game.ghosts:
                g.draw(self.screen)
            self._draw_hud(game)
        elif game.state == GameState.PAUSED:
            self._draw_maze(game.maze, flash=False)
            self._draw_pacman(game.pacman)
            for g in game.ghosts:
                g.draw(self.screen)
            self._draw_hud(game)
            self._draw_pause_screen()
        elif game.state == GameState.QUIT_CONFIRM:
            self._draw_maze(game.maze, flash=False)
            self._draw_pacman(game.pacman)
            for g in game.ghosts:
                g.draw(self.screen)
            self._draw_hud(game)
            self._draw_quit_confirm()
        elif game.state == GameState.PACMAN_DEAD:
            self._draw_maze(game.maze, flash=False)
            for g in game.ghosts:
                g.draw(self.screen)
            self._draw_hud(game)
        elif game.state == GameState.LEVEL_CLEAR:
            self._draw_maze(game.maze, flash=game.level_clear_flash)
            self._draw_hud(game)
            self._draw_text_centered("LEVEL CLEAR!", self.font_large, YELLOW,
                                     SCREEN_H // 2)
        elif game.state == GameState.GAME_OVER:
            self._draw_maze(game.maze, flash=False)
            self._draw_hud(game)
            self._draw_game_over(game)

    def _draw_maze(self, maze, flash=False):
        for row in range(ROWS):
            for col in range(COLS):
                tile = maze.grid[row][col]
                px = col * TILE_SIZE
                py = row * TILE_SIZE + HUD_H
                rect = pygame.Rect(px, py, TILE_SIZE, TILE_SIZE)

                if tile == WALL:
                    color = YELLOW if flash else WALL_COLOR
                    pygame.draw.rect(self.screen, color, rect)
                    # Inset border for depth
                    inner = rect.inflate(-4, -4)
                    border_color = YELLOW if flash else WALL_BORDER
                    pygame.draw.rect(self.screen, border_color, inner)
                elif tile == DOT:
                    cx = px + TILE_SIZE // 2
                    cy = py + TILE_SIZE // 2
                    pygame.draw.circle(self.screen, DOT_COLOR, (cx, cy), 3)
                elif tile == PELLET:
                    cx = px + TILE_SIZE // 2
                    cy = py + TILE_SIZE // 2
                    # Pulsing size
                    pulse = int(2 * math.sin(self.time * 4)) + 7
                    pygame.draw.circle(self.screen, PELLET_COLOR, (cx, cy), pulse)
                elif tile == GHOST_DOOR:
                    # White door bar
                    door_rect = pygame.Rect(px, py + TILE_SIZE // 2 - 2, TILE_SIZE, 4)
                    pygame.draw.rect(self.screen, (255, 200, 200), door_rect)

    def _draw_pacman(self, pacman):
        pacman.draw(self.screen)

    def _draw_hud(self, game):
        hud_rect = pygame.Rect(0, 0, SCREEN_W, HUD_H)
        pygame.draw.rect(self.screen, BLACK, hud_rect)

        # Score
        score_surf = self.font_med.render(f"SCORE {game.score:06d}", True, WHITE)
        self.screen.blit(score_surf, (8, 8))

        # High score
        hi_surf = self.font_med.render(f"BEST {game.high_score:06d}", True, (180, 180, 180))
        self.screen.blit(hi_surf, (SCREEN_W // 2 - hi_surf.get_width() // 2, 8))

        # Lives
        life_radius = 8
        for i in range(game.pacman.lives):
            lx = SCREEN_W - 20 - i * (life_radius * 2 + 4)
            ly = HUD_H // 2
            pygame.draw.circle(self.screen, YELLOW, (lx, ly), life_radius)

    def _draw_start_screen(self):
        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        title = self.font_large.render("PAC-MAN", True, YELLOW)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2,
                                  SCREEN_H // 2 - 60))

        sub = self.font_med.render("Press SPACE to Start", True, WHITE)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2,
                                SCREEN_H // 2))

        ctrl = self.font_small.render("Arrow Keys / WASD to move  |  ESC to quit", True,
                                       (180, 180, 180))
        self.screen.blit(ctrl, (SCREEN_W // 2 - ctrl.get_width() // 2,
                                 SCREEN_H // 2 + 40))

    def _draw_ready(self):
        ready = self.font_large.render("READY!", True, YELLOW)
        self.screen.blit(ready, (SCREEN_W // 2 - ready.get_width() // 2,
                                   SCREEN_H // 2 - 20))

    def _draw_game_over(self, game):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        go = self.font_large.render("GAME OVER", True, RED)
        self.screen.blit(go, (SCREEN_W // 2 - go.get_width() // 2,
                               SCREEN_H // 2 - 60))

        score_txt = self.font_med.render(f"Score: {game.score}", True, WHITE)
        self.screen.blit(score_txt, (SCREEN_W // 2 - score_txt.get_width() // 2,
                                      SCREEN_H // 2 - 10))

        if game.score >= game.high_score and game.score > 0:
            hi = self.font_med.render("NEW HIGH SCORE!", True, YELLOW)
            self.screen.blit(hi, (SCREEN_W // 2 - hi.get_width() // 2,
                                   SCREEN_H // 2 + 25))

        restart = self.font_med.render("Press SPACE to Play Again", True, (180, 180, 180))
        self.screen.blit(restart, (SCREEN_W // 2 - restart.get_width() // 2,
                                    SCREEN_H // 2 + 55))

    def _draw_pause_screen(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        self._draw_text_centered("PAUSED", self.font_large, YELLOW, SCREEN_H // 2 - 30)
        self._draw_text_centered("P  — Resume", self.font_med, WHITE, SCREEN_H // 2 + 10)
        self._draw_text_centered("Q  — Quit", self.font_med, (180, 180, 180), SCREEN_H // 2 + 36)

    def _draw_quit_confirm(self):
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        box_w, box_h = 320, 130
        box_x = SCREEN_W // 2 - box_w // 2
        box_y = SCREEN_H // 2 - box_h // 2
        pygame.draw.rect(self.screen, (40, 40, 40), (box_x, box_y, box_w, box_h), border_radius=8)
        pygame.draw.rect(self.screen, WHITE, (box_x, box_y, box_w, box_h), width=2, border_radius=8)

        self._draw_text_centered("Quit to desktop?", self.font_med, WHITE, box_y + 20)
        self._draw_text_centered("Y / Enter  —  Yes, quit", self.font_small, (255, 100, 100), box_y + 58)
        self._draw_text_centered("N / Esc      —  No, resume", self.font_small, (100, 255, 100), box_y + 82)

    def _draw_text_centered(self, text, font, color, y):
        surf = font.render(text, True, color)
        self.screen.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2, y))
