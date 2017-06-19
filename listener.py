#!/usr/bin/env python3

import datetime
import time
import argparse
import os
from cmd import Cmd

from freechain.node import *
from freechain.common import *

parser = argparse.ArgumentParser(description='program for testing of ' +
                                             'blockchain framework')
parser.add_argument('-p', '--port', nargs='?', default='9000',
                    help='Port for the node to use')
args = parser.parse_args()
port = args.port

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

def branching(chain1, chain2):
    if chain1.get_length() < chain2.get_length():
        return chain2
    else:
        return chain1

class Prompt(Cmd):
    PRINTS = ['loaf_pool', 'mined_loaves', 'blockchain', 'block_hash']

    def block_validator(self, block):
        hash_calc = block.calculate_hash()
        os.system('reset')
        print(self.node.get_chain().json())
        return block.get_hash() == hash_calc

    def __init__(self):
        ''' Prompt class constructor
        '''
        super().__init__()

        self._port = port
        self._node = Node(self._port)
        genesis_block = Block.create_block_from_dict(
            {"hash":"00001620395c8da353f5005e713fe2fee85ad63c618ad01b7dd712bc5f4cc56d",
             "height":0, "loaves":[], "data":"",
             "previous_block_hash":"-1",
             "timestamp":"2017-05-01 15:19:56.585873"})
        self._node.add_block(genesis_block)

        self._node.start()

        self._node.attach_loaf_validator(loaf_validator)
        self._node.attach_block_validator(self.block_validator)
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
        except:
            print(fail('error connecting to node'))
            raise

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
    ''' Program start. If no port argument is given, sets port to 9000.
        Prints error if more than one argument is given, then creates a prompt
        object and waits for user input
    '''

    prompt = Prompt()
    prompt.prompt = '(listener) '
    try:
        prompt.cmdloop(info('Starting node on port ' + str(port) + '...'))
    except KeyboardInterrupt:
        prompt.do_quit(None)
    except SystemExit:
        pass
    except:
        print(fail('fatal error'))
        raise
