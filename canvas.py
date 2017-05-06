from colorama import Back
from blockchain.common import *

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
    def __init__(self, width, height, max_players):
        self.width = width
        self.height = height
        self.max_players = max_players
        self._canvas = [[0]*self.width for i in range(self.height)]
        self.colors = ['red', 'green', 'blue', 'yellow', 'white',
                       'black', 'magenta', 'cyan']
        self.players = {}

    def add_player(self, name, color):
        if len(self.players) >= self.max_players:
            print('Game is full')
            return False
        if name in self.players.keys():
            print('Name is already taken')
            return False
        self.players[name] = color
        return True

    def add_player_check(self, name, color):
        if len(self.players) >= self.max_players:
            print(warning('game is full'))
            return False
        if name in self.players.keys():
            print(warning('name already taken'))
            return False
        if color in self.players.values():
            print(warning('color already taken'))
            return False
        return True

    def update_pixel(self, name, x, y):
        if name not in self.players:
            print('Player is not a part of the game')
            return False
        try:
            self._canvas[x][y] = self.players[name]
        except IndexError:
            print('Coordinates are out of bounds')
            return False
        return True

    def update_pixel_check(self, name, x, y):
        if name not in self.players:
            print(warning('Player is not a part of the game'))
            return False
        if self.players[name] not in self.colors:
            print(warning('unknown color: ' + color))
        try:
            if self._canvas[x][y] != 0:
                print(warning('Pixel already painted'))
                return False
            self._canvas[x][y] = self.players[name]
            self._canvas[x][y] = 0
        except IndexError:
            print(warning('Coordinates are out of bounds'))
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
