from pysat.solvers import Glucose42
import time
from Solver.SlitherlinkPuzzle import Puzzle
import sys

sys.setrecursionlimit(1500)


class Solver:
    def __init__(self, puzzle: Puzzle):
        self._input_puzzle = puzzle
        self._tile_sat_var = []
        self._point_sat_var = []
        self._solved = False
        self._unsolvable = False
        self._solve_time = -1
        self._reload_time = 0
        self._clauses = []
        self._model = []

        # Init variables for reference
        self._create_tile_line_sat_var()
        self._create_point_line_sat_var()

    def _create_tile_line_sat_var(self):
        w, h = (self._input_puzzle.width(), self._input_puzzle.height())
        for i in range(h):
            self._tile_sat_var.append([])
            for j in range(w):
                tile = {
                    "up": i * w + j + 1,
                    "down": (i + 1) * w + j + 1,
                    "left": (h + 1) * w + j * h + i + 1,
                    "right": (h + 1) * w + (j + 1) * h + i + 1
                }
                self._tile_sat_var[i].append(tile)

    def _create_point_line_sat_var(self):
        w, h = (self._input_puzzle.width(), self._input_puzzle.height())
        for i in range(h + 1):
            self._point_sat_var.append([])
            for j in range(w + 1):
                point = {
                    "left": i * w + j,
                    "right": i * w + j + 1,
                    "up": (h + 1) * w + j * h + i,
                    "down": (h + 1) * w + j * h + i + 1
                }
                point["up"] = -1 if i <= 0 else point["up"]
                point["down"] = -1 if i >= h else point["down"]
                point["left"] = -1 if j <= 0 else point["left"]
                point["right"] = -1 if j >= w else point["right"]
                self._point_sat_var[i].append(point)

    def _encode_first_rule(self) -> list[list[int]]:
        clauses = []
        for row in range(self._input_puzzle.height()):
            for col in range(self._input_puzzle.width()):
                t = self._tile_sat_var[row][col]
                e = [t["up"], t["down"], t["left"], t["right"]]
                val = self._input_puzzle.get_tile((row, col))
                # If val == 0 or val == 1 do the inverse of 4 and 3
                if val == 0 or val == 1:
                    val = 4 - val
                    e = [-i for i in e]
                if val == 2:
                    for x1 in range(2):
                        for x2 in range(x1 + 1, 3):
                            for x3 in range(x2 + 1, 4):
                                clauses.append([e[x1], e[x2], e[x3]])
                                clauses.append([-e[x1], -e[x2], -e[x3]])
                elif val == 3:
                    clauses.append([-lit for lit in e])
                    for x1 in range(3):
                        for x2 in range(x1 + 1, 4):
                            clauses.append([e[x1], e[x2]])
                elif val == 4:
                    for _ in range(4):
                        clauses.append([e[_]])
        return clauses

    def _encode_second_rule(self) -> list[list[int]]:
        clauses = []
        for row in range(self._input_puzzle.height() + 1):
            for col in range(self._input_puzzle.width() + 1):
                t = self._point_sat_var[row][col]
                var = []
                for v in t.values():
                    if v != -1:
                        var.append(v)
                print()
                # This rule removes cases with 1 line
                for index in range(len(var)):
                    var[index] = -var[index]
                    clauses.append(var[:])
                    var[index] = -var[index]
                # This rule removes cases with 3+ lines
                for i in range(2):
                    for j in range(i + 1, 3):
                        for k in range(j + 1, 4):
                            if i >= len(var) or j >= len(var) or k >= len(var):
                                continue
                            clauses.append([-var[i], -var[j], -var[k]])
        return clauses

    def solve(self):
        self._solved = False
        start_time = time.perf_counter()
        print("Start solving puzzle of size", self._input_puzzle.width(), "x", self._input_puzzle.height())
        self._clauses = self._encode_first_rule() + self._encode_second_rule()
        while True:
            s = Glucose42(bootstrap_with=self._clauses)
            s.solve()
            self._model = s.get_model()
            self.print_solution()
            if self._model is None:
                print("Unsolvable")
                self._unsolvable = True
                return
            if self._is_valid_solution():
                self._solved = True
                break
            else:
                self._reload_time += 1
                self._encode_third_rule()
        solve_time = time.perf_counter() - start_time
        self._solve_time = solve_time
        print(self._reload_time)
        print("Solve complete")
        return

    def _encode_third_rule(self):
        if not self._model:
            return
        new_clauses = []
        current_sol = self.get_sol()
        for i in range(len(current_sol)):
            for j in range(len(current_sol[i])):
                if not current_sol[i][j]:
                    # Get all the sides of a loop
                    loop_sides = self._check_and_fill_connected_area(current_sol, i, j)
                    clause = []
                    # Reverse the values to get the clause
                    for side in loop_sides:
                        clause.append(-side)
                    new_clauses.append(clause)
        for i in new_clauses:
            self._clauses.append(i[:])
        return

    def _is_valid_solution(self):
        if not self._model:
            return
        visited = self.get_sol()
        found_one_loop = False
        for i in range(self._input_puzzle.height()):
            for j in range(self._input_puzzle.width()):
                if not visited[i][j]:
                    if found_one_loop:
                        return False
                    self._check_and_fill_connected_area(visited, i, j)
                    found_one_loop = True
        return True

    def get_sol(self):
        if not self._model:
            return None
        check = []
        for i in range(self._input_puzzle.height()):
            check.append([False] * self._input_puzzle.width())
        for i in range(self._input_puzzle.height()):
            if self._model[self._tile_sat_var[i][0]["left"] - 1] < 0:
                self._check_and_fill_connected_area(check, i, 0)
            if self._model[self._tile_sat_var[i][self._input_puzzle.width() - 1]["right"] - 1] < 0:
                self._check_and_fill_connected_area(check, i, self._input_puzzle.width() - 1)
        for j in range(self._input_puzzle.width()):
            if self._model[self._tile_sat_var[0][j]["up"] - 1] < 0:
                self._check_and_fill_connected_area(check, 0, j)
            if self._model[self._tile_sat_var[self._input_puzzle.height() - 1][j]["down"] - 1] < 0:
                self._check_and_fill_connected_area(check, self._input_puzzle.height() - 1, j)
        return check

    def _check_and_fill_connected_area(self, check, x, y):
        if x < 0 or y < 0 or x >= self._input_puzzle.height() or y >= self._input_puzzle.width():
            return []
        if check[x][y]:
            return []
        loop_sides = []
        check[x][y] = True
        up, down, left, right = (
            self._model[self._tile_sat_var[x][y]["up"] - 1],
            self._model[self._tile_sat_var[x][y]["down"] - 1],
            self._model[self._tile_sat_var[x][y]["left"] - 1],
            self._model[self._tile_sat_var[x][y]["right"] - 1]
        )
        if up < 0:
            s = self._check_and_fill_connected_area(check, x - 1, y)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(up)
        if down < 0:
            s = self._check_and_fill_connected_area(check, x + 1, y)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(down)
        if left < 0:
            s = self._check_and_fill_connected_area(check, x, y - 1)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(left)
        if right < 0:
            s = self._check_and_fill_connected_area(check, x, y + 1)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(right)
        return loop_sides

    def print_solution(self):
        sol = self.get_sol()
        if sol is None:
            print("No solution found")
            return
        for i in sol:
            s = ""
            for j in i:
                if j:
                    s += " "
                else:
                    s += "█"
            print(s)
        return

    def is_solved(self):
        return False if self._unsolvable else self._solved

    def is_unsolvable(self):
        return self._unsolvable

    def solve_time(self):
        return self._solve_time

    def reload_time(self):
        return self._reload_time

    def clauses_count(self):
        return len(self._clauses)

    def var_count(self):
        return len(self._model)

    def puzzle_width(self):
        return self._input_puzzle.width()

    def puzzle_height(self):
        return self._input_puzzle.height()

    def puzzle(self):
        return self._input_puzzle
