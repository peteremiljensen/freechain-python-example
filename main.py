#!/usr/bin/env python3

import datetime
import time
import argparse
from cmd import Cmd

from canvas import *
from blockchain.node import *

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

args = parser.parse_args()
port = args.port

def loaf_validator(loaf):
    hash_calc = loaf.calculate_hash()
    keys = ['color', 'name', 'type', 'x', 'y']
    try:
        if set(keys).issubset(loaf._loaf['data'].keys()):

            if loaf._loaf['data']['type'] == 'add_player' and \
               type(loaf._loaf['data']['name'])  == str:
                return loaf.get_hash() == hash_calc

            elif loaf._loaf['data']['type'] == 'update_pixel' and \
                 type(loaf._loaf['data']['color']) == str     and \
                 type(loaf._loaf['data']['name'])  == str     and \
                 type(loaf._loaf['data']['x'])     == int     and \
                 type(loaf._loaf['data']['y'])     == int:
                return loaf.get_hash() == hash_calc
        else:
            print('Mandatory keys for loaf data are not present')
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
    return True

def consensus(chain1, chain2):
    return chain2

class Prompt(Cmd):
    PRINTS = ['players', 'loaf_pool', 'mined_loaves', 'blockchain']

    def __init__(self):
        ''' Prompt class constructor
        '''
        super().__init__()

        self._port = port
        self._node = Node(self._port)
        self._procesed_height = 0

        self.game = Canvas()
        self.name = None
        self.color = None

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
            player_block_hash = self._node._chain.get_block(1).get_hash()
            ip = l[0]
            if len(l) == 2:
                self._node.connect_node(ip, l[1])
            else:
                self._node.connect_node(ip)
            while player_block_hash == self._node._chain.get_block(1).get_hash():
                time.sleep(0.2)
            self.game.players = []
            self._procesed_height = 0
            self._procesed_height = self.proces_chain(self._procesed_height)
            if self.game.add_player_check(self.name):
                self.do_mine('')
            else:
                hashes = []
                with self._node._loaf_pool_lock:
                    for loaf in self._node._loaf_pool.values():
                        if loaf._loaf['data']['name'] == self.name and \
                           loaf._loaf['data']['type'] == 'add_player':
                            hashes.append(loaf.get_hash())
                    for hash in hashes:
                        del self._node._loaf_pool[hash]
        except:
            print(fail('error connecting to node'))
            raise

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
        if loaf._loaf['data']['type'] == 'add_player':
            name = loaf._loaf['data']['name']
            if not self.game.add_player(name):
                print('failed to add player:', name)
                return False
            print(name, 'added to game')

        elif loaf._loaf['data']['type'] == 'update_pixel':
            color = loaf._loaf['data']['color']
            name = loaf._loaf['data']['name']
            x = loaf._loaf['data']['x']
            y = loaf._loaf['data']['y']
            if self.game.update_pixel(color, name, x, y):
                print('update returned true')
            else:
                print('failed to update pixel')
                return False
        else:
            print('loaf has undefined type')
            return False
        return True

    def join_game(self):
        if self.game.add_player_check(self.name):
            try:
                loaf = Loaf({'color' : None, 'name' : self.name,
                             'type' : 'add_player', 'x': None,
                             'y' : None})
                if self._node.add_loaf(loaf):
                    self.do_mine('')
            except:
                print('exception join_game')
                raise

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

    def do_change_color(self, args):
        l = args.split()
        if len(l) == 1:
            self.color = l[0]
        else:
            print('Invalid number of arguments')

    def do_draw(self, args):
        l = args.split()
        if len(l) != 2:
            print(fail('invalid number of arguments'))
            return
        if self.game.update_pixel_check(self.color, self.name, int(l[0]), int(l[1])):
            try:
                loaf = Loaf({'color' : self.color, 'name' : self.name,
                             'type' : 'update_pixel', 'x': int(l[0]),
                             'y' : int(l[1])})
                if self._node.add_loaf(loaf):
                    self.do_mine('')
                    self.game.print_canvas()
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
        self.game.print_canvas()

    def do_print(self, args):
        ''' Prints loaf pool or blockchain
        '''
        l = args.split()
        self._procesed_height = self.proces_chain(self._procesed_height)
        try:
            if l[0] == self.PRINTS[0]:
                print(self.game.players)
            elif l[0] == self.PRINTS[1]:
                for loaf in list(self._node._loaf_pool.values()):
                    print(loaf.json())
            elif l[0] == self.PRINTS[2]:
                print(self._node._mined_loaves)
            elif l[0] == self.PRINTS[3]:
                print(self._node._chain.json())
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
        prompt.name = input('Enter name: ')
        prompt.color = input('Enter color: ')
        prompt.join_game()
        prompt.cmdloop(info('Starting node on port ' + str(port) + '...'))
    except KeyboardInterrupt:
        prompt.do_quit(None)
    except SystemExit:
        pass
    except:
        print(fail('fatal error'))
        raise
