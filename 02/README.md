In example below I just wanna share part related to key-pair generation. It was used in powerful infrastructural
solution that protects products on all levels.

#It includes:
- bech32.py - implementation for Bech32 and segwit addresses 
- bitcoin_key_gen.py - implementation for bitcoin address generator based on `fastecdsa`
- create_key_pairs.py - simple file to create 100 addresses

# Steps to install and use it locally.

- Create a venv `python -m venv venv`
- Install requirements: `pip install -r requirements.txt`
- run `python create_key_pairs.py`

