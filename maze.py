import copy
from settings import *

# Classic Pac-Man maze layout (28 cols x 31 rows)
# 0=WALL, 1=DOT, 2=EMPTY, 3=PELLET, 4=GHOST_HOUSE, 5=GHOST_DOOR
MAZE_LAYOUT = [
    # row 0
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    # row 1
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 2
    [0,3,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,3,0],
    # row 3
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
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
    [0,0,0,0,0,0,1,0,0,0,0,0,2,0,0,2,0,0,0,0,0,1,0,0,0,0,0,0],
    # row 11
    [0,0,0,0,0,0,1,0,0,2,2,2,2,2,2,2,2,2,2,0,0,1,0,0,0,0,0,0],
    # row 12
    [0,0,0,0,0,0,1,0,0,2,0,0,0,4,4,0,0,0,2,0,0,1,0,0,0,0,0,0],
    # row 13 (tunnel row)
    [2,2,2,2,2,2,1,0,0,2,0,4,4,4,4,4,4,0,2,0,0,1,2,2,2,2,2,2],
    # row 14 (ghost house interior)
    [2,2,2,2,2,2,1,0,0,2,0,4,4,4,4,4,4,0,2,0,0,1,2,2,2,2,2,2],
    # row 15 (ghost door row)
    [0,0,0,0,0,0,1,0,0,2,0,0,5,0,0,5,0,0,2,0,0,1,0,0,0,0,0,0],
    # row 16
    [0,0,0,0,0,0,1,0,0,2,2,2,2,2,2,2,2,2,2,0,0,1,0,0,0,0,0,0],
    # row 17
    [0,0,0,0,0,0,1,0,0,2,0,0,0,0,0,0,0,0,2,0,0,1,0,0,0,0,0,0],
    # row 18
    [0,0,0,0,0,0,1,0,0,2,0,0,0,0,0,0,0,0,2,0,0,1,0,0,0,0,0,0],
    # row 19
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 20
    [0,1,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,1,0],
    # row 21
    [0,3,0,0,0,0,1,0,0,0,0,0,1,0,0,1,0,0,0,0,0,1,0,0,0,0,3,0],
    # row 22
    [0,1,1,1,0,0,1,1,1,1,1,1,1,2,2,1,1,1,1,1,1,1,0,0,1,1,1,0],
    # row 23
    [0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0],
    # row 24
    [0,0,0,1,0,0,1,0,0,1,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,0,0,0],
    # row 25
    [0,1,1,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,0,0,1,1,1,1,1,1,0],
    # row 26
    [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
    # row 27
    [0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0],
    # row 28
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    # row 29
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    # row 30
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
]

# Tunnel rows (Pac-Man and ghosts can wrap horizontally)
TUNNEL_ROWS = {13, 14}

# Ghost house entrance tile (where eaten ghosts head back to)
GHOST_HOUSE_ENTRANCE = (13, 11)

# Pac-Man spawn
PACMAN_SPAWN = (13, 22)  # EMPTY tile with left/right corridors

# Ghost spawns (col, row) and initial direction
GHOST_SPAWNS = {
    'blinky': (13, 11),   # starts outside the house
    'pinky':  (13, 14),
    'inky':   (11, 14),
    'clyde':  (15, 14),
}


class Maze:
    def __init__(self):
        self.reset()

    def reset(self):
        self.grid = copy.deepcopy(MAZE_LAYOUT)
        self.total_dots = self._count_dots()
        self.dots_remaining = self.total_dots

    def _count_dots(self):
        count = 0
        for row in self.grid:
            for cell in row:
                if cell in (DOT, PELLET):
                    count += 1
        return count

    def get_tile(self, col, row):
        if 0 <= col < COLS and 0 <= row < ROWS:
            return self.grid[row][col]
        return EMPTY

    def set_tile(self, col, row, value):
        if 0 <= col < COLS and 0 <= row < ROWS:
            self.grid[row][col] = value

    def is_wall(self, col, row):
        return self.get_tile(col, row) == WALL

    def is_wall_for_pacman(self, col, row):
        t = self.get_tile(col, row)
        return t in (WALL, GHOST_HOUSE, GHOST_DOOR)

    def is_wall_for_ghost(self, col, row, in_house=False, leaving=False):
        t = self.get_tile(col, row)
        if t == WALL:
            return True
        if t == GHOST_HOUSE:
            return not (in_house or leaving)
        if t == GHOST_DOOR:
            return not (in_house or leaving)
        return False

    def consume(self, col, row):
        """Eat a dot or pellet. Returns tile type eaten, or None."""
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
