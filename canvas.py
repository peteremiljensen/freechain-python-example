from colorama import Back

colors = {'r' : Back.RED + '  ' + Back.RESET,
          'g' : Back.GREEN + '  ' + Back.RESET,
          'b' : Back.BLUE + '  ' + Back.RESET,
          'y' : Back.YELLOW + '  ' + Back.RESET,
          'w' : Back.WHITE + '  ' + Back.RESET,
           0  : Back.BLACK + '  ' + Back.RESET}

class Canvas():
    def __init__(self, w=10, h=10, no_players=5):
        self._canvas = [[0]*w for i in range(h)]
        self.no_players = no_players
        self.players = []

    def add_player(self, name):
        if len(self.players) >= self.no_players:
            print('Game is full')
            return False
        if name in self.players:
            print('Name is already taken')
            return False

        self.players.append(name)
        return True

    def add_player_check(self, name):
        if len(self.players) >= self.no_players:
            print('Game is full')
            return False
        if name in self.players:
            print('Name is already taken')
            return False

        return True

    def update_pixel(self, color, name, x, y):
        if name not in self.players:
            print('Player is not a part of the game')
            return False
        try:
            self._canvas[y][x] = color
        except IndexError:
            print('Coordinates are out of bounds')
            return False
        return True

    def update_pixel_check(self, color, name, x, y):
        if name not in self.players:
            print('Player is not a part of the game')
            return False
        try:
            self._canvas[x][y] = color
            self._canvas[x][y] = 0
        except IndexError:
            print('Coordinates are out of bounds')
            return False
        return True

    def print_canvas(self):
        for row in self._canvas:
            print('')
            for elem in row:
                print(colors[elem], end='')
        print('\n')
