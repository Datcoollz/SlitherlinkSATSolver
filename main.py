from Solver1 import SlitherlinkPuzzle as SPuzzle, SlitherlinkSatSolver as SSolver
from Solver2 import SlitherlinkSatSolver2 as SSolver2
import pygame
import math
import ExamplePuzzle as Example
from threading import Thread

pygame.init()
pygame.font.init()
pygame.display.set_caption("Slitherlink solver")

screen_width, screen_height = (900, 900)
screen = pygame.display.set_mode((screen_width, screen_height))
screen.fill((173, 202, 247))

my_font = "Times new roman"


def draw_puzzle(puzzle: SPuzzle.Puzzle, start_pos=(0, 0), color=(0, 0, 0), line_len=30):
    start_right, start_down = start_pos
    for i in range(puzzle.height):
        for j in range(puzzle.width):
            draw_text((start_right + (j + 0.5) * line_len, start_down + (i + 0.5) * line_len),
                      puzzle.get_tile_string((i, j)), size=line_len)
    for i in range(puzzle.height + 1):
        for j in range(puzzle.width + 1):
            pygame.draw.circle(screen, color, (start_right + j * line_len, start_down + i * line_len),
                               line_len / 10)


def draw_solution(solution, puzzle: SPuzzle.Puzzle, start_pos=(0, 0), line_color=(0, 0, 0), line_len=25, line_width=0):
    print("Start drawing solution")
    start_right, start_down = start_pos
    if line_width == 0:
        line_width = math.floor(line_len / 25) + 1
    for i in range(len(solution)):
        for j in range(len(solution[i])):
            if not solution[i][j]:
                if i - 1 < 0 or solution[i - 1][j]:
                    line_start_pos = (start_right + j * line_len, start_down + i * line_len)
                    line_end_pos = (start_right + (j + 1) * line_len, start_down + i * line_len)
                    pygame.draw.line(screen, line_color, line_start_pos, line_end_pos, line_width)
                if j - 1 < 0 or solution[i][j - 1]:
                    line_start_pos = (start_right + j * line_len, start_down + i * line_len)
                    line_end_pos = (start_right + j * line_len, start_down + (i + 1) * line_len)
                    pygame.draw.line(screen, line_color, line_start_pos, line_end_pos, line_width)

                if i + 1 >= len(solution) or solution[i + 1][j]:
                    line_start_pos = (start_right + j * line_len, start_down + (i + 1) * line_len)
                    line_end_pos = (start_right + (j + 1) * line_len, start_down + (i + 1) * line_len)
                    pygame.draw.line(screen, line_color, line_start_pos, line_end_pos, line_width)
                if j + 1 >= len(solution[i]) or solution[i][j + 1]:
                    line_start_pos = (start_right + (j + 1) * line_len, start_down + i * line_len)
                    line_end_pos = (start_right + (j + 1) * line_len, start_down + (i + 1) * line_len)
                    pygame.draw.line(screen, line_color, line_start_pos, line_end_pos, line_width)
    draw_puzzle(puzzle, start_pos, line_len=line_len)


def draw_text(pos=(0, 0), text="", color=(0, 0, 0), size=30):
    x, y = pos
    font = pygame.font.SysFont(my_font, size)
    text = font.render(text, False, color)
    text_rect = text.get_rect(center=pos)
    screen.blit(text, text_rect)


def main(use_solver_1=True, input_puzzle=None):
    # Solver 1
    example_puzzle = SPuzzle.Puzzle(initial_puzzle=input_puzzle)
    solver1 = SSolver.Solver(example_puzzle)

    # Solver 2
    solver2 = SSolver2.Solver(input_puzzle)

    if not use_solver_1:
        Thread(target=solver2.solve_puzzle).start()
    else:
        Thread(target=solver1.solve).start()

    pygame.display.flip()
    running = True

    pw = screen_width * 0.75 / example_puzzle.width
    ph = screen_height * 0.75 / example_puzzle.height
    line_length = math.floor(pw if pw < ph else ph)
    start_pos = (
        (screen_width - line_length * example_puzzle.width) / 2,
        (screen_height - line_length * example_puzzle.height) / 2)
    puzzle_drawn = False

    screen.fill((173, 202, 247))
    font = pygame.font.SysFont(my_font, 100)
    font = pygame.font.SysFont(my_font, 100)
    text = font.render(f"Solving...", False, (0, 0, 0))
    text_rect = text.get_rect(center=(screen_width / 2, screen_height / 2))
    screen.blit(text, text_rect)
    print("Draw")

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if not puzzle_drawn:
            if use_solver_1:
                if not solver1.is_solved(): continue
            else:
                if not solver2.is_solved(): continue

            if (use_solver_1 and solver1.get_sol() is None) or (not use_solver_1 and solver2.get_sol() is None):
                screen.fill((173, 202, 247))
                font = pygame.font.SysFont(my_font, size=25)
                text = font.render(f"Unsolvable", False, (0, 0, 0))
                text_rect = text.get_rect(center=(screen_width / 2, 100 / 2))
                screen.blit(text, text_rect)

                draw_puzzle(puzzle=example_puzzle, start_pos=start_pos, line_len=line_length)

                pygame.display.flip()
                puzzle_drawn = True
                continue

            # Set screen to drawing notification screen
            screen.fill((173, 202, 247))
            font = pygame.font.SysFont(my_font, 50)
            text = font.render(f"Solving completed, drawing...", False, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_width / 2, screen_height / 2))
            screen.blit(text, text_rect)
            pygame.display.flip()

            # Draw solution
            screen.fill((173, 202, 247))
            if use_solver_1:
                solve_time = solver1.solve_time()
                reload_time = solver1.reload_time()
                solution = solver1.get_sol()
            else:
                solve_time = solver2.solve_time()
                reload_time = solver2.reload_time()
                solution = solver2.get_sol()
            font = pygame.font.SysFont(my_font, size=25)
            text = font.render(f"Solve time: {solve_time}s, reload time: {reload_time}", False, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_width / 2, 100 / 2))
            screen.blit(text, text_rect)

            draw_solution(solution=solution, puzzle=example_puzzle, start_pos=start_pos, line_len=line_length)
            puzzle_drawn = True
        if pygame.key.get_pressed()[pygame.K_ESCAPE]:
            running = False
        pygame.display.flip()


if __name__ == '__main__':
    main(use_solver_1=False, input_puzzle=Example.puzzle_30x30_1)
