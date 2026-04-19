import pygame
import random
from enum import Enum
from collections import deque

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PINK = (255, 184, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 184, 82)
BLUE = (33, 33, 222)

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Pacman:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.direction = Direction.RIGHT
        self.next_direction = Direction.RIGHT
        self.mouth_open = True

    def update(self, walls):
        # Try to move in the next direction first
        next_x = self.x + self.next_direction.value[0]
        next_y = self.y + self.next_direction.value[1]
        
        if self.is_valid_move(next_x, next_y, walls):
            self.x = next_x
            self.y = next_y
            self.direction = self.next_direction
        else:
            # Otherwise try to continue in current direction
            next_x = self.x + self.direction.value[0]
            next_y = self.y + self.direction.value[1]
            if self.is_valid_move(next_x, next_y, walls):
                self.x = next_x
                self.y = next_y

        self.mouth_open = not self.mouth_open

    def is_valid_move(self, x, y, walls):
        if x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT:
            return False
        return walls[y][x] == 0

    def draw(self, screen):
        color = YELLOW
        pygame.draw.circle(screen, color, (self.x * TILE_SIZE + TILE_SIZE // 2, 
                                           self.y * TILE_SIZE + TILE_SIZE // 2), 8)

class Ghost:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.move_counter = 0

    def update(self, pacman, walls):
        self.move_counter += 1
        if self.move_counter < 2:
            return

        self.move_counter = 0
        
        # Simple AI: chase Pacman
        best_direction = None
        best_distance = float('inf')

        for direction in Direction:
            next_x = self.x + direction.value[0]
            next_y = self.y + direction.value[1]

            if 0 <= next_x < GRID_WIDTH and 0 <= next_y < GRID_HEIGHT:
                if walls[next_y][next_x] == 0:
                    distance = abs(next_x - pacman.x) + abs(next_y - pacman.y)
                    if distance < best_distance:
                        best_distance = distance
                        best_direction = direction

        if best_direction:
            self.x += best_direction.value[0]
            self.y += best_direction.value[1]

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (self.x * TILE_SIZE + TILE_SIZE // 2,
                                                self.y * TILE_SIZE + TILE_SIZE // 2), 8)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pacman")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.score = 0
        self.game_over = False
        self.won = False
        self.setup_game()

    def setup_game(self):
        # Create maze (0 = path, 1 = wall)
        self.walls = [[1] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
        
        # Create corridors
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                # Create a maze pattern
                if (x > 1 and x < GRID_WIDTH - 2) and (y > 1 and y < GRID_HEIGHT - 2):
                    if (x % 2 == 1 or y % 2 == 1):
                        self.walls[y][x] = 0

        # Ensure some open space
        for x in range(2, GRID_WIDTH - 2):
            self.walls[2][x] = 0
            self.walls[GRID_HEIGHT - 3][x] = 0

        for y in range(2, GRID_HEIGHT - 2):
            self.walls[y][2] = 0
            self.walls[y][GRID_WIDTH - 3] = 0

        # Place pellets
        self.pellets = []
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.walls[y][x] == 0 and random.random() > 0.8:
                    self.pellets.append((x, y))

        # Initialize Pacman
        self.pacman = Pacman(GRID_WIDTH // 2, GRID_HEIGHT // 2)

        # Initialize ghosts
        self.ghosts = [
            Ghost(2, 2, RED),
            Ghost(GRID_WIDTH - 3, 2, PINK),
            Ghost(2, GRID_HEIGHT - 3, CYAN),
            Ghost(GRID_WIDTH - 3, GRID_HEIGHT - 3, ORANGE),
        ]

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.pacman.next_direction = Direction.UP
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.pacman.next_direction = Direction.DOWN
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    self.pacman.next_direction = Direction.LEFT
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    self.pacman.next_direction = Direction.RIGHT
                elif event.key == pygame.K_SPACE and (self.game_over or self.won):
                    self.__init__()
                    return True
        return True

    def update(self):
        if self.game_over or self.won:
            return

        self.pacman.update(self.walls)

        for ghost in self.ghosts:
            ghost.update(self.pacman, self.walls)

        # Check pellet collision
        if (self.pacman.x, self.pacman.y) in self.pellets:
            self.pellets.remove((self.pacman.x, self.pacman.y))
            self.score += 10

        # Check ghost collision
        for ghost in self.ghosts:
            if self.pacman.x == ghost.x and self.pacman.y == ghost.y:
                self.game_over = True

        # Check win condition
        if not self.pellets:
            self.won = True

    def draw(self):
        self.screen.fill(BLACK)

        # Draw walls
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.walls[y][x] == 1:
                    pygame.draw.rect(self.screen, BLUE, 
                                   (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

        # Draw pellets
        for px, py in self.pellets:
            pygame.draw.circle(self.screen, WHITE, 
                             (px * TILE_SIZE + TILE_SIZE // 2, 
                              py * TILE_SIZE + TILE_SIZE // 2), 2)

        # Draw game objects
        self.pacman.draw(self.screen)
        for ghost in self.ghosts:
            ghost.draw(self.screen)

        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))

        # Draw game state messages
        if self.game_over:
            game_over_text = self.font.render("GAME OVER! Press SPACE to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(game_over_text, text_rect)

        if self.won:
            won_text = self.font.render("YOU WIN! Press SPACE to restart", True, YELLOW)
            text_rect = won_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(won_text, text_rect)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
