# USI Winterschool 2022: creating smart contracts with Algorand + Python
# project 9, Carlos Mari carlos@carloslabs.com

# APP.PY:  April, May 2022

# this is the entry point of the webapp:
# it defines the different URI routes for Flask to serve page content through the lifecycle of the app.

import time
import configuration, secrets, mod_algorand, sqlite3

from flask import Flask, flash, session, g, json, redirect, render_template, request, url_for
from flask_restful import Resource, Api

import pyteal

# to enable cross-domain AJAX requests we need to use the Flask CORS object (see r12)
from flask_cors import CORS

bp = Flask(__name__)
apiREST = Api(bp)
CORS(bp)

bp.secret_key = secrets.token_hex(32)

# retrieve the data object for the session and repaint the screen
# for the USI demo we only have Algo and ASA
class rest_GetData(Resource):
    def get(self):
        return json.jsonify(
            algoBalance=session['algoBalance'],
            asaBalance=session['asaBalance'],
            # random hex string to prevent the GET request being cached            
            uid=str(secrets.token_hex(16))
        )

apiREST.add_resource(rest_GetData,'/rest/getdata')

@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index.html', methods=['GET', 'POST'])
def home():
    session['errorCode'] = 0     
    # move on...           
    return render_template('index.html')

@bp.route('/checklogin', methods=['GET', 'POST'])
def checklogin():
    
    session.clear()
    session['errorCode'] = 0    
    session['walletAddress'] = ''
    session['errorMessage'] = ''
    session['algoBalance'] = 0
    session['asaBalance'] = 0
    session['asaOptIn'] = False
    # move the prices to session variables
    session['priceSilver'] = configuration.PRICE_POINT_SILVER
    session['priceGold'] = configuration.PRICE_POINT_GOLD
    session['clientLevel'] = 0
    
    # 1: check the fields for content
    walletAddress = request.form['frmWalletAddr']    
    # 2) check the balance on the Algo blockchain, check the optin for MKTCOIN
    session['algoBalance'] = mod_algorand.getAlgoBalance(walletAddress)
    if (session['errorCode'] == 0):
        session['asaBalance'] = mod_algorand.getASAbalance(walletAddress) 

    # move on... 
    if (session['errorCode'] == 0):
        session["walletAddress"] = walletAddress
        return render_template('dashboard.html')
    else:
        return render_template('index.html')

# terms
@bp.route('/terms', methods=['GET', 'POST'])
def terms():
    return render_template('terms.html', pagestate = session)

# dashboard: creates the main page layout, populates the page
# and displays the available options to the user depending on the MARKETCOIN balance
@bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():          
        
    # render the dashboard and move on...
    return render_template('dashboard.html', pagestate = session)    

# trade: reads fields from the form and fires an atomic transaction
# between the buyer and the seller - one of which is always BANK

@bp.route('/trade', methods=['GET','POST'])
def trade():

    orderVolume = request.form['fVolume']
    orderType = request.form['orderType']
    secretPhrase = request.form['fPhrase']
    checkAlgoBalance = request.form['algoBalance']
    checkASABalance = request.form['asaBalance']    
    
    # 1) A naive check for order volume greater than available funds

    if (orderType == "buy") and (orderVolume > (checkAlgoBalance)):
        session['errorCode'] = 9000
        session['errorMessage'] = 'Algorand: not enough funds.'
        session['errorContext'] = 'trade()'
        return render_template('dashboard.html')
    
    if (orderType == "sell") and (orderVolume > (checkASABalance)):
        session['errorCode'] = 9010
        session['errorMessage'] = 'Marketcoin: not enough funds.'
        session['errorContext'] = 'trade()'
        return render_template('dashboard.html')           
    
    # 2) check the secret phrase to see if it matches the address        
    thisPrivateKey = mod_algorand.getPrivateFromMnemonic(secretPhrase)
    thisPublicKey = mod_algorand.getPublicFromPrivate(thisPrivateKey)
    
    if (thisPublicKey != session['walletAddress']):
        session['errorCode'] = 10050
        session['errorMessage'] = 'Wallet and passphrase do not match.'
        session['errorContext'] = 'trade()'    
        return render_template('dashboard.html')      
    
    # 3) setup the dictionary
    thisTrade = {}
    if (orderType == "buy"):
        thisTrade['buyerPublic'] = session['walletAddress']
        thisTrade['buyerPrivate'] = thisPrivateKey
        thisTrade['sellerPublic'] = configuration.THE_BANK['public']
        thisTrade['sellerPrivate'] = mod_algorand.getPrivateFromMnemonic(configuration.THE_BANK['mnemonic'])
        thisTrade['buyCurrency'] = "MKTCOIN"        
        thisTrade['sellCurrency'] = "ALGO"        
        thisTrade['xRateBuy'] = configuration.EXCHANGE_ALGO_TO_ASA
        thisTrade['xRateSell'] = configuration.EXCHANGE_ASA_TO_ALGO
        thisTrade['orderVolume'] = orderVolume
        thisTrade['amountBuy'] = orderVolume * thisTrade['xRateBuy']
        thisTrade['amountSell'] = orderVolume * thisTrade['xRateSell']
    elif (orderType == "sell"):
        thisTrade['buyerPublic'] = configuration.THE_BANK['public'] 
        thisTrade['buyerPrivate'] = mod_algorand.getPrivateFromMnemonic(configuration.THE_BANK['mnemonic'])
        thisTrade['sellerPublic'] = session['walletAddress']
        thisTrade['sellerPrivate'] = thisPrivateKey 
        thisTrade['buyCurrency'] = "ALGO"        
        thisTrade['sellCurrency'] = "MKTCOIN"   
        thisTrade['xRateBuy'] = configuration.EXCHANGE_ASA_TO_ALGO
        thisTrade['xRateSell'] = configuration.EXCHANGE_ALGO_TO_ASA 
        thisTrade['orderVolume'] = orderVolume
        thisTrade['amountBuy'] = orderVolume * thisTrade['xRateBuy']
        thisTrade['amountSell'] = orderVolume * thisTrade['xRateSell']     
    
    atm = mod_algorand.atomicTransfer(thisTrade['buyerPublic'], thisTrade['buyerPrivate'],
                                      thisTrade['sellerPublic'], thisTrade['sellerPrivate'],
                                      thisTrade['amountBuy'] , thisTrade['amountSell'])
    
    if (session['errorCode']==0):
        flash("Transaction " + str(atm) + " was completed successfully.", "info")
        if (orderType == "buy"):
            session['algoBalance'] = float(session['algoBalance']) - float(thisTrade['amountSell']) - float(session['txnFee'])
            session['asaBalance'] = float(session['asaBalance']) + float(thisTrade['amountBuy'])            
        if (orderType == "sell"):
            session['algoBalance'] = float(session['algoBalance']) + float(thisTrade['amountBuy']) - float(session['txnFee'])
            session['asaBalance'] = float(session['asaBalance']) - float(thisTrade['amountSell'])
    else:
        # an error ocurred
        flash("Error " + str(session['errorCode']) + ", " + session['errorMessage'] + ". Transaction was aborted.", "warning")        
        
    return redirect(url_for('dashboard')) 

# optin: sends a transaction for 0 MKTCOIN from the wallet, to the wallet
# this trx has the standard fee of 0.001 Algos
# SUCCESS:  httpcode of "201" if the wallet has opted in successfully
# FAIL: httpcode of 404 or 405, with verbose error message
@bp.route('/optin', methods=['GET', 'POST'])
def optin():
    # 1) retrieve the elements in the form
    secretPhrase = request.form['optInPhrase']

    # 2) check the secret phrase to see if it matches the address        
    thisPrivateKey = mod_algorand.getPrivateFromMnemonic(secretPhrase)
    thisPublicKey = mod_algorand.getPublicFromPrivate(thisPrivateKey)
    
    if (thisPublicKey != session['walletAddress']):
        session['errorCode'] = 10060
        session['errorMessage'] = 'Optin aborted: address and passphrase do not match.'
        session['errorContext'] = 'optin()' 
    else:       
        # 3) fire the "opt in transaction"    
        txnID = mod_algorand.setAsaOptIn(thisPublicKey,thisPrivateKey)
    
    return redirect(url_for('dashboard'))   

@bp.route('/spend', methods=['GET','POST'])
def spend():
    # trigger a spend Marketcoin transaction
    secretPhrase = request.form['spendPhrase']
    amountASA = request.form['spendASA']

    # 2) check the secret phrase to see if it matches the address        
    thisPrivateKey = mod_algorand.getPrivateFromMnemonic(secretPhrase)
    thisPublicKey = mod_algorand.getPublicFromPrivate(thisPrivateKey)
    theBank = configuration.THE_BANK['public']
    
    if (thisPublicKey != session['walletAddress']):
        session['errorCode'] = 10070
        session['errorMessage'] = 'Spend aborted: address and passphrase do not match.'
        session['errorContext'] = 'spend()' 
    else:       
        # 3) fire the "spend transaction"  - the recipient is always the bank  
        txnID = mod_algorand.spendASA(thisPublicKey,thisPrivateKey,theBank,amountASA)
        
    if (session['errorCode']==0):
        flash("Transaction " + str(txnID) + " was completed successfully.", "info")
        session['asaBalance'] = float(session['asaBalance']) - float(amountASA)
        session['clientLevel'] = configuration.CLIENT_LEVEL_SILVER
    else:
        # an error ocurred
        flash("Error " + str(session['errorCode']) + ", " + session['errorMessage'] + ". Transaction was aborted.", "warning")        
          
    return redirect(url_for('dashboard')) 

# test / debug button - 
# the following code is for testing a "spend Algo" transaction - it is not implemented in
# the UI of "Project Nine" - it can be easily triggered by calling the entry point 'debug'
@bp.route('/debug', methods=['GET','POST'])
def debug():

    # trigger a spend Algo transaction
    secretPhrase = request.form['spendPhrase']
    amountAlgo = request.form['spendASA']
    theNote = ''    # the tx note is empty

    # 2) check the secret phrase to see if it matches the address        
    thisPrivateKey = mod_algorand.getPrivateFromMnemonic(secretPhrase)
    thisPublicKey = mod_algorand.getPublicFromPrivate(thisPrivateKey)
    theBank = configuration.THE_BANK['public']
    
    if (thisPublicKey != session['walletAddress']):
        session['errorCode'] = 10080
        session['errorMessage'] = 'Algo spend aborted: address and passphrase do not match.'
        session['errorContext'] = 'spend()' 
    else:       
        # 3) fire the "spend transaction"  - the recipient is always the bank  
        txnID = mod_algorand.spendAlgo(thisPublicKey,thisPrivateKey,theBank,amountAlgo,theNote)
        
    if (session['errorCode']==0):
        flash("Transaction " + str(txnID) + " was completed successfully.", "info")
    else:
        # an error ocurred
        flash("Error " + str(session['errorCode']) + ", " + session['errorMessage'] + ". Transaction was aborted.", "warning")        
       
    
    return redirect(url_for('dashboard')) 

# logout view - session is cleared
@bp.route('/logout', methods=['GET', 'POST'])
def logout():
        return redirect(url_for('index'))    
