import math
import pygame
from settings import *
from maze import Maze
from pacman import PacMan
from ghost import Blinky, Pinky, Inky, Clyde, GhostMode
from sounds import PacManSounds


class GameState:
    START = 'start'
    READY = 'ready'
    PLAYING = 'playing'
    PAUSED = 'paused'
    QUIT_CONFIRM = 'quit_confirm'
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
        self.sounds = PacManSounds()

        self.score = 0
        self.high_score = 0
        self.level = 1
        self.dots_eaten = 0
        self.lives = STARTING_LIVES
        self.ghost_eat_multiplier = 1
        self.extra_life_awarded = False

        # Fruit system
        self.fruit_active = False
        self.fruit_timer = 0.0
        self.fruit_tile = None         # (col, row) where fruit appears
        self.fruit_visible = False     # True after spawn delay
        self.fruit_spawn_timer = 0.0
        self.fruit_triggered = [False, False]  # [first_fruit, second_fruit]

        # Floating score display
        self.floating_scores = []      # list of (x, y, text, timer)

        # Freeze timer (pauses game briefly after eating ghost/fruit)
        self.freeze_timer = 0.0

        self.state = GameState.START
        self.pre_pause_state = None
        self.quit_requested = False
        self.ready_timer = 0.0
        self.death_timer = 0.0
        self.level_clear_timer = 0.0
        self.level_clear_flash = False
        self.level_clear_flash_timer = 0.0

        # Phase timing (scatter/chase)
        self.phase_index = 0
        self.phase_timer = 0.0

    # ── Public interface ──────────────────────────────────────────────────────

    def update(self, dt, events):
        # Global hotkeys — work from any active game state
        active = self.state in (GameState.PLAYING, GameState.PAUSED,
                                GameState.QUIT_CONFIRM, GameState.READY)
        for event in events:
            if event.type == pygame.KEYDOWN:
                if active and event.key == pygame.K_p:
                    self._toggle_pause()
                elif active and event.key == pygame.K_q:
                    self._open_quit_confirm()

        if self.state == GameState.START:
            self._update_start(events)

        elif self.state == GameState.PAUSED:
            pass  # Nothing updates while paused

        elif self.state == GameState.QUIT_CONFIRM:
            self._update_quit_confirm(events)

        elif self.state == GameState.READY:
            self._update_ready(dt)

        elif self.state == GameState.PLAYING:
            self._update_playing(dt, events)

        elif self.state == GameState.PACMAN_DEAD:
            self._update_pacman_dead(dt)

        elif self.state == GameState.LEVEL_CLEAR:
            self._update_level_clear(dt, events)

        elif self.state == GameState.GAME_OVER:
            self._update_game_over(events)

        # Update floating score display
        self._update_floating_scores(dt)

    # ── State handlers ────────────────────────────────────────────────────────

    def _update_start(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._start_game()

    def _update_quit_confirm(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_y, pygame.K_RETURN):
                    self.quit_requested = True
                elif event.key in (pygame.K_n, pygame.K_ESCAPE, pygame.K_p):
                    self.state = self.pre_pause_state or GameState.PLAYING

    def _update_ready(self, dt):
        self.ready_timer -= dt
        if self.ready_timer <= 0:
            self.state = GameState.PLAYING
            # Start siren when game begins
            self.sounds.update(dt, self.ghosts)

    def _update_playing(self, dt, events):
        # Handle freeze timer (game pauses briefly for eating animation)
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            return

        # Pac-Man input + movement
        self.pacman.handle_input(events)
        self.pacman.update(dt)

        # Eating dots and pellets
        eaten = self.pacman.eat()
        if eaten == DOT:
            self.score += DOT_SCORE
            self.dots_eaten += 1
            self._check_fruit_trigger()
            self._check_extra_life()
            self.sounds.play_chomp()
            self._add_floating_score(
                self.pacman.x, self.pacman.y - TILE_SIZE, str(DOT_SCORE), 0.4
            )
        elif eaten == PELLET:
            self.score += PELLET_SCORE
            self.dots_eaten += 1
            self._check_fruit_trigger()
            self._check_extra_life()
            self._trigger_frightened()
            self.sounds.play_power_pellet()
            self._add_floating_score(
                self.pacman.x, self.pacman.y - TILE_SIZE, str(PELLET_SCORE), 0.4
            )

        # Phase cycling (scatter/chase)
        self._update_phases(dt)

        # Ghost updates
        for g in self.ghosts:
            g.update(dt, self.pacman, self.blinky, self.dots_eaten, self.level)

        # Collision detection
        pc, pr = self.pacman.get_tile()
        for g in self.ghosts:
            gc, gr = g.get_tile()
            if gc == pc and gr == pr:
                if g.mode == GhostMode.FRIGHTENED:
                    # Eat ghost
                    g.mode = GhostMode.EATEN
                    g.prev_mode = GhostMode.SCATTER
                    pts = GHOST_EAT_BASE * self.ghost_eat_multiplier
                    self.score += pts
                    self.ghost_eat_multiplier = min(self.ghost_eat_multiplier * 2, 8)
                    self._check_extra_life()
                    self.sounds.play_ghost_eaten()
                    # Show floating score
                    self._add_floating_score(g.x, g.y - TILE_SIZE, str(pts), 1.2)
                    # Brief freeze
                    self.freeze_timer = 0.3

                elif g.mode in (GhostMode.SCATTER, GhostMode.CHASE):
                    # Pac-Man dies
                    self._pacman_die()
                    return

        # Fruit system
        self._update_fruit(dt)

        # Siren ambient sound
        self.sounds.update(dt, self.ghosts)

        if self.fruit_active and self.fruit_visible and self.fruit_tile:
            ftc, ftr = self.fruit_tile
            if pc == ftc and pr == ftr:
                fruit_data = self._get_fruit_data()
                fruit_name, fruit_points, _ = fruit_data
                self.score += fruit_points
                self._check_extra_life()
                self.sounds.play_fruit_bonus()
                self._add_floating_score(
                    self.pacman.x, self.pacman.y - TILE_SIZE, str(fruit_points), 1.5
                )
                self.fruit_active = False
                self.fruit_visible = False
                self.fruit_tile = None
                self.freeze_timer = FRUIT_EAT_FREEZE

        # Level clear
        if self.maze.dots_remaining == 0:
            self.state = GameState.LEVEL_CLEAR
            self.level_clear_timer = LEVEL_CLEAR_DURATION
            self.level_clear_flash = False
            self.level_clear_flash_timer = 0.0
            self.fruit_active = False
            self.fruit_visible = False
            self.sounds.play_level_clear()

    def _update_pacman_dead(self, dt):
        self.death_timer -= dt
        if self.death_timer <= 0:
            if self.pacman.lives > 0:
                self._start_round()
            else:
                self.state = GameState.GAME_OVER
                if self.score > self.high_score:
                    self.high_score = self.score

    def _update_level_clear(self, dt, events):
        self.level_clear_timer -= dt
        self.level_clear_flash_timer += dt
        if self.level_clear_flash_timer >= 0.2:
            self.level_clear_flash_timer = 0.0
            self.level_clear_flash = not self.level_clear_flash
        if self.level_clear_timer <= 0:
            self.level += 1
            self._start_level()

    def _update_game_over(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._restart()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _toggle_pause(self):
        if self.state == GameState.QUIT_CONFIRM:
            return
        if self.state == GameState.PAUSED:
            self.state = self.pre_pause_state
            self.pre_pause_state = None
        else:
            self.pre_pause_state = self.state
            self.state = GameState.PAUSED
            self.sounds.stop_siren()

    def _open_quit_confirm(self):
        if self.state != GameState.QUIT_CONFIRM:
            if self.state != GameState.PAUSED:
                self.pre_pause_state = self.state
            self.state = GameState.QUIT_CONFIRM
            self.sounds.stop_siren()

    def _start_game(self):
        self.score = 0
        self.level = 1
        self.lives = STARTING_LIVES
        self.extra_life_awarded = False
        self.pacman.lives = STARTING_LIVES
        self.sounds.play_game_start()
        self._start_level()

    def _restart(self):
        self.__init__()

    def _start_level(self):
        self.maze.reset()
        self.dots_eaten = 0
        self.ghost_eat_multiplier = 1
        self.phase_index = 0
        self.phase_timer = 0.0
        self.fruit_active = False
        self.fruit_visible = False
        self.fruit_timer = 0.0
        self.fruit_spawn_timer = 0.0
        self.fruit_tile = None
        self.fruit_triggered = [False, False]
        self.floating_scores = []
        self.freeze_timer = 0.0
        self._reset_positions()
        self.state = GameState.READY
        self.ready_timer = READY_DURATION

    def _start_round(self):
        """After a death: reset positions but keep maze state."""
        self.ghost_eat_multiplier = 1
        self.phase_index = 0
        self.phase_timer = 0.0
        self.floating_scores = []
        self.freeze_timer = 0.0
        self._reset_positions()
        self.state = GameState.READY
        self.ready_timer = READY_DURATION

    def _reset_positions(self):
        self.pacman.reset()
        for g in self.ghosts:
            g.reset()

    # ── Phase cycling ─────────────────────────────────────────────────────────

    def _update_phases(self, dt):
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

    # ── Fruit system ──────────────────────────────────────────────────────────

    def _get_fruit_data(self):
        """Get fruit data for the current level."""
        index = min(self.level - 1, len(FRUIT_TABLE) - 1)
        return FRUIT_TABLE[index]

    def _check_fruit_trigger(self):
        """Check if fruit should appear based on dots eaten."""
        if self.fruit_active:
            return

        if not self.fruit_triggered[0] and self.dots_eaten >= FRUIT_FIRST_TRIGGER:
            self.fruit_triggered[0] = True
            self._spawn_fruit()
        elif not self.fruit_triggered[1] and self.dots_eaten >= FRUIT_SECOND_TRIGGER:
            self.fruit_triggered[1] = True
            self._spawn_fruit()

    def _spawn_fruit(self):
        """Spawn the bonus fruit below the ghost house."""
        self.fruit_active = True
        self.fruit_visible = False
        self.fruit_spawn_timer = 0.0
        self.fruit_timer = FRUIT_DURATION
        # Fruit appears at (13, 17) — the corridor below the ghost house
        self.fruit_tile = (13, 17)

    def _update_fruit(self, dt):
        """Update fruit state."""
        if not self.fruit_active:
            return

        # Wait for spawn delay
        if not self.fruit_visible:
            self.fruit_spawn_timer += dt
            if self.fruit_spawn_timer >= FRUIT_APPEAR_DELAY:
                self.fruit_visible = True
            return

        # Fruit is visible and counting down
        self.fruit_timer -= dt
        if self.fruit_timer <= 0:
            self.fruit_active = False
            self.fruit_visible = False
            self.fruit_tile = None

    # ── Frightened mode ───────────────────────────────────────────────────────

    def _trigger_frightened(self):
        """Switch all ghosts to FRIGHTENED mode."""
        self.ghost_eat_multiplier = 1
        # Frightened duration decreases with level
        duration = max(
            FRIGHTENED_DURATION_MIN,
            FRIGHTENED_DURATION_BASE + (self.level - 1) * FRIGHTENED_DURATION_PER_LEVEL
        )
        for g in self.ghosts:
            g.set_frightened(duration)

    # ── Death ─────────────────────────────────────────────────────────────────

    def _pacman_die(self):
        self.pacman.alive = False
        self.pacman.lives -= 1
        self.lives = self.pacman.lives
        self.fruit_active = False
        self.fruit_visible = False
        self.state = GameState.PACMAN_DEAD
        self.death_timer = DEATH_DURATION
        self.sounds.play_death()

    # ── Scoring ───────────────────────────────────────────────────────────────

    def _check_extra_life(self):
        if not self.extra_life_awarded and self.score >= EXTRA_LIFE_SCORE:
            self.pacman.lives += 1
            self.lives = self.pacman.lives
            self.extra_life_awarded = True
            self.sounds.play_extra_life()

    def _add_floating_score(self, x, y, text, duration):
        """Show a floating score number at position (x, y)."""
        self.floating_scores.append({
            'x': x,
            'y': y,
            'text': text,
            'timer': duration,
            'duration': duration,
        })

    def _update_floating_scores(self, dt):
        """Update and fade floating score displays."""
        for fs in self.floating_scores[:]:
            fs['timer'] -= dt
            fs['y'] -= 0.3  # float upward slowly
            if fs['timer'] <= 0:
                self.floating_scores.remove(fs)