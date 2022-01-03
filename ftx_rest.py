import json
import time
import datetime
import hashlib
import hmac
import configparser
from urllib import parse
from urllib.parse import urlencode

import pandas as pd
import requests

""" NOTES:
    1. Configuration for API_KEY and API_SECRET
       Update CONFIG_PATH with path to your API key file, its a configuration file in ini format as below
        [CREDENTIALS]
        API_KEY=xxxxxx-xxxxx
        API_SECRET=xxxxxxxx
    2. Default sub account
        Update DEFAULT_SUBACCOUNT in case you want to use a specific sub account
    3. Common parameters:
        FTX Supports pagination on most of the REST APIs, below parameters are common-
        start_time    false   number  filter starting time in seconds
        end_time    false   number  filter ending time in seconds
    
"""

try:
    CONFIG_PATH = "keys.ini"
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    API_KEY = config['CREDENTIALS']['API_KEY']
    API_SECRET = config['CREDENTIALS']['API_SECRET']

except:
    API_KEY = None
    API_SECRET = None

BASE_PRIMARY_URL = 'https://ftx.com/api'
BASE_URL = BASE_PRIMARY_URL

DEFAULT_SUBACCOUNT = None

""" TIME API """
_TIME = "https://otc.ftx.com/api/time"

""" SUBACCOUNT API """
# Private endpoints
_SUBACCOUNTS = "/subaccounts"
_SUBACCOUNTS_UPDATE = "/subaccounts/update_name"
_SUBACCOUNT_BALANCES = "/subaccounts/{nickname}/balances"
_SUBACCOUNT_TRANSFER = "/subaccounts/transfer"

""" Markets API"""
# Public endpoints
_MARKETS = "/markets"
_SINGLE_MARKET = "/markets/{symbol}"
_ORDER_BOOK = "/markets/{symbol}/orderbook"
_TRADES = "/markets/{symbol}/trades"
_HISTORY = "/markets/{symbol}/candles"


""" Account API"""
# Private endpoints
_ACCOUNT = "/account"
_POSITIONS = "/positions"
_LEVERAGE = "/account/leverage"


""" Wallet API """
# Public endpoints
_WALLET_COINS = "/wallet/coins"

# Private endpoints
_WALLET_COINS = "/wallet/coins"
_WALLET_BALANCES = "/wallet/balances"
_WALLET_ALL_BALANCES = "/wallet/all_balances"
_WALLET_DEPOSIT_ADDRESS = "/wallet/deposit_address/{coin}"
_WALLET_DEPOSIT_ADDRESS_LIST = "/wallet/deposit_address/list"
_WALLET_DEPOSITS = "/wallet/deposits"
_WALLET_WITHDRAWALS = "/wallet/withdrawals"
_WALLET_REQUEST_WITHDRAWAL = "/wallet/withdrawals"
_WALLET_WITHDRAWAL_FEES = "/wallet/withdrawal_fee"
_WALLET_SAVED_ADDRESSES = "/wallet/saved_addresses"
_WALLET_SIGNET_DEPOSIT = "/signet/deposits/{signet_link_id}"
_WALLET_SIGNET_WITHDRAWAL = "/signet/withdrawals/{signet_link_id}"

""" Orders API """
# Private endpoints
_ORDERS = "/orders" # same address used to get open orders market={market}
_TRIGGER_ORDER = "/conditional_orders" # same address used to get open orders  market={market}"
_ORDER_HISTORY = "/orders/history" #?market={market}
_TRIGGER_ORDER_HISTORY = "/conditional_orders/history" #  market={market}
_TRIGGER_ORDER_TRIGGERS = "/conditional_orders/{conditional_order_id}/triggers"
_MODIFY_ORDER = "/orders/{order_id}/modify"
_MODIFY_ORDER_BY_CLIENT = "/orders/by_client_id/{client_order_id}/modify"
_MODIFY_TRIGGER_ORDER = "/conditional_orders/{order_id}/modify"
_ORDER_STATUS = "/orders/{order_id}"
_ORDER_STATUS_BY_CLIENT = "/orders/by_client_id/{client_order_id}"
_CANCEL_ORDER = "/orders/{order_id}"
_CANCEL_ORDER_BY_CLIENT = "/orders/by_client_id/{client_order_id}"
_CANCEL_TRIGGER_ORDER = "/conditional_orders/{id}"

""" Fills API"""
_FILLS = "/fills" # ?market={market}"

""" Funding Payments API """
_FUNDING_PAYMENTS = "/funding_payments"

""" Stkaing API """
_STAKING = "/staking/stakes"
_UNSTAKE = "/staking/unstake_requests"
_STAKE_BALANCE = "/staking/balances"
_CANCEL_UNSTAKE = "/staking/unstake_requests/{request_id}"
_STAKING_REWARDS = "/staking/staking_rewards"
_STAKE_REQUEST = "/srm_stakes/stakes"

""" SPOT MARGIN """
_SPOT_MARGIN_HISTORY = "/spot_margin/history"
_BORROW_RATES = "/spot_margin/borrow_rates"
_LENDING_RATES = "/spot_margin/lending_rates"
_DAILY_BORROWED_SUMMARY = "/spot_margin/borrow_summary"
_SPOT_MARKET_INFO = "/spot_margin/market_info"
_MY_BORROW_HISTORY = "/spot_margin/borrow_history"
_MY_LENDING_HISTORY = "/spot_margin/lending_history"
_LENDING_OFFERS = "/spot_margin/offers" # SAME FOR SUBMITTING OFFER
_LENDING_INFO = "/spot_margin/lending_info"


api_limit_track_post = []
api_limit_track_get = []



session = requests.session()

def basic_request(method, endpoint, url_params={}, params={}, json={}, data={}):
    global api_limit_track_post
    global api_limit_track_get

    if method == 'POST':
        api_limit_track_post.append(pd.Timestamp.utcnow())
    elif method == 'GET':
        api_limit_track_get.append(pd.Timestamp.utcnow())
    
    print(endpoint)
    return session.request(method, BASE_URL + endpoint.format(**url_params), params=params, json=json, data=data).json()

def sign_payload(api_secret, ts, method, path_url, body=None):
    signature_payload = f'{ts}{method}{path_url}'.encode()
    if body:
        signature_payload = signature_payload + body
    return hmac.new(api_secret.encode(), signature_payload, 'sha256').hexdigest()

def private_request(method, endpoint, url_params={}, **kwargs):
    ts = int(time.time() * 1000)
    request = requests.Request(method, BASE_URL + endpoint.format(**url_params), **kwargs)
    prepared = request.prepare()
    print(prepared.url)
    signature = sign_payload(API_SECRET, ts, method, prepared.path_url, prepared.body)
    prepared.headers['FTX-KEY'] = API_KEY
    prepared.headers['FTX-SIGN'] = signature
    prepared.headers['FTX-TS'] = str(ts)
    if DEFAULT_SUBACCOUNT:
        prepared.headers['FTX-SUBACCOUNT'] = DEFAULT_SUBACCOUNT
    r = requests.session().send(prepared)
    return r.json()


def server_time():
    r = requests.get(_TIME).json()
    return datetime.datetime.fromisoformat(r['result'])
    
""" SUBACCOUNTS API """
def subaccounts():
    return private_request("GET", _SUBACCOUNTS)

def create_subaccount(nickname):
    '''
    nickname    true    string  nickname for the subaccount
    '''
    payload = {"nickname": nickname}
    return private_request("POST", _SUBACCOUNTS, json=payload)

def rename_subaccount(nickname, new_nickname):
    '''
    nickname    true    string  current nickname for the subaccount
    new_nickname    true    string  new  nickname for the subaccount
    '''
    payload = {"nickname": nickname, "newNickname": new_nickname}
    return private_request("POST", _SUBACCOUNTS_UPDATE, json=payload)

def delete_subaccount(nickname):
    '''
    nickname    true    string  nickname for the subaccount
    '''
    payload = {"nickname": nickname}
    return private_request("DELETE", _SUBACCOUNTS, json=payload)

def subaccount_balances(nickname):
    '''
    nickname    true    string  nickname for the subaccount
    '''
    url_params = {"nickname": nickname}
    return private_request("GET", _SUBACCOUNT_BALANCES, url_params=url_params)
    
def subaccount_transfer(coin, size, source=None, destination=None):
    '''
    coin	string	XRP	
    size	number	31431.0	
    source	string	main	name of the source subaccount. Use null or 'main' for the main account
    destination	string	sub1	name of the destination subaccount. Use null or 'main' for the main account
    '''
    json = {
            "coin": coin,
            "size": size,
            "source": source,
            "destination": destination,
            }
    return private_request("POST", _SUBACCOUNT_TRANSFER, json=json)

""" MARKETS API """
def symbols():
    return basic_request("GET", _MARKETS)
    
def quote(symbol):
    '''
    symbol true    string  Name of the trading pair
    '''
    url_params = {'symbol': symbol}
    return basic_request("GET", _SINGLE_MARKET, url_params)

def order_book(symbol, **params):
    '''
    symbol  true    string  Name of the trading pair
    depth   false   integer max 100, default 20
    '''
    url_params = {'symbol': symbol}
    return basic_request("GET", _ORDER_BOOK, url_params, params)

def trades(symbol, **params):
    '''
    symbol  true    string  Name of the trading pair
    '''
    url_params = {'symbol': symbol}
    return basic_request("GET", _TRADES, url_params, params)

def history(symbol, **params):
    '''
    symbol      true    string  Name of the trading pair
    resolution  false   integer window length in seconds. options: 15, 60, 300, 900, 3600, 14400, 86400, or any multiple of 86400 up to 30*86400
    start_time    false   number  filter starting time in seconds
    end_time    false   number  filter ending time in seconds
    '''
    url_params = {'symbol': symbol}
    return basic_request("GET", _HISTORY, url_params, params)

def account():
    return private_request("GET", _ACCOUNT)

def positions():
    return private_request("GET", _POSITIONS)

def set_leverage(leverage):
    '''
    leverage      true    integer  desired acccount-wide leverage setting
    '''
    json = {"leverage": leverage}
    return private_request("POST", _LEVERAGE, json=json)

""" Wallet API"""
def coins():
    return basic_request("GET", _WALLET_COINS)

def balances():
    return private_request("GET", _WALLET_BALANCES)

def balances_all_accounts():
    return private_request("GET", _WALLET_ALL_BALANCES)

def deposit_address(coin, method=None):
    '''
    coin	string	USDT	
    method	string	erc20	optional; for coins available on different blockchains (e.g USDT)
    '''
    return private_request("GET", _WALLET_DEPOSIT_ADDRESS, 
                        url_params={"coin": coin},
                        params={"method": method})

def deposit_history(**params):
    '''
    start_time    false   number  filter starting time in seconds
    end_time    false   number  filter ending time in seconds
    '''
    return private_request("GET", _WALLET_WITHDRAWALS, **params)

def request_withdrawal(**params):
    '''
    coin	true    string	USDTBEAR	coin to withdraw
    size	true    number	20.2	amount to withdraw
    address	true    string	0xXYZ	address to send to
    tag	    false   string	null	optional
    method	false   string	null	optional; blockchain to use for withdrawal
    password false  string	null	optional; withdrawal password if it is required for your account
    code	false   string	null	optiona; 2fa code if it is required for your account
    '''
    return private_request("POST", _WALLET_WITHDRAWALS, json=params)

def withdrawal_fees(**params):
    '''
    coin    true	string	COIN	coin to withdraw
    size	true    number	20.2	amount to withdraw
    address	true    string	0xsdxx	address to send to
    tag	    false   string	null	optional
    '''
    return private_request("GET", _WALLET_WITHDRAWAL_FEES, params=params)

def saved_addresses(**params):
    '''
    coin	false    string	ETH	optional, filters saved addresses by coin
    '''
    return private_request("GET", _WALLET_SAVED_ADDRESSES, params=params)

""" Order API"""
def open_orders(**params):
    '''
        market	false   string	BTC-0329	optional; market to limit orders
    '''
    return private_request("GET", _ORDERS, params=params)

def order_history(**params):
    '''
    market	false   string	BTC-0329	optional; market to limit orders
    side	false   string	buy	optional; buy or sell side
    orderType	false   string	limit	optional; market or limit orders
    start_time	false   number	1559881511	optional; only fetch orders created after this time
    end_time	false   number	1559901511	optional; only fetch orders created before this time
    '''
    return private_request("GET", _ORDER_HISTORY, params=params)

def open_trigger_orders(**params):
    '''
    market  false	string	XRP-PERP	optional; market to limit orders
    type	false   string	stop	optional; type of trigger order (stop, trailing_stop, or take_profit)
    '''
    return private_request("GET", _TRIGGER_ORDER, params=params)

def trigger_order_info(conditional_order_id, **params):
    '''
    conditional_order_id    true    string  xxx     Order ID of conditional order
    '''
    return private_request("GET", _TRIGGER_ORDER_TRIGGERS, 
            url_params={"conditional_order_id": conditional_order_id}, **params)

def trigger_order_history(**params):
    '''
    market      false	string	BTC-0329	optional; market to limit orders
    start_time	false   number	1559881511	optional; only fetch orders created after this time
    end_time	false   number	1559881511	optional; only fetch orders created before this time
    side	    false   string	buy	optional; valid values are buy and sell.
    type	    false   string	trailing_stop	optional; valid values are stop, trailing_stop, and take_profit.
    orderType	false   string	limit	optional; valid values are market and limit.
    '''
    return private_request("GET", _TRIGGER_ORDER_HISTORY, params=params)

def place_order(**params):
    '''
    market	        string	XRP-PERP	e.g. "BTC/USD" for spot, "XRP-PERP" for futures
    side	        string	sell	"buy" or "sell"
    price	        number	0.306525	Send null for market orders.
    type	        string	limit	"limit" or "market"
    size	        number	31431.0	
    reduceOnly	    boolean	false	optional; default is false
    ioc	boolean	    false	optional; default is false
    postOnly	    boolean	false	optional; default is false
    clientId	    string	null	optional; client order id
    rejectOnPriceBand	boolean	false	optional; if the order should be rejected if its price would instead be adjusted due to price bands
    rejectAfterTs	    number	null	optional; if the order would be put into the placement queue after this timestamp, instead reject it. If it would be placed on the orderbook after the timestamp, then immediately close it instead (as if it were, for instance, a post-only order that would have taken)
    '''
    return private_request("POST", _ORDERS, json=params)

def place_trigger_order(**params):
    '''
    market	            string	XRP-PERP	
    side	            string	sell	"buy" or "sell"
    size	            number	31431.0	
    type	            string	stop	"stop", "trailingStop", "takeProfit"; default is stop
    reduceOnly	        boolean	false	optional; default is false
    retryUntilFilled	boolean	false	Whether or not to keep re-triggering until filled. optional, default true for market orders
    
    Additional parameters for stop loss orders
    triggerPrice	number	0.306525	
    orderPrice	number	0.3063	optional; order type is limit if this is specified; otherwise market

    Additional parameters for trailing stop orders
    trailValue	number	-0.05	negative for "sell"; positive for "buy"

    Additional parameters for take profit orders
    triggerPrice	number	0.306525	
    orderPrice	number	0.3067	optional; order type is limit if this is specified; otherwise market
    '''
    return private_request("POST", _TRIGGER_ORDER, json=params)

def modify_order(order_id, **params):
    '''
    price	number	0.306525	optional; either price or size must be specified
    size	number	31431.0	optional; either price or size must be specified
    clientId	string	order1	optional; client ID for the modified order
    '''
    return private_request("POST", _MODIFY_ORDER, url_params={'order_id': order_id},
                        json=params)

def modify_order_by_client_id(client_order_id, **params):
    '''
    price	number	0.306525	optional; either price or size must be specified
    size	number	31431.0	optional; either price or size must be specified
    clientId	string	order1	optional; client ID for the modified order
    '''
    return private_request("POST", _MODIFY_ORDER_BY_CLIENT, 
                        url_params={'client_order_id': client_order_id},
                        json=params)

def modify_trigger_order(order_id, **params):
    '''
    Parameters for stop loss orders
    size	number	31431.0	
    triggerPrice	number	0.306525	
    orderPrice	number	0.3063	only for stop limit orders

    Parameters for trailing stop orders
    size	number	31431.0	
    railValue	number	-0.05	negative for sell orders; positive for buy orders

    Parameters for take profit orders
    size	number	31431.0	
    triggerPrice	number	0.306525	
    orderPrice	number	0.3067	only for take profit limit orders
    '''
    return private_request("POST", _MODIFY_TRIGGER_ORDER, url_params={"order_id": order_id}, json=params)

def order_status(order_id):
    return private_request("GET", _ORDER_STATUS, url_params={"order_id":order_id})

def order_status_by_client_id(client_order_id):
    return private_request("GET", _ORDER_STATUS_BY_CLIENT, url_params={"client_order_id":client_order_id})

def cancel_order(order_id):
    return private_request("DELETE", _CANCEL_ORDER, url_params={"order_id":order_id})

def cancel_order_by_client_id(client_order_id):
    return private_request("DELETE", _CANCEL_ORDER_BY_CLIENT, url_params={"client_order_id":client_order_id})

def cancel_trigger_order(order_id):
    return private_request("DELETE", _CANCEL_TRIGGER_ORDER, url_params={"order_id":order_id})

def cancel_all_orders(**params):
    '''
    market	                string	USDTBEAR	optional; restrict to cancelling orders only on this market
    side	                string	buy	optional; restrict to cancelling orders only on this side
    conditionalOrdersOnly	boolean	false	optional; restrict to cancelling conditional orders only
    limitOrdersOnly	boolean	false	optional; restrict to cancelling existing limit orders (non-conditional orders) only
    '''
    return private_request("DELETE", _ORDERS, json=params)


def fills(**params):
    '''
    market	string	BTC-0329	optional; market to limit fills
    start_time	number	1564146934	optional; minimum time of fills to return, in Unix time (seconds since 1970-01-01)
    end_time	number	1564233334	optional; maximum time of fills to return, in Unix time (seconds since 1970-01-01)
    order	string	null	optional; default is descending, supply 'asc' to receive fills in ascending order of time
    orderId	number	null	
    '''
    return private_request("GET", _FILLS, params=params)

def funding_payment(**params):
    '''
    start_time	number	1559881511	optional
    end_time	number	1559881711	optional
    future	string	BTC-PERP	optional
    '''
    return private_request("GET", _FUNDING_PAYMENTS, params=params)

""" Staking API"""
def get_stakes(**params):
    return private_request("GET", _STAKING, params=params)

def unstake_request(**params):
    '''
        coin	string	SRM
        size	number	0.1
    '''
    return private_request("POST", _UNSTAKE, json=params)

def stake_balance(**params):
    return private_request("GET", _STAKE_BALANCE, params=params)

def cancel_unstake_request(request_id):
    return private_request("DELETE", _CANCEL_UNSTAKE, url_params={"request_id": request_id})

def stake_rewards(**params):
    return private_request('GET', _STAKING_REWARDS, params=params)

def stake_request(**params):
    '''
    coin	string	SRM
    size	number	0.1
    '''
    return private_request("POST", _STAKE_REQUEST, json=params)

""" Margin API """

def lending_history(**params):
    '''
    start_time	number	1559881511	optional; only fetch history after this time
    end_time	number	1559901511	optional; only fetch history before this time
    '''
    return private_request("GET", _SPOT_MARGIN_HISTORY, params=params)

def borrow_rates(**params):
    return private_request("GET", _BORROW_RATES, params=params)

def lending_rates(**params):
    return private_request("GET", _LENDING_RATES, params=params)

def daily_borrow_summary(**params):
    return private_request("GET", _DAILY_BORROWED_SUMMARY, params=params)

def spot_market_info(**params):
    '''
        market  string  BTC market ie. BTC/USD
    NOTE: Will return None if spot margin is not enabled in account settings.
    '''
    return private_request("GET", _SPOT_MARKET_INFO, params=params)

def my_borrow_history(**params):
    '''
    start_time	number	1559881511	optional; only fetch history after this time
    end_time	number	1559901511	optional; only fetch history before this time
    '''
    return private_request("GET", _MY_BORROW_HISTORY, params=params)

def my_lending_history(**params):
    '''
    start_time	number	1559881511	optional; only fetch history after this time
    end_time	number	1559901511	optional; only fetch history before this time
    '''
    return private_request("GET", _MY_LENDING_HISTORY, params=params)

def lending_offers(**params):
    return private_request("GET", _LENDING_OFFERS, params=params)

def lending_info(**params):
    return private_request("GET", _LENDING_INFO, params=params)

def submit_lending_offer(**params):
    '''
    coin	string	USD	
    size	number	10.0	
    rate	number	1e-6	
    '''
    return private_request("POST", _LENDING_OFFERS, json=params)
    