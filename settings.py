# Tile types
WALL = 0
DOT = 1
EMPTY = 2
PELLET = 3
GHOST_HOUSE = 4
GHOST_DOOR = 5

# Grid dimensions
TILE_SIZE = 20
COLS = 28
ROWS = 31

# Screen
SCREEN_W = COLS * TILE_SIZE          # 560
HUD_H = 40
SCREEN_H = ROWS * TILE_SIZE + HUD_H  # 660

FPS = 60

# Speeds (pixels per frame at 60 FPS)
PACMAN_SPEED = 1.52
GHOST_SPEED_NORMAL = 1.33
GHOST_SPEED_FRIGHTENED = 0.67
GHOST_SPEED_EATEN = 2.0

# Timings (seconds)
FRIGHTENED_DURATION = 8.0
FRIGHTENED_FLASH_START = 2.0   # start flashing this many seconds before end
READY_DURATION = 2.0
DEATH_DURATION = 1.8
LEVEL_CLEAR_DURATION = 2.5

# Phase schedule: (scatter_duration, chase_duration) pairs; last chase is infinite
PHASE_SCHEDULE = [
    ('scatter', 7),
    ('chase', 20),
    ('scatter', 7),
    ('chase', 20),
    ('scatter', 5),
    ('chase', 20),
    ('scatter', 5),
    ('chase', float('inf')),
]

# Score
DOT_SCORE = 10
PELLET_SCORE = 50
GHOST_EAT_BASE = 200
EXTRA_LIFE_SCORE = 10000
STARTING_LIVES = 3

# Ghost release (dots eaten thresholds)
GHOST_RELEASE_DOTS = {
    'blinky': 0,
    'pinky': 0,
    'inky': 30,
    'clyde': 60,
}

# Colors
BLACK  = (0,   0,   0)
DARK_BLUE = (0, 0, 140)
WALL_COLOR = (33, 33, 222)
WALL_BORDER = (0, 0, 100)
YELLOW = (255, 255,   0)
WHITE  = (255, 255, 255)
RED    = (220,  20,  20)
PINK   = (255, 184, 255)
CYAN   = (  0, 255, 255)
ORANGE = (255, 184,  82)
GHOST_FRIGHTENED_COLOR = (0, 0, 200)
GHOST_FLASH_COLOR = (255, 255, 255)
DOT_COLOR = (255, 222, 180)
PELLET_COLOR = (255, 222, 180)
