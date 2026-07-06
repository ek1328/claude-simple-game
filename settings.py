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
SCREEN_W = COLS * TILE_SIZE  # 560
HUD_H = 40
SCREEN_H = ROWS * TILE_SIZE + HUD_H  # 660

FPS = 60

# Speeds (pixels per frame at 60 FPS)
# Ghost normal = varies 75-80% of Pac-Man
PACMAN_SPEED = 1.56
PACMAN_SPEED_TUNNEL = 1.56
GHOST_SPEED_NORMAL = 1.44
GHOST_SPEED_TUNNEL = 1.0  # ghosts slow down in tunnels
GHOST_SPEED_FRIGHTENED = 0.74
GHOST_SPEED_EATEN = 1.87

# Level-based speed multipliers (makes game harder)
PACMAN_SPEED_PER_LEVEL = 0.01  # pacman speed stays constant
GHOST_SPEED_PER_LEVEL = 0.02  # ghosts get slightly faster each level

# Timings (seconds)
FRIGHTENED_DURATION_BASE = 10.0  # level 1
FRIGHTENED_DURATION_MIN = 1.0
FRIGHTENED_DURATION_PER_LEVEL = -0.5
FRIGHTENED_FLASH_START = 2.0  # start flashing this many seconds before end
READY_DURATION = 2.0
DEATH_DURATION = 1.8
LEVEL_CLEAR_DURATION = 2.5
FRUIT_APPEAR_DELAY = 2.0  # delay before fruit appears after enough dots
FRUIT_DURATION = 15.0  # fruit stays for 10 seconds
FRUIT_EAT_FREEZE = 1.0  # freeze after eating fruit to show score

# Phase schedule: (mode, duration_seconds) — last chase is infinite
PHASE_SCHEDULE = [
    ("scatter", 7),
    ("chase", 20),
    ("scatter", 7),
    ("chase", 20),
    ("scatter", 5),
    ("chase", 20),
    ("scatter", 5),
    ("chase", float("inf")),
]

# Score
DOT_SCORE = 10
PELLET_SCORE = 50
GHOST_EAT_BASE = 200
EXTRA_LIFE_SCORE = 10000
STARTING_LIVES = 3

# Fruit data: (name, points, color)
# Appears when 70 dots eaten (first fruit) and 170 dots eaten (second fruit)
FRUIT_TABLE = [
    ("Cherry", 100, (255, 0, 0)),  # level 1
    ("Strawberry", 300, (255, 50, 50)),  # level 2
    ("Orange", 500, (255, 140, 0)),  # levels 3-4
    ("Orange", 500, (255, 140, 0)),
    ("Apple", 700, (255, 0, 0)),  # levels 5-6
    ("Apple", 700, (255, 0, 0)),
    ("Melon", 1000, (0, 200, 0)),  # levels 7-8
    ("Melon", 1000, (0, 200, 0)),
    ("Galaxian", 2000, (0, 200, 255)),  # levels 9-10
    ("Galaxian", 2000, (0, 200, 255)),
    ("Bell", 3000, (255, 255, 0)),  # levels 11-12
    ("Bell", 3000, (255, 255, 0)),
    ("Key", 5000, (255, 255, 255)),  # levels 13+
]
FRUIT_FIRST_TRIGGER = 60
FRUIT_SECOND_TRIGGER = 150

# Ghost release (dots eaten thresholds)
GHOST_RELEASE_DOTS = {
    "blinky": 0,
    "pinky": 0,
    "inky": 30,
    "clyde": 60,
}

# Colors — matching original arcade
BLACK = (0, 0, 0)
DARK_BLUE = (0, 0, 33)
WALL_COLOR = (33, 33, 222)  # classic arcade blue
WALL_BORDER = (0, 0, 140)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 182, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 182, 82)
GHOST_FRIGHTENED_COLOR = (33, 33, 222)  # dark blue when frightened
GHOST_FLASH_COLOR = (255, 255, 255)
DOT_COLOR = (255, 222, 180)  # warm dot color
PELLET_COLOR = (255, 222, 180)  # same as dots but larger/pulsing
