#!/usr/bin/env python3

import datetime
import time
import argparse
from cmd import Cmd

from blockchain.node import *
from blockchain.common import *

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
parser.add_argument('-f', '--file', nargs='?',
                    help='Path to file containing a blockchain to load' +
                    'if the file does not eists, one is created')
args = parser.parse_args()
port = args.port
file = args.file

def loaf_validator(loaf):
    hash_calc = loaf.calculate_hash()
    return loaf.get_hash() == hash_calc

def block_validator(block):
    hash_calc = block.calculate_hash()
    return block.get_hash() == hash_calc and \
           hash_calc[:4] == '0000'

def mine(loaves, prev_block):
    height = prev_block.get_height() + 1
    previous_block_hash = prev_block.get_hash()
    timestamp = str(datetime.datetime.now())
    nounce = 0
    block = None
    while True:
        block = Block(loaves, height, previous_block_hash, timestamp, nounce)
        if block.get_hash()[:4] == '0000':
            return block
        nounce += 1

    if block.validate():
        return block
    else:
        print(fail('block could not be mined'))
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
    PRINTS = ['loaf_pool', 'mined_loaves', 'blockchain', 'block_hash']

    def __init__(self):
        ''' Prompt class constructor
        '''
        super().__init__()

        self._port = port
        self._file = file
        self._node = Node(self._port)

        if file and os.path.exists(self._file):
            chain = Chain.read_chain(self._file)

            if not chain.validate():
                self._file = None
                print(fail('Loaded blockchain is not valid'))
                self.do_quit(args)

            for i in range(1, chain.get_length()):
                if not self._node.add_block(chain.get_block(i)):
                    print(warning('Block of height ' + str(chain.get_block(i).get_height())+\
                                  'read from file, could not be added. '))
                    self.do_quit(args)

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
        except:
            print(fail('error connecting to node'))
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
                    self._node.broadcast_block(block)
                else:
                    print(fail('failed to add block'))
        except:
            print(fail('error trying to mine'))
            raise

    def do_loaf(self, args):
        ''' Parses the argument to get loaf data, creates a loaf from data,
            adds loaf to loaf pool and broadcasts the loaf
        '''
        l = args.split()
        if len(l) != 1:
            print(fail('invalid number of arguments'))
            return
        try:
            loaf = Loaf({'string': l[0]})
            if self._node.add_loaf(loaf):
                self._node.broadcast_loaf(loaf)
            else:
                print(fail('failed to add loaf to loaf pool'))
        except:
            print(fail('error creating and broadcasting loaf'))
            raise

    def do_loafbomb(self, args):
        ''' Does as do_loaf, but does it a number of times, depending on the
            number given as the second argument
        '''
        l = args.split()
        if len(l) != 2:
            print(fail('invalid number of arguments'))
            return
        try:
            for i in range(int(l[1])):
                loaf = Loaf({'string': l[0]+str(i)})
                if self._node.add_loaf(loaf):
                    self._node.broadcast_loaf(loaf)
                else:
                    print(fail('failed to add loaf to loaf pool'))
        except:
            print(fail('error creating and broadcasting loaf'))
            raise

    def do_print(self, args):
        ''' Prints loaf pool or blockchain
        '''
        l = args.split()
        try:
            if l[0] == self.PRINTS[0]:
                for loaf in list(self._node._loaf_pool.values()):
                    print(loaf.json())
            elif l[0] == self.PRINTS[1]:
                print(self._node._mined_loaves)
            elif l[0] == self.PRINTS[2]:
                print(self._node._chain.json())
            elif l[0] == self.PRINTS[3]:
                if len(l) != 2:
                    print(fail('invalid number of arguments'))
                else:
                    if self._node._chain.get_length() > int(l[1]):
                        print(self._node._chain.get_block(int(l[1])).get_hash())
                    else:
                        print(fail('Blockchain does not contain a block of ' +
                                   'height ' + str(l[1])))
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
        if self._file:
            Chain.save_chain(self._file, self._node._chain)
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
