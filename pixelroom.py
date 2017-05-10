#!/usr/bin/env python3

import datetime
import time
import argparse
from cmd import Cmd

from canvas import *
from blockchain.node import *

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
privkey_path = args.privkey
pubkey_path = args.pubkey

def loaf_validator(loaf):
    if 'type' not in loaf._loaf['data'].keys():
        print(fail('Loaf has no type'))
        return
    hash_calc = loaf.calculate_hash()
    new_keys = ['game', 'width', 'height', 'max_players', 'type']
    add_keys = ['game', 'name', 'pubkey', 'color', 'type', 'sig']
    update_keys = ['game', 'name', 'sig', 'x', 'y', 'type']
    try:
        if (loaf._loaf['data']['type'] == 'new_game' and
            set(new_keys).issubset(loaf._loaf['data'].keys()) and
            loaf._loaf['data']['game'] != 'null' and
            type(loaf._loaf['data']['width']) == int and
            type(loaf._loaf['data']['height']) == int and
            type(loaf._loaf['data']['max_players']) == int):
            return loaf.get_hash() == hash_calc

        elif (loaf._loaf['data']['type'] == 'add_player' and
              set(add_keys).issubset(loaf._loaf['data'].keys()) and
              loaf._loaf['data']['game'] != 'null' and
              loaf._loaf['data']['name'] != 'null' and
              loaf._loaf['data']['pubkey'] != 'null' and
              loaf._loaf['data']['color'] != 'null' and
              loaf._loaf['data']['sig'] != 'null'):
            return loaf.get_hash() == hash_calc

        elif (loaf._loaf['data']['type'] == 'update_pixel' and
              set(update_keys).issubset(loaf._loaf['data'].keys()) and
              loaf._loaf['data']['game'] != 'null' and
              loaf._loaf['data']['name'] != 'null' and
              loaf._loaf['data']['sig'] != 'null' and
              type(loaf._loaf['data']['x']) == int and
              type(loaf._loaf['data']['y']) == int):
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

def consensus_check(local_length, rec_length):
    if local_length < rec_length:
        return True
    else:
        return False

def consensus(chain1, chain2):
    if chain1.get_length() < chain2.get_length():
        return chain2
    else:
        return chain1

class Prompt(Cmd):
    PRINTS = ['players', 'loaf_pool', 'mined_loaves', 'blockchain', 'games',
              'current_game']

    def __init__(self):
        ''' Prompt class constructor
        '''
        super().__init__()

        self._port = port
        self._chainfile = chain_path
        self._privkey_path = privkey_path
        self._pubkey_path = pubkey_path
        self._node = Node(self._port)
        genesis_block = Block.create_block_from_dict(
            {"hash":"00001620395c8da353f5005e713fe2fee85ad63c618ad01b7dd712bc5f4cc56d",
             "height":0, "loaves":[], "data":"",
             "previous_block_hash":"-1",
             "timestamp":"2017-05-01 15:19:56.585873"})
        self._node._chain._chain = [genesis_block]

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
                    print(fail('keys do not match'))
                    self.browsing = 1
            else:
                self._privkey, self._pubkey = rsakeys.generate_keys()
                rsakeys.write_keys(self._privkey, self._pubkey,
                                   self._privkey_path, self._pubkey_path)
        else:
            print(warning('browsing mode enabled'))
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
        self._node.attach_consensus_check(consensus_check)
        self._node.attach_consensus(consensus)

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
            self._procesed_height = self.proces_chain(self._procesed_height)
        except:
            print(fail('error connecting to node'))
            raise

    def read_keys(self, priv_path, pub_path):
        return rsakeys.read_keys(priv_path, pub_path)

    def save_keys(self, privkey, pubkey, priv_path, pub_path):
        rsakeys.write_keys(privkey, pubkey, priv_path, pub_path)

    def proces_chain(self, height):
        if not height < self._node._chain.get_length() - 1:
            return height
        chain = self._node._chain._chain[height + 1:]
        for block in chain:
            if not self.proces_block(block):
                print('failed to process block of height:',
                      block.get_height())
                return height
        return self._node._chain.get_length() - 1

    def proces_block(self, block):
        for loaf in block._block['loaves']:
            if not self.proces_loaf(loaf):
                print('failed to proces loaf')
                return False
        return True

    def proces_loaf(self, loaf):
        if loaf._loaf['data']['type'] == 'new_game':
            game_name = loaf._loaf['data']['game']
            width = loaf._loaf['data']['width']
            height = loaf._loaf['data']['height']
            max_players = loaf._loaf['data']['max_players']
            if game_name in self.games.keys():
                print(fail('game already exists'))
                return False
            self.games[game_name] = Canvas(width, height, max_players)
            print(info('Created game: ' + game_name))

        elif loaf._loaf['data']['type'] == 'add_player':
            game = self.games[loaf._loaf['data']['game']]
            color = loaf._loaf['data']['color']
            name = loaf._loaf['data']['name']
            signature = loaf._loaf['data']['sig']
            pubkey = rsakeys.import_key(loaf._loaf['data']['pubkey'].encode('utf-8'))
            hashed_name = hashlib.md5(name.encode('utf-8')).digest()
            if not rsakeys.validate(pubkey, hashed_name, signature):
                print(fail('Failed to verify message'))
                return False
            if not game.add_player(name, color, pubkey):
                print(fail('failed to add player:'))
                return False
            print(info('player ' + name + ' added to game:'))

        elif loaf._loaf['data']['type'] == 'update_pixel':
            game = self.games[loaf._loaf['data']['game']]
            game_name = loaf._loaf['data']['game']
            name = loaf._loaf['data']['name']
            signature = loaf._loaf['data']['sig']
            x = loaf._loaf['data']['x']
            y = loaf._loaf['data']['y']
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
            chain_length = self._node._chain.get_length()
            prev_block = self._node._chain.get_block(chain_length-1)
            block = mine(loaves, prev_block)
            if block is None:
                print(fail('failed to mine block'))
            else:
                if self._node.add_block(block):
                    self._procesed_height = self.proces_chain(self._procesed_height)
                    if self._procesed_height == self._node._chain.get_length() - 1:
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
            print(fail('a keypair is needed to interfere with the game'))
            return
        l = args.split()
        if len(l) != 4:
            print(fail('Invalid number of arguments'))
            print(fail('Args: <game> <width> <height> <max_players> '))
            return

        if l[0] in self.games.keys():
            print(fail('Game already exists'))
            return
        try:
            loaf = Loaf({'game' : l[0], 'height' : int(l[2]),
                         'width' : int(l[1]), 'max_players' : int(l[3]),
                         'type' : 'new_game'})
            if self._node.add_loaf(loaf):
                self.do_mine('')
            else:
                print(fail('failed to add loaf to loaf pool'))
        except:
            print(fail('error creating and broadcasting loaf'))
            raise

        self.game = l[0]

    def do_change_game(self, args):
        l = args.split()
        if len(l) != 1:
            print(fail('invalid number of arguments. args: <game> <name> <color>'))
            return
        if l[0] in self.games.keys():
            self.game = l[0]
        else:
            print(warning('game' + l[0] + 'does not eist'))
            return

    def do_join_game(self, args):
        if self.browsing == 1:
            print(fail('a keypair is needed to interfere with the game'))
            return
        l = args.split()
        if len(l) != 1:
            print(fail('invalid number of arguments. args: <game>'))
            return
        if l[0] in self.games.keys():
            self.game = l[0]
            game = self.games[l[0]]
        else:
            print(warning('game ' + l[0] + ' does not eist'))
            return
        for player in self.games[self.game].players.keys():
            if self.games[self.game].players[player]['pubkey'] == self._pubkey:
                print(fail('you are already in this game as ' + self.name))
                return
        self.name = input('Name: ')
        color = input('Color: ')
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
        if self.browsing == 1:
            print(fail('a keypair is needed to interfere with the game'))
            return
        l = args.split()
        if len(l) != 2:
            print(fail('invalid number of arguments. Args: <game> <x> <y>'))
            return
        if self.game and self.name:
            game_name = self.game
            name = self.name
        else:
            print(fail('name or game not assigned'))
            return
        if self.games[game_name].update_pixel_check(name, int(l[0]), int(l[1])):
            try:
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



    def do_z(self, args):
        self._procesed_height = self.proces_chain(self._procesed_height)
        l = args.split()
        if len(l) != 0:
            print (fail('doesnt take any arguments'))
            return
        if self.game == None:
            print(warning('not in a game'))
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
                print(self.games[self.game].players)
            elif l[0] == self.PRINTS[1]:
                for loaf in list(self._node._loaf_pool.values()):
                    print(loaf.json())
            elif l[0] == self.PRINTS[2]:
                print(self._node._mined_loaves)
            elif l[0] == self.PRINTS[3]:
                print(self._node._chain.json())
            elif l[0] == self.PRINTS[4]:
                print(list(self.games.keys()))
            elif l[0] == self.PRINTS[5]:
                if not self.game:
                    print(fail('not in a game'))
                    return
                print(self.game)
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
            Chain.save_chain(self._chainfile, self._node._chain)
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