import math
import pygame
from settings import *
from maze import PACMAN_SPAWN, TUNNEL_ROWS


class PacMan:
    def __init__(self, maze):
        self.maze = maze
        self.lives = STARTING_LIVES
        self.reset()

    def reset(self):
        spawn_col, spawn_row = PACMAN_SPAWN
        cx, cy = self.maze.tile_to_pixel(spawn_col, spawn_row)
        self.x = float(cx)
        self.y = float(cy)
        self.direction = (0, 0)        # current movement direction (dx, dy) in tile units
        self.next_direction = (-1, 0)  # buffered input
        self.mouth_angle = 30.0        # mouth opening half-angle in degrees
        self.mouth_opening = True
        self.mouth_timer = 0.0
        self.alive = True

    def handle_input(self, events):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.next_direction = (-1, 0)
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.next_direction = (1, 0)
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            self.next_direction = (0, -1)
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.next_direction = (0, 1)

    def _current_tile(self):
        return self.maze.pixel_to_tile(self.x, self.y)

    def _at_tile_center(self):
        col, row = self._current_tile()
        cx, cy = self.maze.tile_to_pixel(col, row)
        threshold = PACMAN_SPEED + 1
        return abs(self.x - cx) <= threshold and abs(self.y - cy) <= threshold

    def _can_move(self, dx, dy):
        col, row = self._current_tile()
        next_col = col + dx
        next_row = row + dy
        if next_col < 0 or next_col >= COLS:
            return True  # tunnel wrap
        return not self.maze.is_wall_for_pacman(next_col, next_row)

    def update(self, dt):
        if not self.alive:
            return

        # Animate mouth
        self.mouth_timer += dt
        half_cycle = 0.12  # seconds per half-cycle
        if self.mouth_timer >= half_cycle:
            self.mouth_timer = 0.0
            self.mouth_opening = not self.mouth_opening
        if self.mouth_opening:
            self.mouth_angle = min(42.0, self.mouth_angle + 8.0)
        else:
            self.mouth_angle = max(4.0, self.mouth_angle - 8.0)

        # Try committing buffered direction at tile centers
        if self._at_tile_center() and self.next_direction not in ((0, 0), self.direction):
            if self._can_move(*self.next_direction):
                self.direction = self.next_direction
                self.next_direction = (0, 0)
                # Snap to tile center
                col, row = self._current_tile()
                cx, cy = self.maze.tile_to_pixel(col, row)
                self.x = float(cx)
                self.y = float(cy)

        if self.direction == (0, 0):
            return

        dx, dy = self.direction
        pixels = PACMAN_SPEED
        col, row = self._current_tile()
        next_col = col + dx
        next_row = row + dy

        # Tunnel wrap
        if next_col < 0 or next_col >= COLS:
            self.x += dx * pixels
            self.y += dy * pixels
            if self.x < TILE_SIZE // 2:
                self.x = COLS * TILE_SIZE - TILE_SIZE // 2
            elif self.x > COLS * TILE_SIZE - TILE_SIZE // 2:
                self.x = TILE_SIZE // 2
            return

        if self.maze.is_wall_for_pacman(next_col, next_row):
            if self._at_tile_center():
                cx, cy = self.maze.tile_to_pixel(col, row)
                self.x = float(cx)
                self.y = float(cy)
        else:
            self.x += dx * pixels
            self.y += dy * pixels

    def get_tile(self):
        return self._current_tile()

    def eat(self):
        """Attempt to eat the current tile. Returns DOT, PELLET, or None."""
        col, row = self._current_tile()
        return self.maze.consume(col, row)

    def draw(self, surface):
        if not self.alive:
            return

        cx = int(self.x)
        cy = int(self.y)
        radius = TILE_SIZE // 2 - 1

        # Heading angle: direction the mouth faces
        dx, dy = self.direction if self.direction != (0, 0) else (1, 0)
        # In screen space, y increases downward, so flip dy for math
        heading_rad = math.atan2(-dy, dx)  # standard math angle

        mouth_half = math.radians(self.mouth_angle)

        # Draw full yellow circle
        pygame.draw.circle(surface, YELLOW, (cx, cy), radius)

        # Cut out mouth by drawing a black triangle (wedge)
        if self.mouth_angle > 1:
            steps = 12
            wedge = [(cx, cy)]
            # From upper jaw to lower jaw going through the mouth opening direction
            for i in range(steps + 1):
                frac = i / steps
                angle = (heading_rad + mouth_half) - frac * 2 * mouth_half
                px = cx + radius * math.cos(angle)
                py = cy - radius * math.sin(angle)  # flip y back for screen
                wedge.append((px, py))
            if len(wedge) >= 3:
                pygame.draw.polygon(surface, BLACK, wedge)
