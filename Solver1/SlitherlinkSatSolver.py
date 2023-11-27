from pysat.solvers import Lingeling
import time
from Solver1 import SlitherlinkPuzzle


class Solver:
    def __init__(self, puzzle: SlitherlinkPuzzle.Puzzle):
        self._input_puzzle = puzzle
        self._width = self._input_puzzle.width
        self._height = self._input_puzzle.height
        self._tile_sat_var = []
        self._point_sat_var = []
        self._create_tile_line_sat_var()
        self._create_point_line_sat_var()
        self._solved = False
        self._solve_time = -1
        self._reload_time = 0
        self._clauses = []
        self._model = []

    def _create_tile_line_sat_var(self):
        for i in range(self._height):
            self._tile_sat_var.append([])
            for j in range(self._width):
                tile = {
                    "up": i * self._width + j + 1,
                    "down": (i + 1) * self._width + j + 1,
                    "left": (self._height + 1) * self._width + j * self._height + i + 1,
                    "right": (self._height + 1) * self._width + (j + 1) * self._height + i + 1
                }
                self._tile_sat_var[i].append(tile)

    def _create_point_line_sat_var(self):
        for i in range(self._height + 1):
            self._point_sat_var.append([])
            for j in range(self._width + 1):
                point = {
                    "left": i * self._width + j,
                    "right": i * self._width + j + 1,
                    "up": (self._height + 1) * self._width + j * self._height + i,
                    "down": (self._height + 1) * self._width + j * self._height + i + 1
                }
                if i <= 0: point["up"] = -1
                if i >= self._height: point["down"] = -1
                if j <= 0: point["left"] = -1
                if j >= self._width: point["right"] = -1
                self._point_sat_var[i].append(point)
            # print(self._point_sat_var[i])

    def _generate_tile_restriction_clauses(self):
        for i in range(self._height):
            for j in range(self._width):
                tile_value = self._input_puzzle.get_tile((i, j))
                if 0 <= tile_value <= 4:
                    t = self._tile_sat_var[i][j]
                    var = [t["up"], t["down"], t["left"], t["right"]]
                    at_most = _get_encoding(var, tile_value, "at_most")
                    at_least = _get_encoding(var, tile_value, "at_least")
                    for c in at_most:
                        if c:
                            # self._solver.add_clause(c)
                            self._clauses.append(c)
                    for c in at_least:
                        if c:
                            # self._solver.add_clause(c)
                            self._clauses.append(c)
        return

    def _generate_point_restriction_clauses(self):
        for i in range(self._height + 1):
            for j in range(self._width + 1):
                t = self._point_sat_var[i][j]
                var = []
                for v in t.values():
                    if v != -1:
                        var.append(v)
                clause = _get_encoding(var, 2, "at_most")
                for c in clause:
                    # self._solver.add_clause(c)
                    self._clauses.append(c[:])
                for index in range(len(var)):
                    var[index] = -var[index]
                    # self._solver.add_clause(var)
                    self._clauses.append(var[:])
                    var[index] = -var[index]

    def solve(self):
        self._solved = False
        start_time = time.perf_counter()
        print("Start solving")
        self._generate_tile_restriction_clauses()
        self._generate_point_restriction_clauses()
        while True:
            s = Lingeling(bootstrap_with=self._clauses)
            s.solve()
            self._model = s.get_model()
            if self._model is None:
                print("Unsolvable")
                self._solved = True
                return
            if self._is_valid_solution():
                break
            else:
                self._reload_time += 1
                self._generate_loop_restriction_clauses()
        solve_time = time.perf_counter() - start_time
        self._solve_time = solve_time
        self._solved = True
        print("Solve complete")
        return

    def _generate_loop_restriction_clauses(self):
        if not self._model:
            return
        new_clauses = []
        current_sol = self.get_sol()
        for i in range(len(current_sol)):
            for j in range(len(current_sol[i])):
                if not current_sol[i][j]:
                    # Get all the sides of a loop
                    loop_sides = self._check_and_fill(current_sol, i, j)
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
        check = self.get_sol()
        checked = False
        for i in range(self._height):
            for j in range(self._width):
                if not check[i][j]:
                    if checked:
                        return False
                    self._check_and_fill(check, i, j)
                    checked = True
        return True

    def is_solved(self):
        return self._solved

    def solve_time(self):
        return self._solve_time

    def reload_time(self):
        return self._reload_time

    def get_sol(self):
        # if self._solver is None:
        if not self._model:
            return None
        check = []
        for i in range(self._height):
            check.append([False] * self._width)
        for i in range(self._height):
            if self._model[self._tile_sat_var[i][0]["left"] - 1] < 0:
                self._check_and_fill(check, i, 0)
            if self._model[self._tile_sat_var[i][self._width - 1]["right"] - 1] < 0:
                self._check_and_fill(check, i, self._width - 1)
        for j in range(self._width):
            if self._model[self._tile_sat_var[0][j]["up"] - 1] < 0:
                self._check_and_fill(check, 0, j)
            if self._model[self._tile_sat_var[self._height - 1][j]["down"] - 1] < 0:
                self._check_and_fill(check, self._height - 1, j)
        return check

    def _check_and_fill(self, check, x, y):
        if x < 0 or y < 0 or x >= self._height or y >= self._width:
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
            s = self._check_and_fill(check, x - 1, y)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(up)
        if down < 0:
            s = self._check_and_fill(check, x + 1, y)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(down)
        if left < 0:
            s = self._check_and_fill(check, x, y - 1)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(left)
        if right < 0:
            s = self._check_and_fill(check, x, y + 1)
            if s is not None: loop_sides.extend(s)
        else:
            loop_sides.append(right)
        return loop_sides

    def print_solution(self):
        sol = self.get_sol()
        for i in sol:
            s = ""
            for j in i:
                if j:
                    s += " "
                else:
                    s += "0"
            print(s)
        return


def _get_encoding(var_list, num, encoding_type):
    count = len(var_list)
    if encoding_type == "at_most":
        clause_size = num + 1
    else:
        if encoding_type == "at_least":
            clause_size = count - num + 1
        else:
            return []
    if clause_size > count:
        return []
    clause = []
    for i in range(clause_size):
        clause.append(i)
    return_clauses = []
    while True:
        c = []
        for i in clause:
            if encoding_type == "at_most":
                c.append(-var_list[i])
            if encoding_type == "at_least":
                c.append(var_list[i])
        return_clauses.append(c)
        if not encoding_increment(clause, clause_size, count, clause_size - 1):
            break
    return return_clauses


def encoding_increment(clause, clause_size, var_count, index):
    if index < 0 or index >= clause_size:
        return False
    clause[index] += 1
    valid = True
    if clause[index] >= var_count - clause_size + index + 1:
        valid = encoding_increment(clause, clause_size, var_count, index - 1)
        clause[index] = clause[index - 1] + 1
    return valid
