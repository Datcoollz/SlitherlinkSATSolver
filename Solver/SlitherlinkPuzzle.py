class Puzzle:
    def __init__(self, initial_puzzle=None):
        self._board = initial_puzzle
        self._height = len(self._board)
        self._width = len(self._board[0])

    def get_tile(self, pos) -> int:
        x, y = pos
        if 0 <= x < self._height and 0 <= y < self._width:
            return self._board[x][y]
        return -1

    def get_tile_string(self, pos):
        x, y = pos
        if 0 <= x < self._height and 0 <= y < self._width:
            if 0 <= self._board[x][y] <= 4:
                return str(self._board[x][y])
        return " "

    def width(self):
        return self._width

    def height(self):
        return self._height
