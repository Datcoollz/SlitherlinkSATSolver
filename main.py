import ExamplePuzzle
from Solver import SlitherlinkSatSolver as Solver, SlitherlinkPuzzle as Puzzle
import pygame
import math
import ExamplePuzzle as Example
from threading import Thread

pygame.init()
pygame.font.init()
pygame.display.set_caption("Slitherlink solver")

screen_width, screen_height = (1200, 700)
screen = pygame.display.set_mode((screen_width, screen_height))
screen_color = ((255, 255, 255))
# (173, 202, 247)
screen.fill(screen_color)

enter_held = False
my_font = "Times new roman"


def draw_puzzle(puzzle: Puzzle.Puzzle, start_pos=(0, 0), color=(0, 0, 0), line_len=30):
    start_right, start_down = start_pos
    for i in range(puzzle.height()):
        for j in range(puzzle.width()):
            pos = (start_right + (j + 0.5) * line_len, start_down + (i + 0.5) * line_len)
            draw_text(puzzle.get_tile_string((i, j)), pos, size=line_len)
    for i in range(puzzle.height() + 1):
        for j in range(puzzle.width() + 1):
            pygame.draw.circle(screen, color, (start_right + j * line_len, start_down + i * line_len),
                               line_len / 10)


def draw_solution(solution, puzzle: Puzzle.Puzzle, start_pos=(0, 0), line_color=(0, 0, 0), line_len=25, line_width=0):
    # print("Start drawing solution")
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


def draw_text(text="", pos=(0, 0), color=(0, 0, 0), size=30, pivot_center=True):
    x, y = pos
    font = pygame.font.SysFont(my_font, size)
    text = font.render(text, True, color)
    text_rect = text.get_rect(center=pos) if pivot_center else text.get_rect(topleft=pos)
    screen.blit(text, text_rect)


def solve_and_display(input_puzzle=None):
    global enter_held
    solver = Solver.Solver(Puzzle.Puzzle(initial_puzzle=input_puzzle))
    Thread(target=solver.solve).start()
    running = True
    pw = screen_width * 0.75 / solver.puzzle_width()
    ph = screen_height * 0.75 / solver.puzzle_height()
    line_length = math.floor(pw if pw < ph else ph)
    start_pos = (
        (screen_width - line_length * solver.puzzle_width()) * 5 / 6,
        (screen_height - line_length * solver.puzzle_height()) / 2)
    result_drawn = False

    screen.fill(screen_color)
    font = pygame.font.SysFont(my_font, 100)
    text = font.render(f"Solving...", False, (0, 0, 0))
    text_rect = text.get_rect(center=(screen_width / 2, screen_height / 2))
    screen.blit(text, text_rect)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        if not result_drawn:
            if solver.is_unsolvable():
                screen.fill(screen_color)
                draw_text(f"Puzzle of size {solver.puzzle_width()}x{solver.puzzle_height()} is unsolvable",
                          pos=(100, 100), pivot_center=False)
                draw_puzzle(puzzle=solver.puzzle(), start_pos=start_pos, line_len=line_length)
                pygame.display.flip()
                result_drawn = True
                continue

            if not solver.is_solved():
                continue

            # Set screen to drawing notification screen
            screen.fill(screen_color)
            font = pygame.font.SysFont(my_font, 50)
            text = font.render(f"Solving completed, drawing...", False, (0, 0, 0))
            text_rect = text.get_rect(center=(screen_width / 2, screen_height / 2))
            screen.blit(text, text_rect)
            pygame.display.flip()

            # Console output
            solver.print_solution()

            # Draw solution
            screen.fill(screen_color)
            solution = solver.get_sol()
            draw_text(f"Solved puzzle of size: {solver.puzzle_width()}x{solver.puzzle_height()}", (100, 100),
                      pivot_center=False)
            draw_text(f"Solve time: {round(solver.solve_time(), 6)}s", (100, 150), pivot_center=False)
            draw_text(f"Total variables count: {solver.var_count()}", (100, 200), pivot_center=False)
            draw_text(f"Total clauses count: {solver.clauses_count()}", (100, 250), pivot_center=False)
            draw_text(f"Reload time: {solver.reload_time()}", (100, 300), pivot_center=False)
            draw_solution(solution=solution, puzzle=solver.puzzle(), start_pos=start_pos, line_len=line_length)
            result_drawn = True
        if pygame.key.get_pressed()[pygame.K_RETURN] and not enter_held:
            enter_held = True
            running = False
        if not pygame.key.get_pressed()[pygame.K_RETURN]:
            enter_held = False
        pygame.display.flip()


if __name__ == '__main__':
    puzzle_list = [
        ExamplePuzzle.puzzle_5x5_1,
        ExamplePuzzle.puzzle_5x5_2,
        ExamplePuzzle.puzzle_5x5_3,
        ExamplePuzzle.puzzle_7x7_1,
        ExamplePuzzle.puzzle_8x8_1,
        ExamplePuzzle.puzzle_10x10_1,
        ExamplePuzzle.puzzle_10x10_2,
        ExamplePuzzle.puzzle_15x15_1,
        ExamplePuzzle.puzzle_15x15_2,
        ExamplePuzzle.puzzle_20x20_1,
        ExamplePuzzle.puzzle_20x20_2,
        ExamplePuzzle.puzzle_25x25_1,
        ExamplePuzzle.puzzle_25_30_1,
        ExamplePuzzle.puzzle_25_30_2,
        ExamplePuzzle.puzzle_30x30_1,
        ExamplePuzzle.puzzle_36x36_1,
    ]

    # solve_and_display(ExamplePuzzle.puzzle_25_30_2)

    for p in puzzle_list:
        t = 0
        run_time = 100
        s = Solver.Solver(Puzzle.Puzzle(initial_puzzle=p))
        for i in range(run_time):
            s = Solver.Solver(Puzzle.Puzzle(initial_puzzle=p))
            s.solve()
            t += s.solve_time()
        # print(f"Puzzle size: {s.puzzle_width()} x {s.puzzle_height()}")
        # print(f"Solve time: {t / run_time}")
        # print(f"Var count: {s.var_count()}")
        # print(f"Clauses count: {s.clauses_count()}")
        # print(f"Reload time: {s.reload_time()}")
        print(f"{s.puzzle_width()}x{s.puzzle_height()} {s.var_count()} {s.clauses_count()} {s.reload_time()} {t / run_time}")
        # solve_and_display(p)
