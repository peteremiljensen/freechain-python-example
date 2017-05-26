#!/usr/bin/env python3

import datetime
import time
import argparse
from cmd import Cmd
from colorama import Fore

from canvas import *
from freechain.node import *

import rsakeys
import hashlib

#                   _
#                  (_)
#   _ __ ___   __ _ _ _ __
#  | '_ ` _ \ / _` | | '_ \
#  | | | | | | (_| | | | | |
#  |_| |_| |_|\__,_|_|_| |_|
#
#

parser = argparse.ArgumentParser(description='program for testing of ' +
                                             'blockchain framework')
parser.add_argument('-p', '--port', nargs='?', default='9000',
                    help='Port for the node to use')
parser.add_argument('-c', '--chain', nargs='?',
                    help='Path to file containing a blockchain to load' +
                    'if the file does not eists, one is created')
parser.add_argument('-r', '--privkey', nargs='?',
                    help='Path to private key. If the file does not exist' +
                    'one is created')
parser.add_argument('-u', '--pubkey', nargs='?',
                    help='Path to public key. If the file does not exist' +
                    'one is created')

args = parser.parse_args()
port = args.port
chain_path = args.chain

if args.privkey == None and args.pubkey == None:
    privkey_path = 'privatepix.asm'
    pubkey_path = 'publicpix.asm'
else:
    privkey_path = args.privkey
    pubkey_path = args.pubkey

def loaf_validator(loaf):
    if 'type' not in loaf.get_data().keys():
        print(fail('Loaf has no type'))
        return
    hash_calc = loaf.calculate_hash()
    new_keys = ['game', 'width', 'height', 'max_players', 'name', 'win', 'type']
    add_keys = ['game', 'name', 'pubkey', 'color', 'type', 'sig']
    start_keys = ['game', 'type']
    update_keys = ['game', 'name', 'sig', 'x', 'y', 'type']
    try:
        if (loaf['type'] == 'new_game' and
            set(new_keys).issubset(loaf.get_data().keys()) and
            loaf['game'] != 'null' and
            type(loaf['width'])  == int and
            type(loaf['height']) == int and
            type(loaf['max_players']) == int and
            loaf['name'] != 'null' and
            type(loaf['win'] == int)):
            return loaf.get_hash() == hash_calc

        elif (loaf['type'] == 'add_player' and
              set(add_keys).issubset(loaf.get_data().keys()) and
              loaf['game']   != 'null' and
              loaf['name']   != 'null' and
              loaf['pubkey'] != 'null' and
              loaf['color']  != 'null' and
              loaf['sig']    != 'null'):
            return loaf.get_hash() == hash_calc

        elif (loaf['type'] == 'start_game' and
              loaf['game'] != 'null'):
            return loaf.get_hash() == hash_calc

        elif (loaf['type'] == 'update_pixel' and
              set(update_keys).issubset(loaf.get_data().keys()) and
              loaf['game'] != 'null' and
              loaf['name'] != 'null' and
              loaf['sig'] != 'null' and
              type(loaf['x']) == int and
              type(loaf['y']) == int):
            return loaf.get_hash() == hash_calc

        else:
            print(fail('loaf could not validate'))
            return False
    except:
        print('exception in loaf validation')
        raise
        return False

def block_validator(block):
    hash_calc = block.calculate_hash()
    return block.get_hash() == hash_calc

def mine(loaves, prev_block):
    height = prev_block.get_height() + 1
    previous_block_hash = prev_block.get_hash()
    timestamp = str(datetime.datetime.now())
    block = Block(loaves, height, previous_block_hash, timestamp)

    if block.validate():
        return block
    else:
        print('Block could not be mined')
        return None

def branching(chain1, chain2):
    if chain1.get_length() < chain2.get_length():
        return chain2
    else:
        return chain1

class Prompt(Cmd):
    PRINTS = ['players', 'blockchain', 'games',
              'current_game', 'turn']

    def __init__(self):
        ''' Prompt class constructor
        '''
        super().__init__()

        self._port = port
        self._chainfile = chain_path
        self._privkey_path = 'pixprivate.asm'
        self._pubkey_path = 'pixpublic.asm'
        self._node = Node(self._port)
        Events.Instance().register_callback(EVENTS_TYPE.RECEIVED_BLOCK,
                                            lambda _: self.do_z(""))
        genesis_block = Block.create_block_from_dict(
            {"hash":"00001620395c8da353f5005e713fe2fee85ad63c618ad01b7dd712bc5f4cc56d",
             "height":0, "loaves":[], "data":"",
             "previous_block_hash":"-1",
             "timestamp":"2017-05-01 15:19:56.585873"})
        self._node.add_block(genesis_block)

        self._procesed_height = 0

        self.game = None
        self.games = {}
        self.name = None
        self.browsing = 0

        if privkey_path and pubkey_path:
            if (os.path.exists(privkey_path) and
                os.path.exists(pubkey_path)):
                self._privkey, self._pubkey = rsakeys.read_keys(privkey_path, pubkey_path)
                try:
                    test = rsakeys.check_keys(self._privkey, self._pubkey)
                except:
                    print(fail('exception in key checking'))
                    self.browsing = 1
                    test = False
                if not test:
                    print(warning('keys do not match, browsing mode enabled'))
                    self.browsing = 1
            else:
                self._privkey, self._pubkey = rsakeys.generate_keys()
                rsakeys.write_keys(self._privkey, self._pubkey,
                                   privkey_path, pubkey_path)
        elif privkey_path or pubkey_path:
            print(warning('you have to provide a private and public key' \
                          + 'to play, browsing mode enabled'))
            self.browsing = 1

        if self._chainfile and os.path.exists(self._chainfile):
            chain = Chain.read_chain(self._chainfile)

            if not chain.validate():
                self._chainfile = None
                print(fail('Loaded blockchain is not valid'))
                self.do_quit(args)

            for i in range(1, chain.get_length()):
                if not self._node.add_block(chain.get_block(i)):
                    print(warning('Block of height ' + str(chain.get_block(i).get_height())+\
                                  'read from file, could not be added. '))
                    self.do_quit(args)
            self._procesed_height = self.proces_chain(self._procesed_height)

        self._node.start()

        self._node.attach_loaf_validator(loaf_validator)
        self._node.attach_block_validator(block_validator)
        self._node.attach_branching(branching)

    def do_connect(self, args):
        ''' Parses the arguments to get nodes ip and connects to node
        '''
        l = args.split()
        if len(l) > 2:
            print(fail('invalid number of arguments'))
            return
        try:
            ip = l[0]
            if len(l) == 2:
                self._node.connect_node(ip, l[1])
            else:
                self._node.connect_node(ip)
            time.sleep(0.5)
            self._procesed_height = 0
            self.games = {}
            self._procesed_height = self.proces_chain(self._procesed_height)
        except:
            print(fail('error connecting to node'))
            raise

    def read_keys(self, priv_path, pub_path):
        return rsakeys.read_keys(priv_path, pub_path)

    def save_keys(self, privkey, pubkey, priv_path, pub_path):
        rsakeys.write_keys(privkey, pubkey, priv_path, pub_path)

    def proces_chain(self, height):
        if not height < self._node.get_chain().get_length() - 1:
            return height
        chain = self._node.get_chain().get_blocks(height + 1, -1)
        for block in chain:
            if not self.proces_block(block):
                print('failed to process block of height:',
                      block.get_height())
                return height
        return self._node._chain.get_length() - 1

    def proces_block(self, block):
        for loaf in block.get_loaves():
            if not self.proces_loaf(loaf):
                print('failed to proces loaf')
                return False
        return True

    def proces_loaf(self, loaf):
        if loaf['type'] == 'new_game':
            game_name = loaf['game']
            width  = loaf['width']
            height = loaf['height']
            max_players = loaf['max_players']
            win   = loaf['win']
            admin = loaf['name']
            if game_name in self.games.keys():
                print(fail('game already exists'))
                return False
            self.games[game_name] = Canvas(width, height, max_players, win, admin)
            print(info('Created game: ' + game_name))

        elif loaf['type'] == 'add_player':
            game  = self.games[loaf['game']]
            color = loaf['color']
            name  = loaf['name']
            signature = loaf['sig']
            pubkey    = rsakeys.import_key(loaf['pubkey'].encode('utf-8'))
            hashed_name = hashlib.md5(name.encode('utf-8')).digest()
            if not rsakeys.validate(pubkey, hashed_name, signature):
                print(fail('Failed to verify message'))
                return False
            if not game.add_player(name, color, pubkey):
                print(fail('failed to add player:'))
                return False
            print(info('player ' + name + ' added to game:'))

        elif loaf['type'] == 'start_game':
            game = self.games[loaf['game']]
            game.start_game()

        elif loaf['type'] == 'update_pixel':
            game = self.games[loaf['game']]
            game_name = loaf['game']
            name = loaf['name']
            signature = loaf['sig']
            x = loaf['x']
            y = loaf['y']
            hashed_name = hashlib.md5(name.encode('utf-8')).digest()
            pubkey = self.games[game_name].players[name]['pubkey']
            if not rsakeys.validate(pubkey, hashed_name, signature):
                print(fail('Failed to verify message'))
                return False
            if not game.update_pixel(name, x, y):
                print(fail('failed to update pixel'))
                return False
        else:
            print('loaf has undefined type')
            return False
        return True

    def do_mine(self, args):
        ''' Reads argument and tries to mine block. if block is mined,
            the block is added to the chain and broadcasted
        '''
        l = args.split()
        if len(l) != 0:
            print (fail('mine doesnt take any arguments'))
            return
        try:
            loaves = self._node.get_loaves()
            chain_length = self._node.get_chain().get_length()
            prev_block = self._node.get_chain().get_block(chain_length-1)
            block = mine(loaves, prev_block)
            if block is None:
                print(fail('failed to mine block'))
            else:
                if self._node.add_block(block):
                    self._procesed_height = self.proces_chain(self._procesed_height)
                    if self._procesed_height == self._node.get_chain().get_length() - 1:
                        self._node.broadcast_block(block)
                    else:
                        print('failed to proces chain')
                else:
                    print(fail('failed to add block'))
        except:
            print(fail('error trying to mine'))
            raise

    def do_new_game(self, args):
        if self.browsing == 1:
            print(warning('can not create games in browsing mode'))
            return
        l = args.split()
        if len(l) != 5:
            print(fail('Invalid number of arguments'))
            print(fail('Args: <game> <width> <height> <max_players> <win>'))
            return

        if l[0] in self.games.keys():
            print(fail('Game already exists'))
            return
        if int(l[4]) > int(l[1]) or int(l[4]) > int(l[1]):
            print(fail('The win condition is too big for the board'))
            return
        try:
            loaf = Loaf({'game' : l[0], 'height' : int(l[2]),
                         'width' : int(l[1]), 'max_players' : int(l[3]),
                         'name' : self.name, 'win' : int(l[4]),
                         'type' : 'new_game'})
            if self._node.add_loaf(loaf):
                self.do_mine('')
                self.do_join_game(str(l[0]))
            else:
                print(fail('failed to add loaf to loaf pool'))
        except:
            print(fail('error creating and broadcasting loaf'))
            raise

    def do_join_game(self, args):
        l = args.split()
        if len(l) != 1:
            print(fail('invalid number of arguments. args: <game>'))
            return
        if l[0] in self.games.keys():
            self.game = l[0]
            game = self.games[self.game]
        else:
            print(warning('game ' + l[0] + ' does not eist'))
            return
        if self.browsing == 1:
            print(warning('joined game as spectator'))
            return
        for player in self.games[self.game].players.keys():
            if player == self.name:
                pubkey_check = self.games[self.game].players[self.name]['pubkey']
                if rsakeys.check_keys(self._privkey, pubkey_check):
                    return
                else:
                    print(fail('failed to authenticate as ' + player))
                    return
        color = input('Color: ')
        if self.games[self.game].status == 1:
            print(warning('game has already started, joined game as spectator'))
            return
        if self.games[self.game].status == -1:
            print(warning('game is over, the winner was: ' \
                          + self.games[self.game].winner))
            return
        if game.add_player_check(self.name, color):
            pubkey = rsakeys.export_key(self._pubkey).decode('utf-8')
            try:
                loaf = Loaf({'color' : color, 'game' : l[0], 'name' : self.name,
                             'pubkey': pubkey,
                             'sig' : rsakeys.sign(self._privkey, self.name),
                             'type' : 'add_player'})
                if self._node.add_loaf(loaf):
                    self.do_mine('')
                    self.games[self.game].print_canvas()
                else:
                    print(fail('failed to add loaf to loaf pool'))
            except:
                print(fail('error creating and broadcasting loaf'))
                raise

    def do_draw(self, args):
        l = args.split()
        if len(l) != 2:
            print(fail('invalid number of arguments. Args: <game> <x> <y>'))
            return
        if self.game:
            game_name = self.game
        else:
            print(fail('not in a game'))
            return
        name = self.name
        self.games[game_name].check_board
        try:
            if self.games[game_name].update_pixel_check(name, int(l[0]), int(l[1])):
                loaf = Loaf({'game' : game_name, 'name' : self.name,
                             'sig' : rsakeys.sign(self._privkey, self.name),
                             'x': int(l[0]), 'y' : int(l[1]),
                             'type' : 'update_pixel'})
                if self._node.add_loaf(loaf):
                    self.do_mine('')
                    self.games[self.game].print_canvas()
                else:
                    print(fail('failed to add loaf to loaf pool'))
        except:
                print(fail('error creating and broadcasting loaf'))
                raise

    def do_start_game(self, args):
        if self.game:
            game_name = self.game
        else:
            print(fail('not in a game'))
            return
        if self.games[game_name].status == -1:
            print(warning('game is over'))
        if self.games[game_name].status == 1:
            print(warning('game is already running'))
        if self.games[game_name].admin == self.name:
            check_pubkey = self.games[game_name].players[self.name]['pubkey']
            if rsakeys.check_keys(self._privkey, check_pubkey):
                try:
                    loaf = Loaf({'game' : game_name, 'type' : 'start_game'})
                    if self._node.add_loaf(loaf):
                        self.do_mine('')
                except:
                    print(fail('error creating and broadcasting loaf'))
                    raise
            else:
                print(warning('failed to authorize, keys do not correspond'))
        else:
            print(warning('you do not have permissions to start the game'))

    def do_z(self, args):
        self._procesed_height = self.proces_chain(self._procesed_height)
        l = args.split()
        if len(l) != 0:
            print (fail('doesnt take any arguments'))
            return
        if self.game == None:
            return
        self.games[self.game].print_canvas()

    def do_print(self, args):
        ''' Prints loaf pool or blockchain
        '''
        l = args.split()
        self._procesed_height = self.proces_chain(self._procesed_height)
        try:
            if l[0] == self.PRINTS[0]:
                if not self.game:
                    print(fail('not in a game'))
                    return
                res = "[ "
                for player in self.games[self.game].players:
                    if self.games[self.game].players[player]['color'] == 'red':
                        res = res + Fore.RED + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'green':
                        res = res + Fore.GREEN + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'blue':
                        res = res + Fore.BLUE + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'yellow':
                        res = res + Fore.YELLOW + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'white':
                        res = res + Fore.WHITE + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'magenta':
                        res = res + Fore.MAGENTA + ' ' + player + Fore.RESET + ','
                    elif self.games[self.game].players[player]['color'] == 'cyan':
                        res = res + Fore.CYAN + ' ' + player + Fore.RESET + ','
                res = res[:-1] + "  ]"
                print(res)
            elif l[0] == self.PRINTS[1]:
                print(self._node._chain.json())
            elif l[0] == self.PRINTS[2]:
                res = "[ "
                for game in list(self.games.keys()):
                    if self.games[game].status == -1:
                        res = res + '\033[91m ' + game + '\033[0m,'
                    if self.games[game].status == 1:
                        res = res + '\033[92m ' + game + '\033[0m,'
                    if self.games[game].status == 0:
                        res = res + '\033[93m ' + game + '\033[0m,'
                res = res[:-1] + "  ]"
                print(res)
            elif l[0] == self.PRINTS[3]:
                if not self.game:
                    print(warning('not in a game'))
                    return
                if self.games[self.game].status == -1:
                    print('\033[91m ' + self.game + '\033[0m')
                if self.games[self.game].status == 1:
                    print('\033[92m ' + self.game + '\033[0m')
                if self.games[self.game].status == 0:
                    print('\033[93m ' + self.game + '\033[0m')
            elif l[0] == self.PRINTS[4]:
                turn = self.games[self.game].current_turn()
                if turn:
                    print(info(turn))
            else:
                print(fail(l[0] + ' does not exist'))

        except:
            print(fail('error printing'))
            raise

    def complete_print(self, text, line, begidx, endidx):
        if not text:
            completions = self.PRINTS[:]
        else:
            completions = [f for f in self.PRINTS
                            if f.startswith(text)]
        return completions

    def do_EOF(self, line):
        ''' Calls do_quit if at end of file
        '''
        self.do_quit(line)

    def do_quit(self, args):
        ''' Quits program
        '''
        if self._chainfile:
            Chain.save_chain(self._chainfile, self._node.get_chain())
        print(info('Quitting'))
        raise SystemExit

    def do_q(self, args):
        self.do_quit(args)

    def emptyline(self):
        ''' If empty line is sent, does nothing
        '''
        return

if __name__ == '__main__':
    ''' Program start. If no port argument is given, sets port to 9000,
        then creates a prompt object and waits for user input
    '''

    prompt = Prompt()
    prompt.name = input('Name: ')
    prompt.prompt = '(freechain) '
    try:
        prompt.cmdloop(info('Starting node on port ' + str(port) + '...'))
    except KeyboardInterrupt:
        prompt.do_quit(None)
    except SystemExit:
        pass
    except:
        print(fail('fatal error'))
        raise
