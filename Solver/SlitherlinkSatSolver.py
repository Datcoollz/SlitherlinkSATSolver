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
        self._model = []
        self._solved = False
        start_time = time.perf_counter()
        self._clauses = self._encode_first_rule() + self._encode_second_rule()
        # print("Total clauses count", len(self._clauses))
        while True:
            s = Glucose42(bootstrap_with=self._clauses)
            s.solve()
            # s.solve()
            if s.get_model() is None:
                print("Unsolvable")
                self._model = None
                self._unsolvable = True
                return
            self._model = [0] + s.get_model()
            if self._encode_third_rule():
                self._solved = True
                break
            else:
                self._reload_time += 1
        solve_time = time.perf_counter() - start_time
        self._solve_time = solve_time
        # print("Solve time", solve_time)
        return

    def _encode_third_rule(self):
        if not self._model:
            return
        visited = self.get_sol()
        useful_loop_list = []
        useless_loop_list = []
        for i in range(self._input_puzzle.height()):
            for j in range(self._input_puzzle.width()):
                if not visited[i][j]:
                    sides, is_useful_loop = self._check_and_fill_connected_area(visited, i, j)
                    # print(self.reload_time(), is_useful_loop, sides)
                    if is_useful_loop:
                        useful_loop_list.append([-_ for _ in sides])
                    else:
                        useless_loop_list.append([-_ for _ in sides])
        valid_solution = (len(useful_loop_list) == 1)
        # If solution is valid, clear all useless loops
        if valid_solution:
            for useless_loop in useless_loop_list:
                for side in useless_loop:
                    self._model[-side] = -self._model[side - 1]
        # Else add all loops into the solver
        else:
            self._clauses += useless_loop_list
            self._clauses += useful_loop_list
        return valid_solution

    def get_sol(self):
        if not self._model:
            return None
        h, w = (self._input_puzzle.height(), self._input_puzzle.width())
        check = [[False for _ in range(w)] for __ in range(h)]
        for i in range(h):
            if self._model[self._tile_sat_var[i][0]["left"]] < 0:
                self._check_and_fill_connected_area(check, i, 0)
            if self._model[self._tile_sat_var[i][w - 1]["right"]] < 0:
                self._check_and_fill_connected_area(check, i, w - 1)
        for j in range(w):
            if self._model[self._tile_sat_var[0][j]["up"]] < 0:
                self._check_and_fill_connected_area(check, 0, j)
            if self._model[self._tile_sat_var[h - 1][j]["down"]] < 0:
                self._check_and_fill_connected_area(check, h - 1, j)
        return check

    def _check_and_fill_connected_area(self, check, x, y) -> (list, bool):
        if x < 0 or y < 0 or x >= self._input_puzzle.height() or y >= self._input_puzzle.width():
            return [], False
        if check[x][y]:
            return [], False
        loop_sides = []
        check[x][y] = True
        is_useful_loop = False
        sides = [
            ("up", (x - 1, y)),
            ("down", (x + 1, y)),
            ("left", (x, y - 1)),
            ("right", (x, y + 1)),
        ]
        for side in sides:
            name, pos = side
            model_val = self._model[self._tile_sat_var[x][y][name]]
            if model_val < 0:
                s, ck = self._check_and_fill_connected_area(check, pos[0], pos[1])
                if s is not None: loop_sides.extend(s)
                if ck: is_useful_loop = True
            else:
                if self._relevant_line_check((x, y), name):
                    is_useful_loop = True
                loop_sides.append(model_val)
        return loop_sides, is_useful_loop

    def _relevant_line_check(self, pos, side):
        # Check whether a line is next to tiles with number or not
        x, y = pos
        if not 0 <= self.puzzle().get_tile((x, y)) <= 4:
            if (side == "up" and (x == 0 or not 0 <= self.puzzle().get_tile((x - 1, y)) <= 4)) or (
                    side == "left" and (y == 0 or not 0 <= self.puzzle().get_tile((x, y - 1)) <= 4)) or (
                    side == "down" and (
                    x == self.puzzle_height() - 1 or not 0 <= self.puzzle().get_tile((x + 1, y)) <= 4)) or (
                    side == "right" and (
                    y == self.puzzle_width() - 1 or not 0 <= self.puzzle().get_tile((x, y + 1)) <= 4)):
                return False
        return True

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
        return len(self._model) - 1

    def puzzle_width(self):
        return self._input_puzzle.width()

    def puzzle_height(self):
        return self._input_puzzle.height()

    def puzzle(self):
        return self._input_puzzle
