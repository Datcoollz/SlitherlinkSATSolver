class Board:
    def __init__(self, puzzle) -> None:
        self.height = len(puzzle)
        self.width = len(puzzle[0])
        self.data = puzzle

    def get_height(self):
        return self.height

    def get_width(self):
        return self.width

    def at(self, row, col) -> int:
        return self.data[row][col]
