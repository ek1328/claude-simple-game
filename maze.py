import copy
from settings import *

# ── Authentic Pac-Man Maze Layout (28 cols x 31 rows) ──────────────────────────
# 0=WALL, 1=DOT, 2=EMPTY, 3=PELLET, 4=GHOST_HOUSE, 5=GHOST_DOOR
#
# This is a faithful reproduction of the original 1980 Namco arcade maze.
# The tunnel wraps at row 14 (the middle of the screen).
# 244 edibles total — 240 regular dots + 4 power pellets, at the original
# positions: rows 3 and 23, columns 1 and 26.
# The ghost house sits at rows 12-16, cols 10-17, with its door on TOP
# (row 12, cols 13-14) as in the arcade.

MAZE_LAYOUT = [
    # row 0  (top)
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    # row 1
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 2
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
    # row 3  (upper power pellets)
    [0,3,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,3,0],
    # row 4
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
    # row 5
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 6
    [0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0],
    # row 7
    [0,1,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,1,0],
    # row 8
    [0,1,1,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,1,1,0],
    # row 9
    [0,0,0,0,0,0,1,0,0,0,0,0,2,0,0,2,0,0,0,0,0,1,0,0,0,0,0,0],
    # row 10
    [2,2,2,2,2,0,1,0,0,0,0,0,2,0,0,2,0,0,0,0,0,1,0,2,2,2,2,2],
    # row 11 (corridor above ghost house)
    [2,2,2,2,2,0,1,0,0,2,2,2,2,2,2,2,2,2,2,0,0,1,0,2,2,2,2,2],
    # row 12 (ghost house top wall with door)
    [2,2,2,2,2,0,1,0,0,2,0,0,0,5,5,0,0,0,2,0,0,1,0,2,2,2,2,2],
    # row 13 (ghost house interior)
    [0,0,0,0,0,0,1,0,0,2,0,4,4,4,4,4,4,0,2,0,0,1,0,0,0,0,0,0],
    # row 14 (tunnel row / ghost house interior)
    [2,2,2,2,2,2,1,2,2,2,0,4,4,4,4,4,4,0,2,2,2,1,2,2,2,2,2,2],
    # row 15 (ghost house interior)
    [0,0,0,0,0,0,1,0,0,2,0,4,4,4,4,4,4,0,2,0,0,1,0,0,0,0,0,0],
    # row 16 (ghost house bottom wall)
    [2,2,2,2,2,0,1,0,0,2,0,0,0,0,0,0,0,0,2,0,0,1,0,2,2,2,2,2],
    # row 17 (corridor below ghost house)
    [2,2,2,2,2,0,1,0,0,2,2,2,2,2,2,2,2,2,2,0,0,1,0,2,2,2,2,2],
    # row 18
    [2,2,2,2,2,0,1,0,0,2,0,0,0,0,0,0,0,0,2,0,0,1,0,2,2,2,2,2],
    # row 19
    [0,0,0,0,0,0,1,0,0,2,0,0,0,0,0,0,0,0,2,0,0,1,0,0,0,0,0,0],
    # row 20
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 21
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
    # row 22
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
    # row 23 (lower power pellets, Pac-Man spawn between cols 13-14)
    [0,3,1,1,0,0,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,0,0,1,1,3,0],
    # row 24
    [0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0],
    # row 25
    [0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0],
    # row 26
    [0,1,1,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,1,1,0],
    # row 27
    [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
    # row 28
    [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
    # row 29
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 30 (bottom)
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Tunnel row index (Pac-Man and ghosts can wrap horizontally here)
TUNNEL_ROW = 14

# Ghost house entrance tile (where eaten ghosts head back to)
GHOST_HOUSE_ENTRANCE = (13, 11)

# Pac-Man spawn position (col, row) — between the two empty tiles on row 23
PACMAN_SPAWN = (13, 23)

# Ghost spawn positions (col, row)
GHOST_SPAWNS = {
    'blinky': (13, 11),    # Blinky starts right outside ghost house
    'pinky':  (13, 14),    # inside house, center
    'inky':   (11, 14),    # left of pinky
    'clyde':  (15, 14),    # right of pinky
}


class Maze:
    def __init__(self):
        self.reset()

    # ── Public API ─────────────────────────────────────────────────────────

    def reset(self):
        """Reset the maze to its initial layout."""
        self.grid = copy.deepcopy(MAZE_LAYOUT)
        self.total_dots = self._count_dots()
        self.dots_remaining = self.total_dots

    def _count_dots(self):
        """Count all dots and pellets in the maze."""
        return sum(1 for row in self.grid for cell in row if cell in (DOT, PELLET))

    def get_tile(self, col, row):
        """Get the tile type at (col, row). Returns EMPTY if out of bounds."""
        if 0 <= col < COLS and 0 <= row < ROWS:
            return self.grid[row][col]
        return EMPTY

    def set_tile(self, col, row, value):
        """Set the tile type at (col, row)."""
        if 0 <= col < COLS and 0 <= row < ROWS:
            self.grid[row][col] = value

    def is_wall(self, col, row):
        """Check if tile is a standard wall."""
        return self.get_tile(col, row) == WALL

    def is_wall_for_pacman(self, col, row):
        """Wall check for Pac-Man — also blocked by ghost house and door."""
        t = self.get_tile(col, row)
        return t in (WALL, GHOST_HOUSE, GHOST_DOOR)

    def is_wall_for_ghost(self, col, row, in_house=False, leaving=False):
        """
        Wall check for ghosts. While inside the house, ghosts can move
        through GHOST_HOUSE tiles. When leaving, they can pass through the door.
        """
        t = self.get_tile(col, row)
        if t == WALL:
            return True
        # Ghosts inside the house cannot pass through house walls
        # unless they are leaving
        if t == GHOST_HOUSE:
            return not (in_house or leaving)
        # Ghost door is only passable when leaving the house
        if t == GHOST_DOOR:
            return not (in_house or leaving)
        return False

    def is_tunnel_tile(self, col, row):
        """Check if the tile is in the tunnel row."""
        return row == TUNNEL_ROW

    def consume(self, col, row):
        """Eat a dot or pellet at (col, row). Returns the tile type eaten, or None."""
        t = self.get_tile(col, row)
        if t == DOT:
            self.set_tile(col, row, EMPTY)
            self.dots_remaining -= 1
            return DOT
        if t == PELLET:
            self.set_tile(col, row, EMPTY)
            self.dots_remaining -= 1
            return PELLET
        return None

    # ── Coordinate conversion ──────────────────────────────────────────────

    def tile_to_pixel(self, col, row):
        """Return the pixel center of a tile."""
        x = col * TILE_SIZE + TILE_SIZE // 2
        y = row * TILE_SIZE + TILE_SIZE // 2 + HUD_H
        return (x, y)

    def pixel_to_tile(self, px, py):
        """Return the tile (col, row) for a pixel position."""
        col = int(px) // TILE_SIZE
        row = int(py - HUD_H) // TILE_SIZE
        return (col, row)