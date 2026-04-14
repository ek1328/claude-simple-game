import pygame
from settings import SCREEN_W, SCREEN_H, FPS
from game import Game
from renderer import Renderer


def main():
    pygame.init()
    pygame.display.set_caption("PAC-MAN")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    game = Game()
    renderer = Renderer(screen)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # delta time in seconds

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        game.update(dt, events)
        if game.quit_requested:
            break
        renderer.draw(game, dt)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
