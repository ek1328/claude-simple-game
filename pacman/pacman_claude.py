"""
PAC-MAN  ─  Python + pygame
Install : pip install pygame
Run     : python pacman.py
Controls: Arrow Keys / WASD | ENTER = start | P = pause | R = restart | ESC = quit
"""

import os, sys, math, random
os.environ["SDL_VIDEO_CENTERED"] = "1"   # centre window on launch

#import pygame.freetype
import pygame.freetype   # more portable than pygame.font — works on all platforms

# ── Layout ────────────────────────────────────────────────────────────────────
TILE   = 24
COLS   = 28
ROWS   = 22
W      = COLS * TILE           # 672
HUD_H  = 44
BOT_H  = 32
MAZE_H = ROWS * TILE           # 528
H      = HUD_H + MAZE_H + BOT_H   # 604
FPS    = 60

PAC_SPD   = 3    # px/frame; TILE (24) % PAC_SPD == 0
GHOST_SPD = 2    # px/frame; TILE (24) % GHOST_SPD == 0

FRIGHT_SECS = 7
BLINK_SECS  = 2

EXIT_COL = 12    # ghost-house exit column
EXIT_ROW = 10    # first open row above house

# ── Colours ───────────────────────────────────────────────────────────────────
BLACK    = (  0,   0,   0)
WALL_F   = ( 28,  28, 210)
WALL_B   = ( 72,  72, 255)
YELLOW   = (255, 215,   0)
LGOLD    = (255, 230, 100)
WHITE    = (255, 255, 255)
RED      = (230,  20,  20)
PINK     = (255, 184, 255)
CYAN_G   = (  0, 224, 224)
ORANGE   = (255, 184,  82)
FRIGHT_C = ( 20,  20, 190)
FRIGHT_W = (220, 220, 220)
CYAN_HUD = (  0, 220, 220)
GRAY     = (140, 140, 140)
PUPIL    = (  0,   0, 180)
DKWALL   = ( 14,  14,  50)

GHOST_COLS = [RED, PINK, CYAN_G, ORANGE]

# ── Cell types ────────────────────────────────────────────────────────────────
EMPTY, WALL, DOT, POWER, HOUSE = 0, 1, 2, 3, 5

# ── Ghost modes ───────────────────────────────────────────────────────────────
CHASE, FRIGHT, EATEN, IN_HOUSE = "chase", "fright", "eaten", "house"

FOUR_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# ── Map ───────────────────────────────────────────────────────────────────────
# Pac-Man spawns at col=14, row=20 (verified DOT cell).
# Cols 9 & 18 are open at rows 9-10 (corridors beside ghost house).
# HOUSE(5) cells are rendered as solid blue walls — pac-man cannot enter.
MAP_ORIG = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  #  0
    [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],  #  1
    [1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1],  #  2
    [1,3,1,0,0,1,2,1,0,0,0,1,2,1,1,2,1,0,0,0,1,2,1,0,0,1,3,1],  #  3
    [1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1],  #  4
    [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],  #  5
    [1,2,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,2,1],  #  6
    [1,2,1,1,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,1,2,1,1,1,1,2,1],  #  7
    [1,2,2,2,2,2,2,1,1,2,2,2,2,1,1,2,2,2,2,1,1,2,2,2,2,2,2,1],  #  8
    [1,1,1,1,1,1,2,1,1,0,1,1,0,1,1,0,1,1,0,1,1,2,1,1,1,1,1,1],  #  9
    [0,0,0,0,0,1,2,1,1,0,1,1,0,1,1,0,1,1,0,1,1,2,1,0,0,0,0,0],  # 10
    [0,0,0,0,0,1,2,1,1,0,5,5,5,5,5,5,5,5,0,1,1,2,1,0,0,0,0,0],  # 11 house roof
    [1,1,1,1,1,1,2,1,1,0,1,1,1,0,0,1,1,1,0,1,1,2,1,1,1,1,1,1],  # 12
    [0,0,0,0,0,0,2,0,0,0,1,1,0,0,0,0,1,1,0,0,0,2,0,0,0,0,0,0],  # 13
    [1,1,1,1,1,1,2,1,1,0,1,1,1,1,1,1,1,1,0,1,1,2,1,1,1,1,1,1],  # 14
    [0,0,0,0,0,1,2,1,1,0,5,5,5,5,5,5,5,5,0,1,1,2,1,0,0,0,0,0],  # 15 house floor
    [0,0,0,0,0,1,2,1,1,0,1,1,1,1,1,1,1,1,0,1,1,2,1,0,0,0,0,0],  # 16
    [1,1,1,1,1,1,2,1,1,0,1,1,1,1,1,1,1,1,0,1,1,2,1,1,1,1,1,1],  # 17
    [1,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,1],  # 18
    [1,2,1,1,1,1,2,1,1,1,1,1,2,1,1,2,1,1,1,1,1,2,1,1,1,1,2,1],  # 19
    [1,3,2,2,1,1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1,1,2,2,3,1],  # 20 ← pac spawn
    [1,1,1,2,1,1,2,1,1,2,1,1,1,1,1,1,1,1,2,1,1,2,1,1,2,1,1,1],  # 21
]

GHOST_DEFS = [          # col, row, delay_frames, color
    (13, 13,   0, RED),
    (13, 13,  80, PINK),
    (14, 13, 160, CYAN_G),
    (15, 13, 240, ORANGE),
]


# ── Font helpers (pygame.freetype — no pygame.font required) ─────────────────
_ft_cache: dict = {}

def _ft(size: int, bold: bool = True) -> pygame.freetype.Font:
    key = (size, bold)
    if key not in _ft_cache:
        _ft_cache[key] = pygame.freetype.SysFont("monospace", size, bold=bold)
    return _ft_cache[key]

def draw_text(surf, text, size, color, cx, cy, bold=True):
    """Render text centred at (cx, cy)."""
    img, rect = _ft(size, bold).render(text, color)
    rect.center = (cx, cy)
    surf.blit(img, rect)

def make_text(text, size, color, bold=True, alpha=255):
    """Return a Surface with rendered text (supports alpha)."""
    img, _ = _ft(size, bold).render(text, color)
    if alpha < 255:
        img.set_alpha(alpha)
    return img


# ── Geometry helpers ──────────────────────────────────────────────────────────
def tcx(col): return col * TILE + TILE // 2
def tcy(row): return row * TILE + TILE // 2

def get_cell(grid, col, row):
    if row < 0 or row >= ROWS:
        return WALL
    return grid[row][col % COLS]

def pac_blocked(grid, col, row):
    return get_cell(grid, col, row) in (WALL, HOUSE)

def ghost_blocked(grid, col, row, allow_house=False):
    c = get_cell(grid, col, row)
    return c == WALL or (c == HOUSE and not allow_house)

def pie_points(cx, cy, r, angle, mouth, steps=24):
    pts = [(cx, cy)]
    for i in range(steps + 1):
        a = angle + mouth + (2 * math.pi - 2 * mouth) * i / steps
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def ghost_body_pts(cx, cy, r):
    pts = []
    for i in range(17):
        a = math.pi + math.pi * i / 16
        pts.append((cx + r * math.cos(a), cy - 2 + r * math.sin(a)))
    pts.append((cx + r, cy + r))
    for i in range(7):
        bx = cx + r - 2 * r * (i / 6)
        by = cy + r - (r * 0.32 if i % 2 == 0 else 0)
        pts.append((bx, by))
    pts.append((cx - r, cy - 2))
    return pts


# ── Pac-Man ───────────────────────────────────────────────────────────────────
class Pacman:
    def __init__(self):
        self.reset()

    def reset(self):
        self.px   = tcx(14)   # col 14, row 20 — verified DOT cell
        self.py   = tcy(20)
        self.dx   = 0
        self.dy   = 0
        self.wdx  = 0         # buffered direction from last key press
        self.wdy  = 0
        self.mouth = 0.25
        self.mdir  = -1

    @property
    def col(self): return self.px // TILE
    @property
    def row(self): return self.py // TILE

    def centred(self):
        return self.px % TILE == TILE // 2 and self.py % TILE == TILE // 2

    def update(self, grid):
        # At a tile centre, try to apply the buffered direction
        if self.centred() and (self.wdx, self.wdy) != (0, 0):
            nc = (self.col + self.wdx) % COLS
            nr =  self.row + self.wdy
            if not pac_blocked(grid, nc, nr):
                self.dx, self.dy = self.wdx, self.wdy

        if (self.dx, self.dy) == (0, 0):
            return

        npx = (self.px + self.dx * PAC_SPD) % (COLS * TILE)
        npy =  self.py + self.dy * PAC_SPD

        # Leading-edge wall check
        h = TILE // 2
        if   self.dx ==  1: lc, lr = (npx + h) // TILE, npy // TILE
        elif self.dx == -1: lc, lr = (npx - h) // TILE, npy // TILE
        elif self.dy ==  1: lc, lr =  npx // TILE,     (npy + h) // TILE
        elif self.dy == -1: lc, lr =  npx // TILE,     (npy - h) // TILE
        else:               lc, lr =  self.col,         self.row
        lc %= COLS

        if pac_blocked(grid, lc, lr):
            # Snap back to tile centre so we never get stuck inside a wall
            self.px = self.col * TILE + TILE // 2
            self.py = self.row * TILE + TILE // 2
        else:
            self.px, self.py = npx, npy

        self.mouth += 0.07 * self.mdir
        if self.mouth >= 0.42: self.mdir = -1
        if self.mouth <= 0.02: self.mdir =  1

    def draw(self, surf, _frame):
        cx = self.px
        cy = self.py + HUD_H
        r  = TILE // 2 - 1

        if   self.dx ==  1: angle = 0
        elif self.dx == -1: angle = math.pi
        elif self.dy == -1: angle = -math.pi / 2
        elif self.dy ==  1: angle =  math.pi / 2
        else:               angle = 0

        pts = pie_points(cx, cy, r, angle, self.mouth)
        pygame.draw.polygon(surf, YELLOW, pts)
        pygame.draw.polygon(surf, (200, 160, 0), pts, 1)

        # Eye — always in upper quadrant; correct formula for left-facing direction
        eye_a = angle + math.pi / 4 if self.dx == -1 else angle - math.pi / 4
        ex = int(cx + math.cos(eye_a) * r * 0.48)
        ey = int(cy + math.sin(eye_a) * r * 0.48)
        pygame.draw.circle(surf, BLACK, (ex, ey), 2)


# ── Ghost ─────────────────────────────────────────────────────────────────────
class Ghost:
    def __init__(self, col, row, delay, color):
        self._col, self._row, self._delay = col, row, delay
        self.color = color
        self.reset()

    def reset(self):
        self.px     = tcx(self._col)
        self.py     = tcy(self._row)
        self.dx     = 0
        self.dy     = 0
        self.mode   = IN_HOUSE
        self.fright = 0
        self.delay  = self._delay

    @property
    def col(self): return self.px // TILE
    @property
    def row(self): return self.py // TILE

    def centred(self):
        return self.px % TILE == TILE // 2 and self.py % TILE == TILE // 2

    def frighten(self):
        if self.mode not in (IN_HOUSE, EATEN):
            self.mode   = FRIGHT
            self.fright = FRIGHT_SECS * FPS
            self.dx, self.dy = -self.dx, -self.dy

    def update(self, grid, pac):
        if self.mode == IN_HOUSE:
            self._house_step()
            return

        spd = GHOST_SPD

        if self.mode == FRIGHT:
            self.fright -= 1
            if self.fright <= 0:
                self.mode = CHASE

        # Target selection
        if self.mode == EATEN:
            spd    = GHOST_SPD * 2
            target = (tcx(EXIT_COL), tcy(EXIT_ROW + 2))
        elif self.mode == FRIGHT:
            target = (random.randint(0, COLS - 1) * TILE,
                      random.randint(0, ROWS - 1) * TILE) if self.centred() else (self.px, self.py)
        else:
            target = (pac.px, pac.py)

        if self.centred():
            self.dx, self.dy = self._best_dir(grid, target, self.mode == EATEN)

        # Move
        npx = (self.px + self.dx * spd) % (COLS * TILE)
        npy =  self.py + self.dy * spd

        h = TILE // 2
        if   self.dx ==  1: lc, lr = (npx + h) // TILE, npy // TILE
        elif self.dx == -1: lc, lr = (npx - h) // TILE, npy // TILE
        elif self.dy ==  1: lc, lr =  npx // TILE,     (npy + h) // TILE
        elif self.dy == -1: lc, lr =  npx // TILE,     (npy - h) // TILE
        else:               lc, lr =  self.col,         self.row
        lc %= COLS

        if ghost_blocked(grid, lc, lr, allow_house=(self.mode == EATEN)):
            self.px = self.col * TILE + TILE // 2
            self.py = self.row * TILE + TILE // 2
        else:
            self.px, self.py = npx, npy

        # Revive eaten ghost once deep inside house
        if self.mode == EATEN:
            if abs(self.py - tcy(13)) <= spd + 2 and abs(self.px - tcx(EXIT_COL)) <= spd + 2:
                self.px, self.py = tcx(EXIT_COL), tcy(13)
                self.mode  = IN_HOUSE
                self.delay = 50

    def _house_step(self):
        self.delay -= 1
        if self.delay > 0:
            # Gentle bob while waiting
            self.py = tcy(self._row) + int(math.sin(self.delay * 0.18) * 5)
            return
        # Slide to exit column
        tx = tcx(EXIT_COL)
        if abs(self.px - tx) > GHOST_SPD:
            self.dx = 1 if self.px < tx else -1
            self.dy = 0
            self.px += self.dx * GHOST_SPD
            return
        self.px = tx
        # Rise above house roof
        ty = tcy(EXIT_ROW)
        if self.py > ty:
            self.dy = -1
            self.py -= GHOST_SPD
            return
        # Exited
        self.py          = ty
        self.dx, self.dy = 1, 0
        self.mode        = CHASE

    def _best_dir(self, grid, target, allow_house):
        gc, gr = self.col, self.row
        opp    = (-self.dx, -self.dy)
        best_d = (self.dx, self.dy) if (self.dx, self.dy) != (0, 0) else (1, 0)
        best_dist = float("inf")
        dirs = list(FOUR_DIRS)
        random.shuffle(dirs)
        for d in dirs:
            if d == opp:
                continue
            nc = (gc + d[0]) % COLS
            nr =  gr + d[1]
            if ghost_blocked(grid, nc, nr, allow_house):
                continue
            dist = (nc * TILE - target[0]) ** 2 + (nr * TILE - target[1]) ** 2
            if dist < best_dist:
                best_dist, best_d = dist, d
        return best_d

    def draw(self, surf, frame):
        cx = self.px
        cy = self.py + HUD_H
        r  = TILE // 2 - 1

        blink = (self.mode == FRIGHT
                 and self.fright < BLINK_SECS * FPS
                 and (frame // 7) % 2 == 0)

        if   self.mode == EATEN: body = (30, 30, 100)
        elif blink:               body = FRIGHT_W
        elif self.mode == FRIGHT: body = FRIGHT_C
        else:                     body = self.color

        pts = ghost_body_pts(cx, cy, r)
        if len(pts) >= 3:
            pygame.draw.polygon(surf, body, pts)
            rim = tuple(max(0, c - 60) for c in body)
            pygame.draw.polygon(surf, rim, pts, 1)

        if self.mode == FRIGHT:
            for i in range(4):
                sx = int(cx - 5 + i * 3.5)
                sy = cy + 2 + (2 if i % 2 else -2)
                pygame.draw.circle(surf, WHITE, (sx, sy), 1)
        else:
            for ox in (-4, 4):
                ex, ey = cx + ox, cy - 3
                pygame.draw.circle(surf, WHITE, (ex, ey), 3)
                pygame.draw.circle(surf, PUPIL,
                                   (ex + self.dx * 2, ey + self.dy * 2), 2)


# ── Game ──────────────────────────────────────────────────────────────────────
class Game:
    MENU  = "menu"
    READY = "ready"
    PLAY  = "play"
    DEAD  = "dead"
    WIN   = "win"
    OVER  = "over"
    PAUSE = "pause"

    def __init__(self):
        pygame.init()
        pygame.freetype.init()
        pygame.display.set_caption("PAC-MAN")
        self.screen  = pygame.display.set_mode((W, H))
        self.clock   = pygame.time.Clock()
        self.frame   = 0
        self.hiscore = 0
        self._new_game()

    # ── Init ──────────────────────────────────────────────────────────────────
    def _new_game(self):
        self.score = 0
        self.lives = 3
        self.level = 1
        self.state = self.MENU
        self._setup_level()

    def _setup_level(self):
        self.grid       = [row[:] for row in MAP_ORIG]
        self.total_dots = sum(c in (DOT, POWER) for row in self.grid for c in row)
        self.eaten_dots = 0
        self.pops       = []   # [(px, py, text, ttl)]
        self.combo      = 0
        self.ready_cd   = FPS * 2
        self.pac        = Pacman()
        self.ghosts     = [Ghost(*d) for d in GHOST_DEFS]
        self._wall_surf = self._build_wall_surf()

    def _build_wall_surf(self):
        """Pre-render static walls once per level into a cached Surface."""
        surf = pygame.Surface((W, H), pygame.SRCALPHA)
        for row in range(ROWS):
            for col in range(COLS):
                if self.grid[row][col] in (WALL, HOUSE):
                    rect = pygame.Rect(col * TILE, HUD_H + row * TILE, TILE, TILE)
                    pygame.draw.rect(surf, WALL_F, rect, border_radius=4)
                    pygame.draw.rect(surf, WALL_B, rect, width=1, border_radius=4)
        return surf

    def _reset_positions(self):
        self.pac.reset()
        for g in self.ghosts:
            g.reset()
        self.combo    = 0
        self.ready_cd = FPS * 2
        self.state    = self.READY

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        respawn_ms = 0   # countdown in ms; >0 means pac just died

        while True:
            dt = self.clock.tick(FPS)

            # ── Events ────────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    self._handle_key(event.key)

            # ── Respawn timer ──────────────────────────────────────────────────
            if self.state == self.DEAD:
                respawn_ms -= dt
                if respawn_ms <= 0:
                    respawn_ms = 0
                    self._reset_positions()

            # ── Update ────────────────────────────────────────────────────────
            if self.state == self.READY:
                self.ready_cd -= 1
                if self.ready_cd <= 0:
                    self.state = self.PLAY

            elif self.state == self.PLAY:
                self.pac.update(self.grid)
                self._eat()
                for g in self.ghosts:
                    g.update(self.grid, self.pac)
                died = self._collide()
                if died and self.state == self.DEAD:
                    respawn_ms = 1400
                self.pops = [(x, y - 0.6, t, ttl - 1)
                             for (x, y, t, ttl) in self.pops if ttl > 1]

            # ── Draw ──────────────────────────────────────────────────────────
            self._draw()
            self.frame += 1

    def _handle_key(self, k):
        dirs = {
            pygame.K_LEFT:  (-1,  0), pygame.K_a: (-1,  0),
            pygame.K_RIGHT: ( 1,  0), pygame.K_d: ( 1,  0),
            pygame.K_UP:    ( 0, -1), pygame.K_w: ( 0, -1),
            pygame.K_DOWN:  ( 0,  1), pygame.K_s: ( 0,  1),
        }
        if k in dirs:
            self.pac.wdx, self.pac.wdy = dirs[k]
            if self.state in (self.MENU, self.OVER):
                self._setup_level()
                self.state = self.READY
        elif k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            if self.state in (self.MENU, self.OVER):
                self._setup_level()
                self.state = self.READY
            elif self.state == self.WIN:
                self.level += 1
                self._setup_level()
                self.state = self.READY
        elif k == pygame.K_p:
            if   self.state == self.PLAY:  self.state = self.PAUSE
            elif self.state == self.PAUSE: self.state = self.PLAY
        elif k == pygame.K_r:
            self._new_game()
        elif k == pygame.K_ESCAPE:
            pygame.quit(); sys.exit()

    # ── Gameplay logic ────────────────────────────────────────────────────────
    def _eat(self):
        col = self.pac.col % COLS
        row = self.pac.row
        if not (0 <= row < ROWS):
            return
        cell = self.grid[row][col]
        if cell == DOT:
            self.grid[row][col] = EMPTY
            self._score(10)
            self.eaten_dots += 1
        elif cell == POWER:
            self.grid[row][col] = EMPTY
            self._score(50)
            self.eaten_dots += 1
            self.combo = 0
            for g in self.ghosts:
                g.frighten()
        if self.eaten_dots >= self.total_dots:
            self.state = self.WIN

    def _score(self, pts):
        self.score += pts
        if self.score > self.hiscore:
            self.hiscore = self.score
        self.pops.append((self.pac.px, self.pac.py + HUD_H - TILE, str(pts), 38))

    def _collide(self):
        """Returns True if pac-man just died."""
        for g in self.ghosts:
            if g.mode in (IN_HOUSE, EATEN):
                continue
            if abs(self.pac.px - g.px) < TILE - 4 and abs(self.pac.py - g.py) < TILE - 4:
                if g.mode == FRIGHT:
                    g.mode   = EATEN
                    g.fright = 0
                    self.combo += 1
                    self._score(200 * (2 ** (self.combo - 1)))
                else:
                    self.lives -= 1
                    self.state = self.OVER if self.lives <= 0 else self.DEAD
                    return True
        return False

    # ── Drawing ───────────────────────────────────────────────────────────────
    def _draw(self):
        self.screen.fill(BLACK)
        self._draw_hud()
        self._draw_maze()

        if self.state != self.MENU:
            self.pac.draw(self.screen, self.frame)
            for g in self.ghosts:
                g.draw(self.screen, self.frame)

        self._draw_pops()

        if self.state == self.MENU:
            self._overlay("PAC-MAN",
                          "PRESS  ARROW KEY  OR  ENTER  TO  START", YELLOW)
        elif self.state == self.READY:
            draw_text(self.screen, "READY!", 28, YELLOW, W // 2, HUD_H + MAZE_H // 2)
        elif self.state == self.DEAD:
            draw_text(self.screen, "OOPS!", 28, (255, 80, 80), W // 2, HUD_H + MAZE_H // 2)
        elif self.state == self.WIN:
            self._overlay("LEVEL  CLEAR!",
                          "PRESS  ENTER  FOR  NEXT  LEVEL", CYAN_HUD)
        elif self.state == self.OVER:
            self._overlay("GAME  OVER",
                          "PRESS  ENTER  TO  PLAY  AGAIN", (255, 80, 80))
        elif self.state == self.PAUSE:
            self._overlay("PAUSED", "PRESS  P  TO  RESUME", GRAY)

        pygame.display.flip()

    def _draw_hud(self):
        ty = HUD_H // 2
        draw_text(self.screen, f"SCORE  {self.score}", 15, WHITE,    110,    ty)
        draw_text(self.screen, f"HI  {self.hiscore}",  15, LGOLD,    W // 2, ty)
        draw_text(self.screen, f"LEVEL  {self.level}", 15, CYAN_HUD, W - 100, ty)

        pygame.draw.line(self.screen, (30, 30, 80), (0, HUD_H - 1),      (W, HUD_H - 1))
        pygame.draw.line(self.screen, (30, 30, 80), (0, HUD_H + MAZE_H), (W, HUD_H + MAZE_H))

        by = HUD_H + MAZE_H + BOT_H // 2
        for i in range(self.lives):
            pts = pie_points(22 + i * 26, by, 9, 0, 0.28)
            pygame.draw.polygon(self.screen, YELLOW, pts)

        hint = make_text("ESC=quit   P=pause   R=restart", 11, GRAY, bold=False)
        self.screen.blit(hint, hint.get_rect(midright=(W - 8, by)))

    def _draw_maze(self):
        self.screen.blit(self._wall_surf, (0, 0))
        pulse = 5 + int(2.0 * math.sin(self.frame * 0.12))
        for row in range(ROWS):
            for col in range(COLS):
                cell = self.grid[row][col]
                cx   = col * TILE + TILE // 2
                cy   = HUD_H + row * TILE + TILE // 2
                if cell == DOT:
                    pygame.draw.circle(self.screen, YELLOW, (cx, cy), 2)
                elif cell == POWER:
                    pygame.draw.circle(self.screen, YELLOW, (cx, cy), pulse)
                    pygame.draw.circle(self.screen, LGOLD,  (cx, cy), pulse, 1)

    def _draw_pops(self):
        for (x, y, text, ttl) in self.pops:
            img = make_text(text, 13, CYAN_HUD, bold=True, alpha=min(255, ttl * 7))
            self.screen.blit(img, img.get_rect(center=(int(x), int(y))))

    def _overlay(self, title, sub, color):
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 168))
        self.screen.blit(dim, (0, 0))

        cx, cy = W // 2, H // 2
        bw, bh = 268, 82
        box = pygame.Rect(cx - bw, cy - bh, bw * 2, bh * 2)
        pygame.draw.rect(self.screen, DKWALL, box, border_radius=12)
        pygame.draw.rect(self.screen, WALL_B, box, width=2, border_radius=12)

        draw_text(self.screen, title, 28, color, cx, cy - 26)
        draw_text(self.screen, sub,   12, WHITE, cx, cy + 12, bold=False)
        draw_text(self.screen, f"HI-SCORE  {self.hiscore}", 13, LGOLD, cx, cy + 44)


# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    Game().run()
