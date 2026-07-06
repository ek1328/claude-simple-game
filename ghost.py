import math
import random
import pygame
from settings import *
from maze import GHOST_HOUSE_ENTRANCE, GHOST_SPAWNS, TUNNEL_ROW

# ── Authentic Pac-Man Ghost AI ─────────────────────────────────────────────────
#
# The original arcade game uses four distinct ghost behaviors:
#
#   Blinky (red):   Shadow — directly targets Pac-Man's current tile.
#   Pinky (pink):   Speedy — targets 4 tiles ahead of Pac-Man.
#   Inky (cyan):    Bashful — uses vector from Blinky to 2 tiles ahead of Pac-Man.
#   Clyde (orange): Pokey — targets Pac-Man if far (>8 tiles), scatter if close.
#
# In SCATTER mode, each ghost targets a corner:
#   Blinky → top-right, Pinky → top-left, Inky → bottom-right, Clyde → bottom-left
#
# In FRIGHTENED mode, ghosts move randomly at half speed.
# In EATEN mode, ghosts race back to the ghost house at high speed.
#
# Key behaviors:
#   - Ghosts cannot reverse direction in scatter/chase (except on mode change).
#   - Direction priority for tie-breaking: up > left > down > right.
#   - Ghosts slow down in the tunnel.
#   - Ghost house door is impassible except when leaving/eaten.


class GhostMode:
    SCATTER = 'scatter'
    CHASE = 'chase'
    FRIGHTENED = 'frightened'
    EATEN = 'eaten'
    IN_HOUSE = 'in_house'
    LEAVING = 'leaving'


# Direction priority for tie-breaking (arcade: up > left > down > right)
DIR_PRIORITY = [(0, -1), (-1, 0), (0, 1), (1, 0)]


def _reverse_dir(d):
    """Return the opposite direction."""
    return (-d[0], -d[1])


class Ghost:
    """Base ghost class. Subclasses override scatter_target and get_chase_target()."""

    color = WHITE
    scatter_target = (0, 0)  # override in subclasses

    def __init__(self, name, maze):
        self.name = name
        self.maze = maze
        self.mode = GhostMode.IN_HOUSE
        self.prev_mode = GhostMode.SCATTER  # restored after frightened/eaten
        self.frightened_timer = 0.0
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.release_dots = GHOST_RELEASE_DOTS.get(name, 0)
        self.house_bounce_dir = -1  # up = -1, down = +1 inside house
        self.reset()

    def reset(self):
        """Reset ghost to spawn position and initial state."""
        spawn_col, spawn_row = GHOST_SPAWNS[self.name]
        cx, cy = self.maze.tile_to_pixel(spawn_col, spawn_row)
        self.x = float(cx)
        self.y = float(cy)
        self.direction = (0, -1)
        self.last_decision_tile = None
        self.speed_multiplier = 1.0

        if self.name == 'blinky':
            self.mode = GhostMode.SCATTER
        else:
            self.mode = GhostMode.IN_HOUSE

        self.frightened_timer = 0.0
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.prev_mode = GhostMode.SCATTER
        self.house_bounce_dir = 1  # start bouncing downward

    # ── Position helpers ───────────────────────────────────────────────────

    def get_tile(self):
        """Return (col, row) tile coordinates for the ghost."""
        col = int(self.x) // TILE_SIZE
        row = int(self.y - HUD_H) // TILE_SIZE
        return (col, row)

    def _tile_center(self, col, row):
        """Return pixel center of a tile."""
        return self.maze.tile_to_pixel(col, row)

    def _at_tile_center(self):
        """Check if ghost is near the center of its current tile."""
        col, row = self.get_tile()
        cx, cy = self._tile_center(col, row)
        speed = max(GHOST_SPEED_NORMAL, GHOST_SPEED_EATEN)
        threshold = speed + 1
        return abs(self.x - cx) <= threshold and abs(self.y - cy) <= threshold

    def _snap_to_tile(self):
        """Snap ghost position to current tile center."""
        col, row = self.get_tile()
        cx, cy = self._tile_center(col, row)
        self.x = float(cx)
        self.y = float(cy)

    def _is_in_tunnel(self):
        """Check if ghost is in the tunnel row."""
        return self.get_tile()[1] == TUNNEL_ROW

    # ── Speed ──────────────────────────────────────────────────────────────

    def get_speed(self):
        """Get current speed based on mode and tunnel status."""
        if self.mode == GhostMode.EATEN:
            return GHOST_SPEED_EATEN

        base_speed = GHOST_SPEED_NORMAL
        if self.mode == GhostMode.FRIGHTENED:
            base_speed = GHOST_SPEED_FRIGHTENED

        # Tunnel slowdown
        if self._is_in_tunnel():
            base_speed = min(base_speed, GHOST_SPEED_TUNNEL)

        return base_speed * self.speed_multiplier

    # ── Chase targeting (override in subclasses) ───────────────────────────

    def get_chase_target(self, pacman, blinky):
        """Return the chase target tile. Override in subclasses."""
        return pacman.get_tile()

    # ── Target selection ───────────────────────────────────────────────────

    def _get_target(self, pacman, blinky):
        """Get the current target tile based on ghost mode."""
        if self.mode == GhostMode.SCATTER:
            return self.scatter_target
        if self.mode == GhostMode.CHASE:
            return self.get_chase_target(pacman, blinky)
        if self.mode == GhostMode.EATEN:
            return GHOST_HOUSE_ENTRANCE
        return None

    # ── Movement logic ─────────────────────────────────────────────────────

    def _legal_moves(self, col, row):
        """
        Return list of valid (dcol, drow) from (col, row).
        Excludes reverse direction unless it's the only option.
        """
        rev = _reverse_dir(self.direction)
        in_house = self.mode in (GhostMode.IN_HOUSE, GhostMode.LEAVING)
        leaving = self.mode == GhostMode.LEAVING
        moves = []

        for d in DIR_PRIORITY:
            nc, nr = col + d[0], row + d[1]

            # Tunnel wrapping is always allowed
            if nc < 0 or nc >= COLS:
                if d != rev:
                    moves.append(d)
                continue

            if not self.maze.is_wall_for_ghost(nc, nr, in_house=in_house, leaving=leaving):
                moves.append(d)

        # Don't reverse unless forced
        filtered = [m for m in moves if m != rev]
        if filtered:
            return filtered

        # If reverse is the only option, check if it's valid
        if rev in moves:
            return [rev]

        return []

    def _choose_direction(self, col, row, target):
        """
        Choose the best direction to move toward the target.
        In FRIGHTENED mode, chooses randomly.
        Uses direction priority (up > left > down > right) for tie-breaking.
        """
        moves = self._legal_moves(col, row)
        if not moves:
            # Edge case: keep current direction
            return self.direction

        # Frightened: random movement (but no reversing)
        if self.mode == GhostMode.FRIGHTENED:
            # 50% chance to intentionally turn at each junction for more
            # unpredictable behavior
            return random.choice(moves)

        # Scatter/Chase/Eaten: target-based movement
        if target is None:
            return moves[0]

        tc, tr = target

        def dist(d):
            """Squared Euclidean distance from the new tile to target."""
            nc, nr = col + d[0], row + d[1]
            return (nc - tc) ** 2 + (nr - tr) ** 2

        # Find moves with minimum distance to target
        min_dist = min(dist(d) for d in moves)
        best_moves = [d for d in moves if dist(d) == min_dist]

        # Use direction priority for tie-breaking
        for priority_dir in DIR_PRIORITY:
            if priority_dir in best_moves:
                return priority_dir

        return best_moves[0]

    # ── Mode control ───────────────────────────────────────────────────────

    def set_frightened(self, duration):
        """Switch to FRIGHTENED mode."""
        if self.mode not in (GhostMode.EATEN, GhostMode.IN_HOUSE, GhostMode.LEAVING):
            if self.mode != GhostMode.FRIGHTENED:
                self.prev_mode = self.mode
            self.mode = GhostMode.FRIGHTENED

        self.frightened_timer = duration
        self.flash_toggle = False
        self.flash_timer = 0.0
        self.last_decision_tile = None

        # Reverse direction upon becoming frightened
        self.direction = _reverse_dir(self.direction)

    def end_frightened(self):
        """End FRIGHTENED mode and restore previous mode."""
        if self.mode == GhostMode.FRIGHTENED:
            self.mode = self.prev_mode
            self.last_decision_tile = None

    def set_mode(self, new_mode):
        """
        Called when scatter/chase phase transitions.
        Ghosts reverse direction on mode change (classic behavior).
        """
        if self.mode in (GhostMode.FRIGHTENED, GhostMode.EATEN,
                         GhostMode.IN_HOUSE, GhostMode.LEAVING):
            # Don't change mode, just remember the intended one
            self.prev_mode = new_mode
        else:
            self.mode = new_mode
            # Reverse direction on scatter/chase mode change
            self.direction = _reverse_dir(self.direction)
            self.last_decision_tile = None

    # ── Update ─────────────────────────────────────────────────────────────

    def update(self, dt, pacman, blinky, dots_eaten, level):
        """Update ghost position and state."""

        # ── IN_HOUSE: wait for release threshold ────────────────────────
        if self.mode == GhostMode.IN_HOUSE:
            if dots_eaten >= self.release_dots:
                self.mode = GhostMode.LEAVING
            else:
                # Bounce vertically inside house (classic behavior)
                self.y += self.house_bounce_dir * GHOST_SPEED_NORMAL
                spawn_col, spawn_row = GHOST_SPAWNS[self.name]
                center_y = self.maze.tile_to_pixel(spawn_col, spawn_row)[1]
                bounce_range = TILE_SIZE * 0.6
                if self.y > center_y + bounce_range:
                    self.y = center_y + bounce_range
                    self.house_bounce_dir = -1
                elif self.y < center_y - bounce_range:
                    self.y = center_y - bounce_range
                    self.house_bounce_dir = 1
            return

        # ── LEAVING: move out of ghost house ─────────────────────────────
        if self.mode == GhostMode.LEAVING:
            entrance_col, entrance_row = GHOST_HOUSE_ENTRANCE
            ex, ey = self.maze.tile_to_pixel(entrance_col, entrance_row)

            # First center horizontally above the entrance
            if abs(self.x - ex) > 2:
                self.x += math.copysign(min(GHOST_SPEED_NORMAL, abs(self.x - ex)), ex - self.x)
            else:
                self.x = float(ex)
                self.y -= GHOST_SPEED_NORMAL

            # Reached entrance position
            if self.y <= ey:
                self.y = float(ey)
                self.mode = self.prev_mode
                self.direction = (-1, 0)  # head left out of house
                self.last_decision_tile = None
            return

        # ── FRIGHTENED timer ────────────────────────────────────────────
        if self.mode == GhostMode.FRIGHTENED:
            self.frightened_timer -= dt

            # Flash faster as time runs out
            flash_interval = 0.35
            if self.frightened_timer <= 1.5:
                flash_interval = 0.15
            elif self.frightened_timer <= 3.0:
                flash_interval = 0.25

            self.flash_timer += dt
            if self.flash_timer >= flash_interval:
                self.flash_timer = 0.0
                self.flash_toggle = not self.flash_toggle

            if self.frightened_timer <= 0:
                self.end_frightened()
            # Frightened ghosts keep wandering — fall through to movement

        # ── EATEN: check for arrival at the ghost house entrance ────────
        if self.mode == GhostMode.EATEN:
            entrance_col, entrance_row = GHOST_HOUSE_ENTRANCE
            ex, ey = self.maze.tile_to_pixel(entrance_col, entrance_row)

            if abs(self.x - ex) <= GHOST_SPEED_EATEN + 2 and abs(self.y - ey) <= GHOST_SPEED_EATEN + 2:
                self.x = float(ex)
                self.y = float(ey)
                self.mode = GhostMode.LEAVING
                self.prev_mode = GhostMode.SCATTER
                self.last_decision_tile = None
                return
            # Not home yet — fall through and race toward the entrance

        # ── Normal movement (SCATTER / CHASE / FRIGHTENED / EATEN) ─────────
        current_tile = self.get_tile()

        # Only change direction at tile centers (one decision per tile)
        if self._at_tile_center() and current_tile != self.last_decision_tile:
            self._snap_to_tile()
            col, row = current_tile
            target = self._get_target(pacman, blinky)
            self.direction = self._choose_direction(col, row, target)
            self.last_decision_tile = current_tile

        # Move forward
        speed = self.get_speed()
        dx, dy = self.direction
        self.x += dx * speed
        self.y += dy * speed

        # Tunnel wrap
        if self.x < TILE_SIZE // 2:
            self.x = COLS * TILE_SIZE - TILE_SIZE // 2
        elif self.x > COLS * TILE_SIZE - TILE_SIZE // 2:
            self.x = TILE_SIZE // 2

    # ── Drawing ────────────────────────────────────────────────────────────

    def draw(self, surface):
        """Draw the ghost with authentic arcade-style appearance."""
        cx = int(self.x)
        cy = int(self.y)
        radius = TILE_SIZE // 2 - 1

        # Determine body and eye color based on mode
        if self.mode == GhostMode.EATEN:
            body_color = None  # eyes only
            eye_fill = EMPTY
        elif self.mode == GhostMode.FRIGHTENED:
            # Authentic: frightened ghosts alternate between dark blue and
            # white when about to expire
            if self.frightened_timer <= 2.0 and self.flash_toggle:
                body_color = GHOST_FLASH_COLOR
                eye_fill = RED  # red eyes when flashing white
            else:
                body_color = GHOST_FRIGHTENED_COLOR
                eye_fill = None  # normal frightened face
        else:
            body_color = self.color
            eye_fill = None

        if body_color is not None:
            self._draw_ghost_body(surface, cx, cy, radius, body_color)

        # Draw eyes
        if self.mode == GhostMode.FRIGHTENED and self.frightened_timer > 2.0:
            self._draw_frightened_face(surface, cx, cy, radius)
        else:
            self._draw_ghost_eyes(surface, cx, cy, radius)

        # EATEN ghosts are just eyes
        if self.mode == GhostMode.EATEN:
            self._draw_eaten_eyes(surface, cx, cy, radius)

    def _draw_ghost_body(self, surface, cx, cy, radius, body_color):
        """Draw the classic ghost body with scalloped bottom."""
        # Body: circle on top + rectangle
        pygame.draw.circle(surface, body_color, (cx, cy - 2), radius)
        body_rect = pygame.Rect(cx - radius, cy - 2, radius * 2, radius + 2)
        pygame.draw.rect(surface, body_color, body_rect)

        # Scalloped bottom (3 bumps)
        bump_r = radius // 3
        num_bumps = 3
        bump_spacing = (radius * 2) // num_bumps
        for i in range(num_bumps):
            bx = cx - radius + bump_spacing // 2 + i * bump_spacing
            by = cy - 2 + radius + 2
            # Alternating up/down bumps for the authentic look
            if i == 1:
                by -= bump_r // 2  # middle bump slightly higher
            pygame.draw.circle(surface, body_color, (bx, by), bump_r)

        # Fill gaps between bumps
        for i in range(num_bumps - 1):
            x1 = cx - radius + bump_spacing // 2 + i * bump_spacing + bump_r
            x2 = cx - radius + bump_spacing // 2 + (i + 1) * bump_spacing - bump_r
            y = cy - 2 + radius + 2
            pygame.draw.line(surface, body_color, (x1, y), (x2, y), bump_r * 2)

    def _draw_ghost_eyes(self, surface, cx, cy, radius):
        """Draw white eyes with pupils that follow the movement direction."""
        dx, dy = self.direction if self.direction != (0, 0) else (0, -1)

        eye_offset_x = radius // 2
        eye_offset_y = radius // 3
        eye_radius = radius // 3

        for ox in (-eye_offset_x, eye_offset_x):
            ex = cx + ox
            ey = cy - 2 - eye_offset_y

            # White of eye
            pygame.draw.circle(surface, WHITE, (ex, ey), eye_radius)

            # Blue pupil
            pupil_offset_x = dx * (eye_radius // 2)
            pupil_offset_y = dy * (eye_radius // 2)
            pupil_radius = max(2, eye_radius // 2)
            pygame.draw.circle(surface, DARK_BLUE,
                               (ex + pupil_offset_x, ey + pupil_offset_y),
                               pupil_radius)

    def _draw_frightened_face(self, surface, cx, cy, radius):
        """Draw the wavy mouth and dot eyes of a frightened ghost."""
        # Small dot eyes
        eye_y = cy - 2 - radius // 3
        for ex in (cx - radius // 2, cx + radius // 2):
            pygame.draw.circle(surface, WHITE, (ex, eye_y), 2)

    def _draw_eaten_eyes(self, surface, cx, cy, radius):
        """Draw only the eyes for eaten ghosts (floating eyes)."""
        dx, dy = self.direction if self.direction != (0, 0) else (0, -1)

        eye_y = cy - 2 - radius // 3
        eye_radius = radius // 3

        for ox in (-radius // 2, radius // 2):
            ex = cx + ox
            # White of eye
            pygame.draw.circle(surface, WHITE, (ex, eye_y), eye_radius)
            # Blue pupil
            pupil_x = ex + dx * (eye_radius // 2)
            pupil_y = eye_y + dy * (eye_radius // 2)
            pygame.draw.circle(surface, DARK_BLUE,
                               (pupil_x, pupil_y), max(2, eye_radius // 2))


# ── Ghost subclasses (authentic arcade behaviors) ─────────────────────────────


class Blinky(Ghost):
    """
    Shadow (Red) — Oikake (追いかけ) "Chaser"
    Scatter target: top-right corner
    Chase target: Pac-Man's current tile (direct pursuit)
    Blinky becomes faster (Cruz Elroy) after a certain number of dots eaten.
    """
    color = RED
    scatter_target = (25, 0)

    def __init__(self, maze):
        super().__init__('blinky', maze)

    def get_chase_target(self, pacman, blinky):
        return pacman.get_tile()


class Pinky(Ghost):
    """
    Speedy (Pink) — Machibuse (待ち伏せ) "Ambusher"
    Scatter target: top-left corner
    Chase target: 4 tiles ahead of Pac-Man
    Original bug: when Pac-Man faces up, Pinky targets 4 up AND 4 left.
    """
    color = PINK
    scatter_target = (2, 0)

    def __init__(self, maze):
        super().__init__('pinky', maze)

    def get_chase_target(self, pacman, blinky):
        pc, pr = pacman.get_tile()
        dx, dy = pacman.direction if pacman.direction != (0, 0) else (0, -1)
        # Original arcade bug: when facing up, also shifts 4 left
        if dy == -1:  # facing up
            return (pc + dx * 4 - 4, pr + dy * 4)
        return (pc + dx * 4, pr + dy * 4)


class Inky(Ghost):
    """
    Bashful (Cyan) — Kimagure (気まぐれ) "Whimsical"
    Scatter target: bottom-right corner
    Chase target: vector from Blinky to 2 tiles ahead of Pac-Man, doubled.
    """
    color = CYAN
    scatter_target = (27, 30)

    def __init__(self, maze):
        super().__init__('inky', maze)

    def get_chase_target(self, pacman, blinky):
        pc, pr = pacman.get_tile()
        dx, dy = pacman.direction if pacman.direction != (0, 0) else (0, -1)

        # Pivot: 2 tiles ahead of Pac-Man
        pivot_c = pc + dx * 2
        pivot_r = pr + dy * 2

        # Vector from Blinky to pivot, then double it
        bc, br = blinky.get_tile()
        tc = pivot_c + (pivot_c - bc)
        tr = pivot_r + (pivot_r - br)
        return (tc, tr)


class Clyde(Ghost):
    """
    Pokey (Orange) — Otoboke (お惚け) "Feign Ignorance"
    Scatter target: bottom-left corner
    Chase target: Pac-Man if distance > 8 tiles, otherwise scatter target.
    """
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