from bitcoin_key_gen import get_bitcoin_address, private_key


def get_key_pairs():
    """
    simple function to create  private key based on secp256k1 curve and then create bitcoin address based on this key
    :return: private key(str), bitcoin_address(str)
    """
    priv_key = private_key()
    bitcoin_address = get_bitcoin_address(priv_key)
    return priv_key, bitcoin_address


for i in range(100):
    priv_key, bitcoin_address = get_key_pairs()
    print(bitcoin_address)
