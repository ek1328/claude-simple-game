import math
import pygame
from settings import *
from maze import PACMAN_SPAWN

# ── Authentic Pac-Man ──────────────────────────────────────────────────────────
# Key aspects of original Pac-Man movement:
# 1. Cornering: Pac-Man can pre-turn even if not perfectly aligned to center
# 2. Tunnel slowdown: Speed reduces in the tunnel
# 3. Mouth animation: continuous open/close cycle
# 4. Death animation: expanding black circle consuming Pac-Man

MOUTH_OPENING_RATE = 180.0   # degrees per second
MOUTH_MAX_ANGLE = 45.0
MOUTH_MIN_ANGLE = 2.0


class PacMan:
    def __init__(self, maze):
        self.maze = maze
        self.lives = STARTING_LIVES
        self.reset()

    def reset(self):
        """Reset Pac-Man to starting position and state."""
        spawn_col, spawn_row = PACMAN_SPAWN
        cx, cy = self.maze.tile_to_pixel(spawn_col, spawn_row)
        self.x = float(cx)
        self.y = float(cy)
        self.direction = (0, 0)           # current movement direction (dx, dy)
        self.next_direction = (-1, 0)     # buffered input (default: left)
        self.mouth_angle = MOUTH_MAX_ANGLE
        self.mouth_opening = True         # True=opening, False=closing
        self.alive = True
        self.death_scale = 1.0            # for death animation
        self.death_phase = 0              # 0-10 death animation frames

    # ── Input handling ─────────────────────────────────────────────────────

    def handle_input(self, events):
        """Process keyboard input and buffer the next direction."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.next_direction = (-1, 0)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.next_direction = (1, 0)
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.next_direction = (0, -1)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.next_direction = (0, 1)

    # ── Movement helpers ───────────────────────────────────────────────────

    def _current_tile(self):
        """Return the tile (col, row) Pac-Man is currently in."""
        return self.maze.pixel_to_tile(self.x, self.y)

    def _tile_center(self, col, row):
        """Return the pixel center of the given tile."""
        return self.maze.tile_to_pixel(col, row)

    def _at_tile_center(self):
        """Check if Pac-Man is close enough to the current tile's center."""
        col, row = self._current_tile()
        cx, cy = self._tile_center(col, row)
        threshold = PACMAN_SPEED * 0.6
        return abs(self.x - cx) <= threshold and abs(self.y - cy) <= threshold

    def _can_move(self, dx, dy):
        """
        Check if Pac-Man can move in direction (dx, dy).
        Returns True for tunnel wraps.
        """
        col, row = self._current_tile()
        next_col = col + dx
        next_row = row + dy
        # Tunnel wrap — always allowed
        if next_col < 0 or next_col >= COLS:
            return True
        return not self.maze.is_wall_for_pacman(next_col, next_row)

    def _get_speed(self):
        """Get current speed. Slower in tunnels."""
        if self.maze.is_tunnel_tile(*self._current_tile()):
            return PACMAN_SPEED_TUNNEL
        return PACMAN_SPEED

    # ── Update ─────────────────────────────────────────────────────────────

    def update(self, dt):
        """Update Pac-Man position and animation."""
        if not self.alive:
            return

        # Animate mouth — classic continuous open/close cycle
        if self.mouth_opening:
            self.mouth_angle += MOUTH_OPENING_RATE * dt
            if self.mouth_angle >= MOUTH_MAX_ANGLE:
                self.mouth_angle = MOUTH_MAX_ANGLE
                self.mouth_opening = False
        else:
            self.mouth_angle -= MOUTH_OPENING_RATE * dt
            if self.mouth_angle <= MOUTH_MIN_ANGLE:
                self.mouth_angle = MOUTH_MIN_ANGLE
                self.mouth_opening = True

        # At tile centers, try committing the buffered direction
        if self._at_tile_center():
            col, row = self._current_tile()
            cx, cy = self._tile_center(col, row)

            # Commit buffered direction if valid (ignore (0,0) which means "no input buffered")
            if self.next_direction != (0, 0) and self.next_direction != self.direction:
                ndx, ndy = self.next_direction
                if self._can_move(ndx, ndy):
                    self.direction = (ndx, ndy)
                    self.next_direction = (0, 0)

            # Snap to tile center for precise turning
            self.x = float(cx)
            self.y = float(cy)

        # If stopped, do nothing
        if self.direction == (0, 0):
            return

        dx, dy = self.direction
        speed = self._get_speed()

        # Calculate desired position
        new_x = self.x + dx * speed
        new_y = self.y + dy * speed

        # Handle tunnel wrap
        new_col = int(new_x) // TILE_SIZE
        if new_col < 0:
            self.x = COLS * TILE_SIZE - TILE_SIZE // 2
            self.y = new_y
            return
        elif new_col >= COLS:
            self.x = TILE_SIZE // 2
            self.y = new_y
            return

        # Check collision with upcoming tile
        col, row = self._current_tile()
        next_col = col + dx
        next_row = row + dy

        if self.maze.is_wall_for_pacman(next_col, next_row):
            # Glide back to tile center so the player can turn
            self._glide_to_center(col, row)
        else:
            self.x = new_x
            self.y = new_y

    def _glide_to_center(self, col, row):
        """Glide Pac-Man toward the current tile center at normal speed."""
        cx, cy = self._tile_center(col, row)
        speed = self._get_speed()

        if abs(self.x - cx) > speed:
            self.x += math.copysign(speed, cx - self.x)
        else:
            self.x = float(cx)

        if abs(self.y - cy) > speed:
            self.y += math.copysign(speed, cy - self.y)
        else:
            self.y = float(cy)

    # ── Gameplay ───────────────────────────────────────────────────────────

    def get_tile(self):
        """Get the tile coordinates Pac-Man occupies."""
        return self._current_tile()

    def eat(self):
        """Attempt to eat the current tile. Returns DOT, PELLET, or None."""
        col, row = self._current_tile()
        return self.maze.consume(col, row)

    # ── Drawing ────────────────────────────────────────────────────────────

    def draw(self, surface):
        """Draw Pac-Man at his current position."""
        if not self.alive:
            return

        cx = int(self.x)
        cy = int(self.y)
        radius = TILE_SIZE // 2 - 1

        # Heading angle: direction the mouth faces
        dx, dy = self.direction if self.direction != (0, 0) else (1, 0)
        heading_rad = math.atan2(-dy, dx)   # standard math angle (y up)

        mouth_half = math.radians(self.mouth_angle)

        # Draw solid yellow circle
        pygame.draw.circle(surface, YELLOW, (cx, cy), radius)

        # Cut out mouth with a black wedge
        if self.mouth_angle > 1:
            wedge = [(cx, cy)]
            steps = 10
            for i in range(steps + 1):
                frac = i / steps
                angle = (heading_rad + mouth_half) - frac * 2 * mouth_half
                px = cx + radius * math.cos(angle)
                py = cy - radius * math.sin(angle)
                wedge.append((px, py))
            if len(wedge) >= 3:
                pygame.draw.polygon(surface, BLACK, wedge)

    def draw_death_animation(self, surface, progress):
        """
        Draw Pac-Man's death animation.
        Progress goes from 0.0 to 1.0 — Pac-Man "pops" out of existence.
        """
        cx = int(self.x)
        cy = int(self.y)
        radius = TILE_SIZE // 2 - 1

        # Phase 1 (0.0-0.3): Normal Pac-Man but frozen
        # Phase 2 (0.3-0.7): Mouth opens wider and wider
        # Phase 3 (0.7-1.0): Pac-Man shrinks and disappears

        if progress < 0.3:
            pygame.draw.circle(surface, YELLOW, (cx, cy), radius)
            # Small mouth
            mouth_half = math.radians(15)
            dx, dy = self.direction if self.direction != (0, 0) else (1, 0)
            heading_rad = math.atan2(-dy, dx)
            wedge = [(cx, cy)]
            for i in range(6):
                frac = i / 5
                angle = (heading_rad + mouth_half) - frac * 2 * mouth_half
                px = cx + radius * math.cos(angle)
                py = cy - radius * math.sin(angle)
                wedge.append((px, py))
            pygame.draw.polygon(surface, BLACK, wedge)
        elif progress < 0.7:
            # Mouth widening
            t = (progress - 0.3) / 0.4
            mouth = math.radians(15 + t * 60)
            dx, dy = self.direction if self.direction != (0, 0) else (1, 0)
            heading_rad = math.atan2(-dy, dx)
            pygame.draw.circle(surface, YELLOW, (cx, cy), radius)
            wedge = [(cx, cy)]
            for i in range(10):
                frac = i / 9
                angle = (heading_rad + mouth) - frac * 2 * mouth
                px = cx + radius * math.cos(angle)
                py = cy - radius * math.sin(angle)
                wedge.append((px, py))
            pygame.draw.polygon(surface, BLACK, wedge)
        else:
            # Shrinking away
            t = (progress - 0.7) / 0.3
            shrink_radius = int(radius * (1.0 - t))
            if shrink_radius > 0:
                pygame.draw.circle(surface, YELLOW, (cx, cy), shrink_radius)