#%%
import hashlib
import hmac
from urllib.parse import urlencode

import pandas as pd
import requests


API_KEY = None
API_SECRET = None

BASE_PRIMARY_URL = 'https://api.bybit.com'
BASE_SECONDARY_URL = 'https://api.bytick.com'

BASE_URL = BASE_PRIMARY_URL


'''
NOTES

AUTH: api_key, timestamp, sign - optional - recvWindow ms - default 5000

user cancel_by_id = the rest are a bit dodgy


'''
api_limit_track_post = []
api_limit_track_get = []


#PUBLIC
_SERVERTIME = '/spot/v1/time'
_SYMBOLS = '/spot/v1/symbols'
_ORDERBOOK = '/spot/quote/v1/depth'
_ORDERBOOK_MERGED = '/spot/quote/v1/depth/merged'
_TRADES = '/spot/quote/v1/trades'
_KLINES = '/spot/quote/v1/kline'
_TICKER24HR = '/spot/quote/v1/ticker/24hr'
_TICKERPRICE = '/spot/quote/v1/ticker/price'
_BOOKTICKER = '/spot/quote/v1/ticker/book_ticker'

#PRIVATE
_ORDER = '/spot/v1/order'
_FAST_CANCEL = '/spot/v1/order/fast'
_BATCH_CANCEL = '/spot/order/batch-cancel'
_BATCH_FAST_CANCEL = '/spot/order/batch-fast-cancel'
_BATCH_CANCEL_IDS = '/spot/order/batch-cancel-by-ids'
_OPEN_ORDERS = '/spot/v1/open-orders'
_ORDER_HISTORY = '/spot/v1/history-orders'
_TRADE_HISTORY = '/spot/v1/myTrades'

_WALLET = '/spot/v1/account'


session = requests.session()

def basic_request(method, endpoint, params=None):
	global api_limit_track_post
	global api_limit_track_get

	if method == 'POST':
		api_limit_track_post.append(pd.Timestamp.utcnow())
	elif method == 'GET':
		api_limit_track_get.append(pd.Timestamp.utcnow())
	
	print(endpoint)
	return session.request(method, BASE_URL + endpoint, params=params).json()


def private_request(method, endpoint, params={}):
	global api_limit_track_post
	global api_limit_track_get

	if method == 'POST':
		api_limit_track_post.append(pd.Timestamp.utcnow())
	elif method == 'GET':
		api_limit_track_get.append(pd.Timestamp.utcnow())

	params.update(timestamp=create_ts())
	params.update(api_key=API_KEY)
	params = {k:params[k] for k in sorted(params)}

	params_string = urlencode(params)

	signature = hmac.new(bytes(API_SECRET, 'utf-8'), params_string.encode('utf-8'), hashlib.sha256).hexdigest()

	params.update(sign=signature)

	print(endpoint)
	return session.request(method, BASE_URL + endpoint, params=params).json()


def create_ts():
	return str(round(pd.Timestamp.utcnow().timestamp() * 1000))


def server_time():
	return basic_request('GET', _SERVERTIME)


def symbols():
	return basic_request('GET', _SYMBOLS)


def orderbook(symbol, **params):
	'''
	symbol 	true 	string 	Name of the trading pair
	limit 	false 	integer 	Default value is 100
	'''
	params.update(symbol=symbol)
	return basic_request('GET', _ORDERBOOK, params)


def orderbook_merged(symbol, **params):
	'''
	symbol 	true 	string 	Name of the trading pair
	scale 	false 	int 	Precision of the merged orderbook, 1 means 1 digit
	limit 	false 	integer 	Default value is 100
	'''
	params.update(symbol=symbol)
	return basic_request('GET', _ORDERBOOK_MERGED, params)


def trades(symbol, limit=60):
	return basic_request('GET', _TRADES, {'limit': limit, 'symbol': symbol})


def candlesticks(symbol, interval, **params):
	'''
	symbol 	true 	string 	Name of the trading pair
	interval 	true 	1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 12h, 1d, 1w, 1M
	limit 	false 	integer 	Default value is 1000, max 1000
	startTime 	false 	number 	Start time, unit in millisecond
	endTime 	false 	number 	End time, unit in millisecond

	'''
	params.update(symbol=symbol)
	params.update(interval=interval)
	return basic_request('GET', _KLINES, params)


def ticker_info(symbol=None):
	symbol = {'symbol': symbol} if symbol else None
	return basic_request('GET', _TICKER24HR, symbol)


def ticker_price(symbol=None):
	symbol = {'symbol': symbol} if symbol else None
	return basic_request('GET', _TICKERPRICE, symbol)


def best_bid_ask(symbol=None):
	symbol = {'symbol': symbol} if symbol else None
	return basic_request('GET', _BOOKTICKER, symbol)



''' PRIVATE ENDPOINTS '''


def place_order(**params):
	'''
	symbol 	true 	string 	Name of the trading pair
	qty 	true 	number 	Order quantity (for market orders: when side is Buy, this is in the quote currency. Otherwise, qty is in the base currency. For example, on BTCUSDT a Buy order is in USDT, otherwise it's in BTC. For limit orders, the qty is always in the base currency.)
	side 	true 	string 	Order direction
	type 	true 	string 	Order type
	timeInForce 	false 	string 	Time in force
	price 	false 	number 	Order price. When the type field is MARKET, the price field is optional. When the type field is LIMIT or LIMIT_MAKER, the price field is required
	orderLinkId 	false 	string 	User-generated order ID
		
	'''

	return private_request('POST', _ORDER, params)


def order_info(orderid):
	return private_request('GET', _ORDER, {'orderId': orderid})


def cancel_order(orderid):
	return private_request('DELETE', _ORDER, {'orderId': orderid})


def fast_cancel(symbolId, orderId):
	return private_request('DELETE', _FAST_CANCEL, locals())


def cancel_all(symbol):
	return private_request('DELETE', _BATCH_CANCEL, {'symbol': symbol})


def fast_cancel_all(symbol):
	return private_request('DELETE', _BATCH_FAST_CANCEL, {'symbol': symbol})


def cancel_by_id(orderid):
	''' Order ID, use commas to indicate multiple orderIds. Maximum of 100 ids. '''
	return private_request('DELETE', _BATCH_CANCEL_IDS, {'orderIds': orderid})


def open_orders(**params):
	return private_request('GET', _OPEN_ORDERS, params)


def order_history(**params):
	'''
	symbol 	false 	string 	Name of the trading pair
	orderId 	false 	string 	Specify orderId to return all the orders that orderId of which are smaller than this particular one for pagination purpose
	limit 	false 	integer 	Default value is 500, max 500
	'''
	return private_request('GET', _ORDER_HISTORY, params)


def trade_history(**params):
	'''
	symbol 	false 	string 	Name of the trading pair
	limit 	false 	integer 	Default value is 50, max 50
	fromId 	false 	integer 	Query begins with the trade ID
	toId 	false 	integer 	Query ends with the trade ID
	startTime 	false 	long 	Start time
	endTime 	false 	long 	End time
	'''
	return private_request('GET', _TRADE_HISTORY, params)
	

def wallet_balance():
	return private_request('GET', _WALLET)


def ws_auth():
	expires = int(create_ts()) + 1000
	signature = str(hmac.new(bytes(API_SECRET, 'utf-8'), bytes(f'GET/realtime{expires}', "utf-8"), digestmod="sha256").hexdigest())
	return {'op': 'auth', 'args': [API_KEY, expires, signature]}




# %%

# Custom functions
def maker_order(**params):
	params.update(type='LIMIT_MAKER')
	return place_order(**params)


def maker_buy(symbol, price, qty):
	params = locals()
	params.update(side='Buy')
	return maker_order(**params)


def maker_sell(symbol, price, qty):
	params = locals()
	params.update(side='Sell')
	return maker_order(**params)


def all_open_orders(**params):
	return open_orders(**params)


def open_orders_by_symbol(symbol, **params):
	params.update(symbol=symbol)
	return open_orders(**params)


def open_orders_by_id(orderid, **params):
	params.update(orderId=orderid)
	return open_orders(**params)


def balances():
	coins_resp = wallet_balance()
	#coins = {coin['coin']: {'free': coin['free'], 'total': coin['total'], 'locked': coin['locked']}for coin in coins['result']['balances']}
	coins = {'last_update': create_ts()}
	for line in coins_resp['result']['balances']:
		sym = line['coin']
		coins[f'{sym}_free'] = line['free']
		coins[f'{sym}_locked'] = line['locked']

	return coins


def pair_info():
	'''
	RETURNS 
	{'name': 'BTCUSDT',
	'alias': 'BTCUSDT',
	'baseCurrency': 'BTC',
	'quoteCurrency': 'USDT',
	'basePrecision': '0.000001',
	'quotePrecision': '0.00000001',
	'minTradeQuantity': '0.000158',
	'minTradeAmount': '10',
	'maxTradeQuantity': '4',
	'maxTradeAmount': '100000',
	'minPricePrecision': '0.01',
	'category': 1,
	'showStatus': True}
	'''



	resp = symbols()
	info = {}
	for ticker in resp['result']:
		info[ticker['name']] = ticker
	return info


def cancel_all_orders():
	orders = all_open_orders()
	try:
		order_ids = [line['orderId'] for line in orders['result']]
		if order_ids:
			cancel_by_id(','.join(order_ids))
	except Exception as e:
		print(e)


def check_api_limit():
	global api_limit_track_post
	global api_limit_track_get

	two_min_ago = pd.Timestamp.utcnow() - pd.Timedelta(minutes=2)
	api_limit_track_post = [i for i in api_limit_track_post if i > two_min_ago]
	api_limit_track_get = [i for i in api_limit_track_get if i > two_min_ago]

	post_len = len(api_limit_track_post)
	get_len = len(api_limit_track_get)

	return [get_len, post_len]

def check_micro_api_limit():
	global api_limit_track_post
	global api_limit_track_get

	one_secs_ago = pd.Timestamp.utcnow() - pd.Timedelta(seconds=1)

	post_len = len([i for i in api_limit_track_post if i > one_secs_ago])
	get_len = len([i for i in api_limit_track_get if i > one_secs_ago])

	return [get_len, post_len]



def ticker_list():
	sym = symbols()
	return [i['name'] for i in sym['result']]


def choose_optimal_server():
	global BASE_URL
	BASE_URL = BASE_PRIMARY_URL
	primary = server_performance_tests()
	BASE_URL = BASE_SECONDARY_URL
	seconday = server_performance_tests()
	if primary < seconday:
		BASE_URL = BASE_PRIMARY_URL

	print(primary, seconday)
	print(primary < seconday)


def server_performance_tests():
	server_time()
	now = pd.Timestamp.utcnow()
	for _ in range(10):
		server_time()
	return (pd.Timestamp.utcnow() - now) / 10
# %%
