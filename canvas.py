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
    def __init__(self, width, height, max_players, win, admin):
        self.width = width
        self.height = height
        self.max_players = max_players
        self.admin = admin
        self._canvas = [[0]*self.width for i in range(self.height)]
        self.colors = ['red', 'green', 'blue', 'yellow', 'white',
                       'black', 'magenta', 'cyan']
        self.players = {}
        self.status = 0
        self.winner = None
        self.next_turn = None

    def add_player(self, name, color, pubkey):
        if len(self.players) >= self.max_players:
            print('Game is full')
            return False
        if name in self.players.keys():
            print('Name is already taken')
            return False
        for player in self.players.keys():
            if self.players[player]['color'] == color:
                print(warning('color already taken'))
                return False
        self.players[name] = {'color' : color, 'pubkey' : pubkey}
        return True

    def add_player_check(self, name, color):
        if len(self.players) >= self.max_players:
            print(warning('game is full'))
            return False
        if name in self.players.keys():
            print(warning('name already taken'))
            return False
        for player in self.players.keys():
            if self.players[player]['color'] == color:
                print(warning('color already taken'))
                return False
        return True

    def update_pixel(self, name, x, y):
        if self.status == -1:
            print(warning('game is over'))
            return False
        if self.status == 0:
            print(warning('game has not started yet'))
            return False
        if not name == self.next_turn:
            print(warning('not your turn'))
            cur = str(self.current_turn())
            print(info('current turn: ' + cur))
            return False
        try:
            self._canvas[x][y] = self.players[name]['color']
        except IndexError:
            print('Coordinates are out of bounds')
            return False
        self.next()
        return True

    def update_pixel_check(self, name, x, y):
        if self.status == -1:
            print(warning('game is over'))
            return False
        if self.status == 0:
            print(warning('game has not started yet'))
            return False
        if name not in self.players:
            print(warning('Player is not a part of the game'))
            return False
        if self.players[name]['color'] not in self.colors:
            print(warning('unknown color: ' + color))
        if not name == self.next_turn:
            print(warning('not your turn'))
            cur = str(self.current_turn())
            print(info('current turn: ' + cur))
            return False
        try:
            if self._canvas[x][y] != 0:
                print(warning('Pixel already painted'))
                return False
            self._canvas[x][y] = self.players[name]['color']
            self._canvas[x][y] = 0
        except IndexError:
            print(warning('Coordinates are out of bounds'))
            return False
        return True

    def start_game(self):
        if self.status == -1:
            print(warning('game is over'))
        if self.status == 1:
            print(warning('game is already running'))
        else:
            self.next_turn = list(self.players.keys())[0]
            self.status = 1
            print(info('game has started'))
            cur = str(self.current_turn())
            print(info('current turn: ' + cur))

    def check_board():
        for i in range(self.height):
            for j in range(self.width):
                if self._canvas[i][j] == 0:
                    break
                color = self._canvas[i][j]


    def next(self):
        player_index = list(self.players.keys()).index(self.next_turn) + 1
        if player_index == len(self.players.keys()):
            self.next_turn = list(self.players.keys())[0]
        else:
            self.next_turn = list(self.players.keys())[player_index]

    def current_turn(self):
        if self.next_turn:
            return self.next_turn
        else:
            print(warning('game has not started yet'))

    def print_canvas(self):
        for row in self._canvas:
            print('')
            for elem in row:
                try:
                    print(colors[elem], end='')
                except:
                    print(colors[0], end='')
        print('\n')
        print(self._canvas)
