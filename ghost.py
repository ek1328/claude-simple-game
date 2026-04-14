import math
import random
import pygame
from settings import *
from maze import GHOST_HOUSE_ENTRANCE, GHOST_SPAWNS


class GhostMode:
    SCATTER = 'scatter'
    CHASE = 'chase'
    FRIGHTENED = 'frightened'
    EATEN = 'eaten'
    IN_HOUSE = 'in_house'
    LEAVING = 'leaving'


# Direction priority for tie-breaking: up, left, down, right
DIR_PRIORITY = [(0, -1), (-1, 0), (0, 1), (1, 0)]


class Ghost:
    """Base ghost class. Subclasses override get_chase_target()."""

    scatter_target = (0, 0)  # override in subclasses
    color = WHITE

    def __init__(self, name, maze):
        self.name = name
        self.maze = maze
        self.mode = GhostMode.IN_HOUSE
        self.prev_mode = GhostMode.SCATTER  # restored after frightened/eaten
        self.frightened_timer = 0.0
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.release_dots = GHOST_RELEASE_DOTS.get(name, 0)
        self.house_bounce_dir = -1  # bouncing inside house: -1=up, 1=down
        self.reset()

    def reset(self):
        spawn_col, spawn_row = GHOST_SPAWNS[self.name]
        cx, cy = self.maze.tile_to_pixel(spawn_col, spawn_row)
        self.x = float(cx)
        self.y = float(cy)
        self.direction = (0, -1)

        if self.name == 'blinky':
            self.mode = GhostMode.SCATTER
        else:
            self.mode = GhostMode.IN_HOUSE

        self.frightened_timer = 0.0
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.prev_mode = GhostMode.SCATTER
        self.house_bounce_dir = 1
        self.last_decision_tile = None

    def get_tile(self):
        col = int(self.x) // TILE_SIZE
        row = int(self.y - HUD_H) // TILE_SIZE
        return (col, row)

    def _tile_center(self, col, row):
        return self.maze.tile_to_pixel(col, row)

    def _at_tile_center(self):
        col, row = self.get_tile()
        cx, cy = self._tile_center(col, row)
        speed = max(GHOST_SPEED_NORMAL, GHOST_SPEED_EATEN)
        return abs(self.x - cx) <= speed + 1 and abs(self.y - cy) <= speed + 1

    def _snap_to_tile(self):
        col, row = self.get_tile()
        cx, cy = self._tile_center(col, row)
        self.x = float(cx)
        self.y = float(cy)

    def get_speed(self):
        if self.mode == GhostMode.FRIGHTENED:
            return GHOST_SPEED_FRIGHTENED
        if self.mode == GhostMode.EATEN:
            return GHOST_SPEED_EATEN
        return GHOST_SPEED_NORMAL

    def get_chase_target(self, pacman, blinky):
        """Override in subclasses. Returns (target_col, target_row)."""
        return pacman.get_tile()

    def _get_target(self, pacman, blinky):
        if self.mode == GhostMode.SCATTER:
            return self.scatter_target
        if self.mode == GhostMode.CHASE:
            return self.get_chase_target(pacman, blinky)
        if self.mode == GhostMode.EATEN:
            return GHOST_HOUSE_ENTRANCE
        return None  # not used for other modes

    def _legal_moves(self, col, row):
        """Return list of (dcol, drow) that are valid from (col, row), excluding reverse."""
        rev = (-self.direction[0], -self.direction[1])
        moves = []
        for d in DIR_PRIORITY:
            if d == rev:
                continue
            nc, nr = col + d[0], row + d[1]
            in_house = self.mode in (GhostMode.IN_HOUSE, GhostMode.LEAVING)
            if not self.maze.is_wall_for_ghost(nc, nr, in_house=in_house, leaving=(self.mode == GhostMode.LEAVING)):
                moves.append(d)
        return moves

    def _choose_direction(self, col, row, target):
        moves = self._legal_moves(col, row)
        if not moves:
            # Allow reverse as last resort
            rev = (-self.direction[0], -self.direction[1])
            nc, nr = col + rev[0], row + rev[1]
            in_house = self.mode in (GhostMode.IN_HOUSE, GhostMode.LEAVING)
            if not self.maze.is_wall_for_ghost(nc, nr, in_house=in_house):
                return rev
            return self.direction

        if self.mode == GhostMode.FRIGHTENED:
            return random.choice(moves)

        if target is None:
            return moves[0] if moves else self.direction

        tc, tr = target

        def dist(d):
            nc, nr = col + d[0], row + d[1]
            return (nc - tc) ** 2 + (nr - tr) ** 2

        best = min(moves, key=dist)
        return best

    def set_frightened(self):
        if self.mode not in (GhostMode.EATEN, GhostMode.IN_HOUSE, GhostMode.LEAVING):
            if self.mode != GhostMode.FRIGHTENED:
                self.prev_mode = self.mode
            self.mode = GhostMode.FRIGHTENED
        self.frightened_timer = FRIGHTENED_DURATION
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.last_decision_tile = None  # allow immediate direction reconsideration

    def end_frightened(self):
        if self.mode == GhostMode.FRIGHTENED:
            self.mode = self.prev_mode
            self.last_decision_tile = None

    def set_mode(self, new_mode):
        """Called by game for scatter/chase phase transitions."""
        if self.mode in (GhostMode.FRIGHTENED, GhostMode.EATEN,
                         GhostMode.IN_HOUSE, GhostMode.LEAVING):
            self.prev_mode = new_mode
        else:
            self.mode = new_mode
            # Reverse direction on mode change (classic behavior)
            self.direction = (-self.direction[0], -self.direction[1])
            self.last_decision_tile = None

    def update(self, dt, pacman, blinky, dots_eaten):
        # Handle release from ghost house
        if self.mode == GhostMode.IN_HOUSE:
            if dots_eaten >= self.release_dots:
                self.mode = GhostMode.LEAVING
            else:
                # Bounce vertically inside house
                self.y += self.house_bounce_dir * GHOST_SPEED_NORMAL
                spawn_col, spawn_row = GHOST_SPAWNS[self.name]
                center_cy = self.maze.tile_to_pixel(spawn_col, spawn_row)[1]
                if abs(self.y - center_cy) > TILE_SIZE * 0.6:
                    self.house_bounce_dir *= -1
                return

        if self.mode == GhostMode.LEAVING:
            # Move up toward entrance
            entrance_col, entrance_row = GHOST_HOUSE_ENTRANCE
            ex, ey = self.maze.tile_to_pixel(entrance_col, entrance_row)
            # First center horizontally
            if abs(self.x - ex) > 2:
                self.x += math.copysign(min(GHOST_SPEED_NORMAL, abs(self.x - ex)), ex - self.x)
            else:
                self.x = float(ex)
                self.y -= GHOST_SPEED_NORMAL
            if self.y <= ey:
                self.y = float(ey)
                self.mode = self.prev_mode
                self.direction = (-1, 0)
            return

        # Update frightened timer
        if self.mode == GhostMode.FRIGHTENED:
            self.frightened_timer -= dt
            self.flash_timer += dt
            if self.flash_timer >= 0.25:
                self.flash_timer = 0.0
                self.flash_toggle = not self.flash_toggle
            if self.frightened_timer <= 0:
                self.end_frightened()
                return

        # Check if eaten ghost reached home
        if self.mode == GhostMode.EATEN:
            entrance_col, entrance_row = GHOST_HOUSE_ENTRANCE
            ex, ey = self.maze.tile_to_pixel(entrance_col, entrance_row)
            if abs(self.x - ex) <= GHOST_SPEED_EATEN + 1 and abs(self.y - ey) <= GHOST_SPEED_EATEN + 1:
                self.x = float(ex)
                self.y = float(ey)
                self.mode = GhostMode.IN_HOUSE
                self.release_dots = 0  # re-release immediately
                return

        # Normal movement: decide direction once per tile center
        current_tile = self.get_tile()
        if self._at_tile_center() and current_tile != self.last_decision_tile:
            self._snap_to_tile()
            col, row = current_tile
            target = self._get_target(pacman, blinky)
            self.direction = self._choose_direction(col, row, target)
            self.last_decision_tile = current_tile

        # Move
        speed = self.get_speed()
        dx, dy = self.direction
        self.x += dx * speed
        self.y += dy * speed

        # Tunnel wrap
        if self.x < TILE_SIZE // 2:
            self.x = COLS * TILE_SIZE - TILE_SIZE // 2
        elif self.x > COLS * TILE_SIZE - TILE_SIZE // 2:
            self.x = TILE_SIZE // 2

    def draw(self, surface):
        cx = int(self.x)
        cy = int(self.y)
        radius = TILE_SIZE // 2 - 1

        # Determine body color
        if self.mode == GhostMode.FRIGHTENED:
            if self.frightened_timer <= FRIGHTENED_FLASH_START and self.flash_toggle:
                body_color = GHOST_FLASH_COLOR
            else:
                body_color = GHOST_FRIGHTENED_COLOR
        elif self.mode == GhostMode.EATEN:
            body_color = None  # eyes only
        else:
            body_color = self.color

        if body_color is not None:
            # Draw ghost body: circle top + rect bottom
            pygame.draw.circle(surface, body_color, (cx, cy - 2), radius)
            pygame.draw.rect(surface, body_color,
                             (cx - radius, cy - 2, radius * 2, radius + 2))

            # Draw 3 bumps on the bottom
            bump_r = radius // 3
            for i in range(3):
                bx = cx - radius + bump_r + i * 2 * bump_r
                by = cy - 2 + radius + 2
                pygame.draw.circle(surface, body_color, (bx, by), bump_r)

        # Draw eyes (always visible)
        dx, dy = self.direction
        eye_offsets = [(-radius // 2, -radius // 3), (radius // 2, -radius // 3)]
        for ox, oy in eye_offsets:
            ex = cx + ox
            ey = cy + oy - 2
            pygame.draw.circle(surface, WHITE, (ex, ey), radius // 3)
            # Pupil shifts in direction of movement
            px = ex + dx * (radius // 5)
            py = ey + dy * (radius // 5)
            pygame.draw.circle(surface, (0, 0, 180), (int(px), int(py)), radius // 5)


# ── Ghost subclasses ──────────────────────────────────────────────────────────

class Blinky(Ghost):
    color = RED
    scatter_target = (25, 0)

    def __init__(self, maze):
        super().__init__('blinky', maze)

    def get_chase_target(self, pacman, blinky):
        return pacman.get_tile()


class Pinky(Ghost):
    color = PINK
    scatter_target = (2, 0)

    def __init__(self, maze):
        super().__init__('pinky', maze)

    def get_chase_target(self, pacman, blinky):
        pc, pr = pacman.get_tile()
        dx, dy = pacman.direction if pacman.direction != (0, 0) else (0, -1)
        return (pc + dx * 4, pr + dy * 4)


class Inky(Ghost):
    color = CYAN
    scatter_target = (27, 30)

    def __init__(self, maze):
        super().__init__('inky', maze)

    def get_chase_target(self, pacman, blinky):
        pc, pr = pacman.get_tile()
        dx, dy = pacman.direction if pacman.direction != (0, 0) else (0, -1)
        pivot_c = pc + dx * 2
        pivot_r = pr + dy * 2
        bc, br = blinky.get_tile()
        # Vector from Blinky to pivot, doubled
        tc = pivot_c + (pivot_c - bc)
        tr = pivot_r + (pivot_r - br)
        return (tc, tr)


class Clyde(Ghost):
    color = ORANGE
    scatter_target = (0, 30)

    def __init__(self, maze):
        super().__init__('clyde', maze)

    def get_chase_target(self, pacman, blinky):
        pc, pr = pacman.get_tile()
        cc, cr = self.get_tile()
        dist = math.sqrt((cc - pc) ** 2 + (cr - pr) ** 2)
        if dist > 8:
            return (pc, pr)
        return self.scatter_target
