# USI Winterschool 2022: creating smart contracts with Algorand + Python
# project 9, Carlos Mari carlos@carloslabs.com

# configuration:  Apr - May 2022

# The MARKETCOIN ASA
MARKETCOIN= {
    'index': 88504379,
    'params': {'creator': 'ERSFRCT6VTLUVKQWER2P4UBVX6KNAHKVV2ARBLW7KNDREVDQHQ2EYSC7FI',
    'decimals': 2,
    'default-frozen': False,
    'manager': 'ERSFRCT6VTLUVKQWER2P4UBVX6KNAHKVV2ARBLW7KNDREVDQHQ2EYSC7FI',
    'name': 'MARKETCOIN',
    'name-b64': 'TUFSS0VUQ09JTg==',
    'reserve': 'ERSFRCT6VTLUVKQWER2P4UBVX6KNAHKVV2ARBLW7KNDREVDQHQ2EYSC7FI',
    'total': 100000000,
    'unit-name': 'MKTCOIN',
    'unit-name-b64': 'TUtUQ09JTg==',
    'url': 'www.carloslabs.com/marketcoin',
    'url-b64': 'd3d3LmNhcmxvc2xhYnMuY29tL21hcmtldGNvaW4='}
    }

# Wallet addresses

# The Bank: for this demo this is the address of the webapp.
# This is NOT the reserve for MKTCOIN (see dictionary above)

# All "buy" and "sell" transactions are between THE_BANK and a client's wallet

# Wallet has opted-in and has a balance of both Algo and MKTCOIN.

THE_BANK= {
    'public': '{USERS-PUBLIC-KEY}',
    'private': '',
    'mnemonic' : '{USERS-MNEMONIC-PHRASE}'
    }

# ...and four users of the webapp

# ... some Algo and some MKTCOIN
John =  {
    'public': '{USERS-PUBLIC-KEY}',
    'private': '',
    'mnemonic' : '{USERS-MNEMONIC-PHRASE}'
    }
# ... some Algo and no MKTCOIN, has Opted In
Paul = {
    'public': '{USERS-PUBLIC-KEY}',
    'private': '',
    'mnemonic' : '{USERS-MNEMONIC-PHRASE}'
    }
# ... new wallet: no Algo, no MKTCOIN, no OptIn
George = {
    'public': '{USERS-PUBLIC-KEY}',
    'private': '',
    'mnemonic' : '{USERS-MNEMONIC-PHRASE}'
    }
# ... some Algo and no MKTCOIN, has not Opted In
Ringo = {
    'public': '{USERS-PUBLIC-KEY}',
    'private': '',
    'mnemonic' : '{USERS-MNEMONIC-PHRASE}'
}

# EXCHANGE RATES
# In a more elaborate system, the exchange rates could be floating based on 
# market forces - for this demo, they are pegged at 1:1
# Exchange rates are floats
EXCHANGE_ALGO_TO_ASA = 1
EXCHANGE_ASA_TO_ALGO = 1

# PRICE POINTS
# In a more elaborate system the products and services for sales are possibly
# stored in a DB file somewhere. The  price here is in whole ASA units
PRICE_POINT_SILVER = 1
PRICE_POINT_GOLD = 2

# MKTCOIN BALANCES FOR CLIENT TIERS: change to a very small value to
# test without going to the faucet every single time :-)
# The prices are in whole ASA units
CLIENT_LEVEL_SILVER = 1
CLIENT_LEVEL_GOLD = 2