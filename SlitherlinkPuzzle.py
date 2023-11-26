class Puzzle:
    def __init__(self, initial_puzzle=None):
        self._board = initial_puzzle
        self.height = len(self._board)
        self.width = len(self._board[0])

    def set_tile(self, pos, val):
        x, y = pos
        self._board[x][y] = val

    def get_tile(self, pos):
        x, y = pos
        if 0 <= x < self.height and 0 <= y < self.width:
            return self._board[x][y]
        return -1

    def get_tile_string(self, pos):
        x, y = pos
        if 0 <= x < self.height and 0 <= y < self.width:
            if 0 <= self._board[x][y] <= 4:
                return str(self._board[x][y])
        return " "
