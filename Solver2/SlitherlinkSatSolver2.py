from Solver2.SlitherlinkBoard import Board
from pysat.solvers import Glucose42
import time
import sys

sys.setrecursionlimit(1500)

class Solver:
    def __init__(self, puzzle: list) -> None:
        self.board = Board(puzzle)
        self.board_height = self.board.get_height()
        self.board_width = self.board.get_width()
        self.num_vertices = (self.board_height + 1) * (self.board_width + 1)
        self.sub_loop_size = 0
        self.sub_loop_lines = []
        self.solved = False
        self._solve_time = -1
        self._reload_time = 0

        self.graph = [[] for _ in range(self.num_vertices)]

        self.visited = [-1 for _ in range(self.num_vertices)]

        self.lines = [-line for line in range(
            self.board_height * (self.board_width + 1) +
            (self.board_height + 1) * self.board_width + 1)]

        self.clauses = []

    def cell_up_line(self, row, col) -> int:
        return row * self.board_width + col + 1

    def cell_down_line(self, row, col) -> int:
        return (row + 1) * self.board_width + col + 1

    def cell_left_line(self, row, col) -> int:
        return (self.board_height + 1) * self.board_width + \
            col * self.board_height + row + 1

    def cell_right_line(self, row, col) -> int:
        return (self.board_height + 1) * self.board_width + \
            (col + 1) * self.board_height + row + 1

    def get_vertex_coordinate(self, vertex_id):
        row = vertex_id // (self.board_width + 1)
        col = vertex_id % (self.board_width + 1)
        return row, col

    def get_vertex_id(self, row, col) -> int:
        return row * (self.board_width + 1) + col

    def vertex_up_line(self, row, col) -> int:
        return (self.board_height + 1) * self.board_width + \
            col * self.board_height + row

    def vertex_down_line(self, row, col) -> int:
        return (self.board_height + 1) * self.board_width + \
            col * self.board_height + row + 1

    def vertex_left_line(self, row, col) -> int:
        return row * self.board_width + col

    def vertex_right_line(self, row, col) -> int:
        return row * self.board_width + col + 1

    def prepare_clauses(self) -> None:
        first_rule_clauses = self.encode_first_rule()
        second_rule_clauses = self.encode_second_rule()

        self.clauses = first_rule_clauses + second_rule_clauses

    def encode_first_rule(self) -> list[list[int]]:
        clauses = []
        for row in range(self.board_height):
            for col in range(self.board_width):
                e = [
                    self.cell_up_line(row, col),
                    self.cell_right_line(row, col),
                    self.cell_down_line(row, col),
                    self.cell_left_line(row, col)
                ]

                val = self.board.at(row, col)

                if val == 0:
                    for _ in range(4):
                        clauses.append([-e[_]])

                elif val == 1:
                    clauses.append([lit for lit in e])

                    for i in range(3):
                        for j in range(i + 1, 4):
                            clauses.append([-e[i], -e[j]])

                elif val == 2:
                    for i in range(2):
                        for j in range(i + 1, 3):
                            for k in range(j + 1, 4):
                                clauses.append([e[i], e[j], e[k]])
                                clauses.append([-e[i], -e[j], -e[k]])

                elif val == 3:
                    clauses.append([lit for lit in e])

                    for i in range(3):
                        for j in range(i + 1, 4):
                            clauses.append([e[i], e[j]])

                elif val == 4:
                    for _ in range(4):
                        clauses.append([e[_]])

        return clauses

    def encode_second_rule(self) -> list[list[int]]:
        clauses = []

        for vert_id in range(self.num_vertices):
            row, col = self.get_vertex_coordinate(vert_id)

            # not all values of `e` is correct in some cases,
            # but we do not use those incorrect values in our clauses.
            e = [
                self.vertex_up_line(row, col),
                self.vertex_right_line(row, col),
                self.vertex_down_line(row, col),
                self.vertex_left_line(row, col)
            ]

            # top left corner
            if row == 0 and col == 0:
                clauses.append([-e[1], e[2]])
                clauses.append([e[1], -e[2]])

            # top right corner
            elif row == 0 and col == self.board_width:
                clauses.append([-e[3], e[2]])
                clauses.append([e[3], -e[2]])

            # bottom left corner
            elif row == self.board_height and col == 0:
                clauses.append([-e[1], e[0]])
                clauses.append([e[1], -e[0]])

            # bottom right corner
            elif row == self.board_height and col == self.board_width:
                clauses.append([-e[0], e[3]])
                clauses.append([e[0], -e[3]])

            # top side
            elif row == 0:
                clauses.append([-e[1], e[2], e[3]])
                clauses.append([e[1], -e[2], e[3]])
                clauses.append([e[1], e[2], -e[3]])
                clauses.append([-e[1], -e[2], -e[3]])

            # right side
            elif col == self.board_width:
                clauses.append([-e[0], e[2], e[3]])
                clauses.append([e[0], -e[2], e[3]])
                clauses.append([e[0], e[2], -e[3]])
                clauses.append([-e[0], -e[2], -e[3]])

            # bottom side
            elif row == self.board_height:
                clauses.append([-e[0], e[1], e[3]])
                clauses.append([e[0], -e[1], e[3]])
                clauses.append([e[0], e[1], -e[3]])
                clauses.append([-e[0], -e[1], -e[3]])

            # left side
            elif col == 0:
                clauses.append([-e[0], e[1], e[2]])
                clauses.append([e[0], -e[1], e[2]])
                clauses.append([e[0], e[1], -e[2]])
                clauses.append([-e[0], -e[1], -e[2]])

            # other: inner board
            else:
                for i in range(2):
                    for j in range(i + 1, 3):
                        for k in range(j + 1, 4):
                            clauses.append([-e[i], -e[j], -e[k]])

                clauses.append([-e[0], e[1], e[2], e[3]])
                clauses.append([e[0], -e[1], e[2], e[3]])
                clauses.append([e[0], e[1], -e[2], e[3]])
                clauses.append([e[0], e[1], e[2], -e[3]])

        return clauses

    def solve_puzzle(self) -> None:
        start_time = time.perf_counter()
        self.prepare_clauses()
        self.solve()
        self.handle_third_rule()
        self.solved = True
        self._solve_time = time.perf_counter() - start_time

    def handle_third_rule(self) -> None:
        while True:
            if self.validate_and_add_assumptions():
                break
            self._reload_time += 1
            self.solve()

    def solve(self) -> None:
        self.solved = False
        print(len(self.clauses))
        with Glucose42(bootstrap_with=self.clauses) as solver:
            solver.solve()
            model = solver.get_model()
        self.lines = [0] + model

    def validate_and_add_assumptions(self) -> bool:
        self.build_vertex_graph()

        num_connected_vertices = 0
        for u in range(self.num_vertices):
            if len(self.graph[u]) > 0:
                num_connected_vertices += 1

        for u in range(self.num_vertices):
            if len(self.graph[u]) > 0 and self.visited[u] == -1:
                self.sub_loop_size = -1
                self.sub_loop_lines = []
                self.find_loop(u)

                # validate the model (check whether it contained only ONE loop)
                if self.sub_loop_size == num_connected_vertices:
                    return True

                # if the model is invalid, create new assumptions
                # corresponding to the sub loops
                sub_loop_clauses = []
                for line in self.sub_loop_lines:
                    sub_loop_clauses.append(-line)

                self.clauses.append(sub_loop_clauses)

    def find_loop(self, u: int) -> None:
        self.sub_loop_size += 1
        for tup in self.graph[u]:
            v = tup[0]
            if self.visited[v] == -1:
                self.visited[v] = tup[1]
                self.sub_loop_lines.append(tup[1])
                self.find_loop(v)

    def build_vertex_graph(self) -> None:
        # reset the graph
        for _ in range(len(self.graph)):
            self.graph[_] = []
        for _ in range(len(self.visited)):
            self.visited[_] = -1

        # build new graph
        for u in range(self.num_vertices):

            row, col = self.get_vertex_coordinate(u)
            # not all values of `e` is correct in some cases,
            # but we do not use those incorrect values in our clauses.
            e = [
                self.vertex_up_line(row, col),
                self.vertex_right_line(row, col),
                self.vertex_down_line(row, col),
                self.vertex_left_line(row, col)
            ]

            # top left corner
            if row == 0 and col == 0:
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))

            # top right corner
            elif row == 0 and col == self.board_width:
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))

            # bottom left corner
            elif row == self.board_height and col == 0:
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))

            # bottom right corner
            elif row == self.board_height and col == self.board_width:
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))

            # top side
            elif row == 0:
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))

            # right side
            elif col == self.board_width:
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))

            # bottom side
            elif row == self.board_height:
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))

            # left side
            elif col == 0:
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))

            # other: inner board
            else:
                if self.lines[e[0]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row - 1, col), e[0]))
                if self.lines[e[1]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col + 1), e[1]))
                if self.lines[e[2]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row + 1, col), e[2]))
                if self.lines[e[3]] > 0:
                    self.graph[u].append(
                        (self.get_vertex_id(row, col - 1), e[3]))

    def is_solved(self):
        return self.solved

    def solve_time(self):
        return self._solve_time

    def reload_time(self):
        return self._reload_time

    def get_sol(self):
        if not self.lines:
            return None
        check = []
        for i in range(self.board_height):
            check.append([False] * self.board_width)
        for i in range(self.board_height):
            if self.lines[self.cell_left_line(i, 0)] < 0:
                self._check_and_fill(check, i, 0)
            if self.lines[self.cell_right_line(i, self.board_width - 1)] < 0:
                self._check_and_fill(check, i, self.board_width - 1)
        for j in range(self.board_width):
            if self.lines[self.cell_up_line(0, j)] < 0:
                self._check_and_fill(check, 0, j)
            if self.lines[self.cell_down_line(self.board_height - 1, j)] < 0:
                self._check_and_fill(check, self.board_height - 1, j)
        return check

    def _check_and_fill(self, check, x, y):
        if x < 0 or y < 0 or x >= self.board_height or y >= self.board_width:
            return []
        if check[x][y]:
            return []
        loop_sides = []
        check[x][y] = True
        up, down, left, right = (
            self.lines[self.cell_up_line(x, y)],
            self.lines[self.cell_down_line(x, y)],
            self.lines[self.cell_left_line(x, y)],
            self.lines[self.cell_right_line(x, y)]
        )
        if up < 0:
            s = self._check_and_fill(check, x - 1, y)
            if s is not None:
                loop_sides.extend(s)
        else:
            loop_sides.append(up)
        if down < 0:
            s = self._check_and_fill(check, x + 1, y)
            if s is not None:
                loop_sides.extend(s)
        else:
            loop_sides.append(down)
        if left < 0:
            s = self._check_and_fill(check, x, y - 1)
            if s is not None:
                loop_sides.extend(s)
        else:
            loop_sides.append(left)
        if right < 0:
            s = self._check_and_fill(check, x, y + 1)
            if s is not None:
                loop_sides.extend(s)
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
