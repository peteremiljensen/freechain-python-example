from Crypto.PublicKey import RSA
from Crypto import Random
import hashlib

def generate_keys():
    rand = Random.new().read
    key = RSA.generate(1024, rand)
    pubkey = key.publickey()

    return key, pubkey

def export_key(key):
    return key.exportKey('PEM')

def import_key(key):
    return RSA.importKey(key)

def read_keys(priv_path, pub_path):
    with open(priv_path, 'r') as f:
        filekey = RSA.importKey(f.read())

    with open(pub_path, 'r') as f:
        filepubkey = RSA.importKey(f.read())

    return filekey, filepubkey

def write_keys(privkey, pubkey, priv_path, pub_path):
    with open(priv_path, 'wb') as f:
        bin_privkey = privkey.exportKey('PEM')
        f.write(bin_privkey)

    with open(pub_path, 'wb') as f:
        bin_pubkey = pubkey.exportKey('PEM')
        f.write(bin_pubkey)

def check_keys(privkey, pubkey):
    hash = hashlib.md5('hejtest'.encode('utf-8')).digest()
    signature = privkey.sign(hash, '')
    return pubkey.verify(hash, signature)

def sign(privkey, message):
    hash = hashlib.md5(message.encode('utf-8')).digest()
    return privkey.sign(hash, '')

def validate(pubkey, hash, signature):
    return pubkey.verify(hash, signature)
