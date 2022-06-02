# USI Winterschool 2022: creating smart contracts with Algorand + Python
# project 9, Carlos Mari carlos@carloslabs.com

# mod-algorand:  Apr - May 2022

from algosdk import account, error, mnemonic, transaction
from algosdk.constants import microalgos_to_algos_ratio
from algosdk.v2client import algod
from algosdk.future.transaction import AssetTransferTxn, PaymentTxn

from flask import session, g
import configuration

def algod_client():
    algo_address = "https://testnet-algorand.api.purestake.io/ps2"
    algo_token = "{YOUR-PURESTAKE-API-KEY}"
    headers = {
        "X-API-Key": algo_token,
    }

    return algod.AlgodClient(algo_token, algo_address, headers)

# getPublicFromPrivate: gets the public key from the private key
# used to check if the "public key" used to login, is the corresponding "private key"
def getPublicFromPrivate(privateKey):
    try:
        getPublicFromPrivate = account.address_from_private_key(privateKey)
    except Exception as err:
        session['errorCode'] = 9004
        session['errorMessage'] = str(err)
        session['errorContext'] = 'getPublicFromPrivate()'  
        return(0) 
        
    return(getPublicFromPrivate)

# getPrivateFromMnemonic: return the private key from the user's mnemonic (success)
# or 0 (fail)
# As in a real wallet, the secret key is not used but the 25 word mnemonic
def getPrivateFromMnemonic(passphrase):
    try:
        getPrivateFromMnemonic = mnemonic.to_private_key(passphrase)
    except Exception as err:
        session['errorCode'] = 9004
        session['errorMessage'] = str(err)
        session['errorContext'] = 'getPrivateFromMnemonic()'  
        return(0)          
         
    return(getPrivateFromMnemonic)           

# getAlgoBalance: return a balance for an existing wallet
# if address does not exist, returns zero and error msg

def getAlgoBalance(address):
    newAlgo = algod_client()
    getAlgoBalance = 0  
    try:
        account_info = newAlgo.account_info(address)
        getAlgoBalance = '{0:.4F}'.format((account_info.get('amount') / microalgos_to_algos_ratio)) 
        session['algoBalance'] = getAlgoBalance
    except Exception as err:
        session['errorCode'] = 10001
        session['errorMessage'] = 'Address does not exist in blockchain'
        session['errorContext'] = 'getASAbalance()'
        session['algoBalance'] = 0  
        return(0)           
       
    return(getAlgoBalance)

# getASAbalance: checks the blockchain for the assetID
def getASAbalance(address):
    newAlgo = algod_client()  
    getASAbalance = 0   # default value if ASA not opted in
    session['asaBalance'] = getASAbalance    
        
    try:
        account_info = newAlgo.account_info(address)
    except Exception as err:
        session['errorCode'] = 10004
        session['errorMessage'] = 'Address does not exist in blockchain'
        session['errorContext'] = 'getASAbalance()'  
        return(0) 

    idx = 0
    
    for k in account_info['assets']:
        this_asset = account_info['assets'][idx]
        idx += 1        
        if (this_asset['asset-id'] == configuration.MARKETCOIN['index']):
            getASAbalance = '{0:.2F}'.format((this_asset['amount'] / 100))
            session['asaBalance'] = getASAbalance
            session['asaOptIn'] = True
            break

    return(getASAbalance)

# setAsaOptIn: the user opt-in for the ASA
# send and receive a txn for 0 MKTCOIN to the user's wallet
# It returns the TX ID (string) if success; or (None)) and error message, if fail
def setAsaOptIn(recipientPublicKey,recipientPrivateKey):
    retval = ''
    newAlgo = algod_client()
    params = newAlgo.suggested_params()
    tx = AssetTransferTxn(recipientPublicKey, params, recipientPublicKey, 0, configuration.MARKETCOIN['index'])
    sigTx = tx.sign(recipientPrivateKey)

    try:
        retval = newAlgo.send_transaction(sigTx)
    except Exception as err:
        session['errorCode'] = 10008
        session['errorMessage'] = str(err)
        session['errorContext'] = 'setAsaOptIn()' 
        return(0)                           
 
    return(retval)

# spendAlgo:
# send and receive a txn for ASAs from the user's wallet - most likely to THE_BANK
# It returns the TX ID (string) if success; or (None)) and error message, if fail
def spendAlgo(senderPublicKey,senderPrivateKey,recipientPublicKey,amountAlgo,txNote=None):
    retval = ''
    newAlgo = algod_client()
    params = newAlgo.suggested_params()
    precision = 1e6

    # amountAlgo = (float(amountAlgo) * int(precision)) - params.min_fee    # ALGO to micros, minus txn fee    
    amountAlgo = 0
    tx = PaymentTxn(senderPublicKey, params, recipientPublicKey, amountAlgo, None, txNote)
    sigTx = tx.sign(senderPrivateKey)

    try:
        retval = newAlgo.send_transaction(sigTx) 
    except Exception as err:
        session['errorCode'] = 10038
        session['errorMessage'] = str(err)
        session['errorContext'] = 'spendAlgo()' 
        return(0)                           
 
    return(retval)

# spendASA:
# send and receive a txn for ASAs from the user's wallet - most likely to THE_BANK
# It returns the TX ID (string) if success; or (None)) and error message, if fail
def spendASA(senderPublicKey,senderPrivateKey,recipientPublicKey,amountASA):
    retval = ''
    newAlgo = algod_client()
    params = newAlgo.suggested_params()
    precisionASA = 100

    amountASA = (int(amountASA) * int(precisionASA))  

    tx = AssetTransferTxn(senderPublicKey,params,recipientPublicKey, amountASA,configuration.MARKETCOIN['index'])
    sigTx = tx.sign(senderPrivateKey)

    try:
        retval = newAlgo.send_transaction(sigTx) 
    except Exception as err:
        session['errorCode'] = 10028
        session['errorMessage'] = str(err)
        session['errorContext'] = 'spendASA()' 
        return(0)                           
 
    return(retval)

#   An atomic transfer: "buyer" sends ALGO to "seller" and gets MKTCOIN back
#   By reversing "buyer" and "seller" this code can handle  BUY and SALE trades

# Returns   : Transaction ID
#           : "0" (as string) and error message if fail
def atomicTransfer(buyerPublic, buyerPrivate, sellerPublic, sellerPrivate, amountAlgo, amountASA):
    
    newAlgo = algod_client()
    params = newAlgo.suggested_params()
    precision = 1e6
    precisionASA = 100
    
    amountAlgo = (float(amountAlgo) * int(precision))     # ALGO to micros, minus txn fee
    amountASA = (float(amountASA) * int(precisionASA))                      # MKTCOIN to cents, no txn fee

    amountAlgo = int(amountAlgo)    #rounding
    amountASA = int(amountASA)      #rounding        
    
    session['txnFee'] = (params.min_fee / precision)                      # save the fee in a session var, for use later
    
    txnNote = ''
    # 1st part: send Algos from the buyer to the seller
    unsigned_txn_1 = PaymentTxn(buyerPublic, params, sellerPublic, amountAlgo, None, txnNote)
    unsigned_txn_2 = AssetTransferTxn(sellerPublic,params,buyerPublic, amountASA,configuration.MARKETCOIN['index'])

    tx_group_id = transaction.calculate_group_id([unsigned_txn_1,unsigned_txn_2])
    unsigned_txn_1.group = tx_group_id
    unsigned_txn_2.group = tx_group_id
    
    signed_txn_1 = unsigned_txn_1.sign(buyerPrivate)
    signed_txn_2 = unsigned_txn_2.sign(sellerPrivate)
    
    signed_tx_group = [signed_txn_1,signed_txn_2]
    
    try:
        retval = newAlgo.send_transactions(signed_tx_group)
    except Exception as err:
        session['errorCode'] = 10030
        session['errorMessage'] = str(err)
        session['errorContext'] = 'atomicTransfer()'        
        retval = "0"

    return(retval) 