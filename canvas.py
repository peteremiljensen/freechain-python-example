from colorama import Back

colors = {'red'     : Back.RED + '  ' + Back.RESET,
          'green'   : Back.GREEN + '  ' + Back.RESET,
          'blue'    : Back.BLUE + '  ' + Back.RESET,
          'yellow'  : Back.YELLOW + '  ' + Back.RESET,
          'white'   : Back.WHITE + '  ' + Back.RESET,
          'black'   : Back.BLACK + '  ' + Back.RESET,
          'magenta' : Back.MAGENTA + '  ' + Back.RESET,
          'cyan'    : Back.CYAN + '  ' + Back.RESET,
           0        : Back.BLACK + '  ' + Back.RESET}

class Canvas():
    def __init__(self, w=20, h=20, no_players=3):
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
            return False
        if name in self.players:
            return False

        return True

    def update_pixel(self, color, name, x, y):
        if name not in self.players:
            print('Player is not a part of the game')
            return False
        try:
            self._canvas[x][y] = color
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
                try:
                    print(colors[elem], end='')
                except:
                    print(colors[0], end='')
        print('\n')
