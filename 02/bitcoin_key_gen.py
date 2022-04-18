import binascii
import hashlib

import base58
import bech32
from fastecdsa import curve, keys

sha256 = lambda x: hashlib.sha256(x).digest()
ripemd160 = lambda x: hashlib.new("ripemd160", x).digest()
hash160 = lambda x: ripemd160(sha256(x))


def private_key():
    sk = keys.gen_private_key(curve=curve.secp256k1)
    private_string = hex(sk)[2:]
    return private_string


def number_to_string(num):
    l = 32
    fmt_str = "%0" + str(2 * l) + "x"
    string = binascii.unhexlify((fmt_str % num).encode())
    assert len(string) == l, (len(string), l)
    return string


def pub_key(priv_key):
    public_key = keys.get_public_key(int(priv_key, 16), curve.secp256k1)
    return number_to_string(public_key.x) + number_to_string(public_key.y)


def get_bitcoin_address_P2PKH(priv_key):
    """
    https://en.bitcoin.it/wiki/Technical_background_of_version_1_Bitcoin_addresses
    """
    # 0 - Having a private ECDSA key
    verifying_key = pub_key(priv_key)
    # 1 - Take the corresponding public key generated with it
    # (33 bytes, 1 byte 0x02 (y-coord is even), and 32 bytes corresponding to X coordinate)
    public_key = "\04" + verifying_key.hex()
    # 2 - Perform SHA-256 hashing on the public key
    hash_public_key = hashlib.sha256(public_key.encode())
    # 3 - Perform RIPEMD-160 hashing on the result of SHA-256
    ripemd160 = hashlib.new("ripemd160")
    ripemd160.update(hash_public_key.digest())
    # 4 - Add version byte in front of RIPEMD-160 hash (0x00 for Main Network)
    rip_hash_public_key = "\00".encode() + ripemd160.digest()
    # 5 - Perform SHA-256 hash on the extended RIPEMD-160 result
    hash_rip_hash_public_key = hashlib.sha256(rip_hash_public_key).digest()
    # 6 - Perform SHA-256 hash on the result of the previous SHA-256 hash
    hash_hash_rip_hash_public_key = hashlib.sha256(hash_rip_hash_public_key).digest()
    # 7 - Take the first 4 bytes of the second SHA-256 hash. This is the address checksum
    four_symb = hash_hash_rip_hash_public_key[:4]
    # 8 - Add the 4 checksum bytes from stage 7 at the end of extended RIPEMD-160 hash from stage 4.
    # This is the 25-byte binary Bitcoin Address.
    binary_addr = rip_hash_public_key + four_symb
    # 9 - Convert the result from a byte string into a base58 string using Base58Check encoding.
    # This is the most commonly used Bitcoin Address format
    addr = base58.b58encode(binary_addr)
    return addr


def get_bitcoin_address(priv_key):  # get_bech32_address
    public_key = keys.get_public_key(int(priv_key, 16), curve.secp256k1)
    # compress public key, add prefix b'\x03' if odd, b'\x02' if even
    start_bytes = b"\x03" if public_key.y & 1 else b"\x02"
    compressed_key = start_bytes + number_to_string(public_key.x)
    # the witness version. This is 0 at the moment represented by the byte 0x00
    witver = 0x00
    # the witness program. https://github.com/bitcoin/bips/blob/master/bip-0141.mediawiki#witness-program
    witprog = hash160(compressed_key)
    # the human-readable part. This is bc for mainnet and tb for testnet
    hrp = "bc"
    return bech32.encode(hrp, witver, witprog)
