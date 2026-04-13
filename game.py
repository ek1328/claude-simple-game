from settings import *
from maze import Maze
from pacman import PacMan
from ghost import Blinky, Pinky, Inky, Clyde, GhostMode


class GameState:
    START = 'start'
    READY = 'ready'
    PLAYING = 'playing'
    PACMAN_DEAD = 'pacman_dead'
    LEVEL_CLEAR = 'level_clear'
    GAME_OVER = 'game_over'


class Game:
    def __init__(self):
        self.maze = Maze()
        self.pacman = PacMan(self.maze)
        self.blinky = Blinky(self.maze)
        self.pinky  = Pinky(self.maze)
        self.inky   = Inky(self.maze)
        self.clyde  = Clyde(self.maze)
        self.ghosts = [self.blinky, self.pinky, self.inky, self.clyde]

        self.score = 0
        self.high_score = 0
        self.level = 1
        self.dots_eaten = 0
        self.ghost_eat_multiplier = 1
        self.extra_life_awarded = False

        self.state = GameState.START
        self.ready_timer = 0.0
        self.death_timer = 0.0
        self.level_clear_timer = 0.0
        self.level_clear_flash = False
        self.level_clear_flash_timer = 0.0

        # Phase timing
        self.phase_index = 0
        self.phase_timer = 0.0

    # ── Public interface ──────────────────────────────────────────────────────

    def update(self, dt, events):
        import pygame
        if self.state == GameState.START:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._start_game()

        elif self.state == GameState.READY:
            self.ready_timer -= dt
            if self.ready_timer <= 0:
                self.state = GameState.PLAYING

        elif self.state == GameState.PLAYING:
            self._update_playing(dt, events)

        elif self.state == GameState.PACMAN_DEAD:
            self.death_timer -= dt
            if self.death_timer <= 0:
                if self.pacman.lives > 0:
                    self._start_round()
                else:
                    self.state = GameState.GAME_OVER
                    if self.score > self.high_score:
                        self.high_score = self.score

        elif self.state == GameState.LEVEL_CLEAR:
            self.level_clear_timer -= dt
            self.level_clear_flash_timer += dt
            if self.level_clear_flash_timer >= 0.2:
                self.level_clear_flash_timer = 0.0
                self.level_clear_flash = not self.level_clear_flash
            if self.level_clear_timer <= 0:
                self.level += 1
                self._start_level()

        elif self.state == GameState.GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._restart()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _start_game(self):
        self.score = 0
        self.level = 1
        self.extra_life_awarded = False
        self.pacman.lives = STARTING_LIVES
        self._start_level()

    def _restart(self):
        self.__init__()

    def _start_level(self):
        self.maze.reset()
        self.dots_eaten = 0
        self.ghost_eat_multiplier = 1
        self.phase_index = 0
        self.phase_timer = 0.0
        self._reset_positions()
        self.state = GameState.READY
        self.ready_timer = READY_DURATION

    def _start_round(self):
        """After a death: reset positions but keep maze state."""
        self.ghost_eat_multiplier = 1
        self.phase_index = 0
        self.phase_timer = 0.0
        self._reset_positions()
        self.state = GameState.READY
        self.ready_timer = READY_DURATION

    def _reset_positions(self):
        self.pacman.reset()
        for g in self.ghosts:
            g.reset()

    def _update_playing(self, dt, events):
        import pygame

        # Pac-Man input + movement
        self.pacman.handle_input(events)
        self.pacman.update(dt)

        # Eating
        eaten = self.pacman.eat()
        if eaten == DOT:
            self.score += DOT_SCORE
            self.dots_eaten += 1
            self._check_extra_life()
        elif eaten == PELLET:
            self.score += PELLET_SCORE
            self.dots_eaten += 1
            self._check_extra_life()
            self._trigger_frightened()

        # Phase (scatter/chase) cycling
        current_phase_name, current_phase_dur = PHASE_SCHEDULE[self.phase_index]
        if current_phase_dur != float('inf'):
            self.phase_timer += dt
            if self.phase_timer >= current_phase_dur:
                self.phase_timer = 0.0
                self.phase_index = min(self.phase_index + 1, len(PHASE_SCHEDULE) - 1)
                new_phase, _ = PHASE_SCHEDULE[self.phase_index]
                new_mode = GhostMode.SCATTER if new_phase == 'scatter' else GhostMode.CHASE
                for g in self.ghosts:
                    g.set_mode(new_mode)

        # Ghost updates
        for g in self.ghosts:
            g.update(dt, self.pacman, self.blinky, self.dots_eaten)

        # Collisions
        pc, pr = self.pacman.get_tile()
        for g in self.ghosts:
            gc, gr = g.get_tile()
            if gc == pc and gr == pr:
                if g.mode == GhostMode.FRIGHTENED:
                    g.mode = GhostMode.EATEN
                    g.prev_mode = GhostMode.SCATTER
                    pts = GHOST_EAT_BASE * self.ghost_eat_multiplier
                    self.score += pts
                    self.ghost_eat_multiplier = min(self.ghost_eat_multiplier * 2, 8)
                    self._check_extra_life()
                elif g.mode in (GhostMode.SCATTER, GhostMode.CHASE):
                    self._pacman_die()
                    return

        # Level clear
        if self.maze.dots_remaining == 0:
            self.state = GameState.LEVEL_CLEAR
            self.level_clear_timer = LEVEL_CLEAR_DURATION
            self.level_clear_flash = False
            self.level_clear_flash_timer = 0.0

    def _trigger_frightened(self):
        self.ghost_eat_multiplier = 1
        for g in self.ghosts:
            g.set_frightened()

    def _pacman_die(self):
        self.pacman.alive = False
        self.pacman.lives -= 1
        self.state = GameState.PACMAN_DEAD
        self.death_timer = DEATH_DURATION

    def _check_extra_life(self):
        if not self.extra_life_awarded and self.score >= EXTRA_LIFE_SCORE:
            self.pacman.lives += 1
            self.extra_life_awarded = True
