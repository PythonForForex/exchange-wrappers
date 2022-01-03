from requests.models import encode_multipart_formdata
import requests
from ftx_rest import *
import datetime
import dateutil
import json

def test_sign_payload():
    api = "LR0RQT6bKjrUNh38eCw9jYC89VDAbRkCogAc_XAm"
    secret = "T4lPid48QtjNxjLUFOcUZghD7CUJ7sTVsfuvQZF2"
    ts = 1588591511721
    method = "GET"
    path_url = "/api/markets"
    assert "dbc62ec300b2624c580611858d94f2332ac636bb86eccfa1167a7777c496ee6f" == sign_payload(secret, ts, method, path_url)
    ts = 1588591856950
    j = {"market": "BTC-PERP", "side": "buy", "price": 8500, "size": 1, "type": "limit", "reduceOnly": False, "ioc": False, "postOnly": False, "clientId": None}
    path_url = "/api/orders"
    method = "POST"
    assert "c4fbabaf178658a59d7bbf57678d44c369382f3da29138f04cd46d3d582ba4ba" == sign_payload(secret, ts, method, path_url, json.dumps(j).encode())

def test_private_request():
    a = private_request("GET", "/account")
    assert a['success']
    payload = {"leverage": 5}  
    l = private_request("POST", "/account/leverage", json=payload)
    assert l['success']
    a = private_request("GET", "/account")
    assert a['result']['leverage'] == 5


def test_server_time():
    dt = server_time()
    print(dt)
    assert dt.date() == datetime.datetime.utcnow().date()


def test_subaccounts():
    resp = create_subaccount(nickname="test_account1")
    assert resp['success']
    s = subaccounts()
    assert s['success']
    assert 'test_account1' in [x['nickname'] for x in s['result']]
    resp = rename_subaccount("test_account1", "test_account2")
    assert resp['success']
    s = subaccounts()
    assert s['success']
    assert 'test_account2' in [x['nickname'] for x in s['result']]
    resp = delete_subaccount("test_account2")
    assert resp['success']

def test_subaccount_balances():
    resp = create_subaccount(nickname="test_account1")
    b = subaccount_balances("test_account1")
    resp = delete_subaccount("test_account1")
    assert b['success']
    assert 'result' in b

def test_subaccount_transfer():
    resp = create_subaccount(nickname="test_account1")
    tr = subaccount_transfer("XRP", 0, None, "test_account1")
    resp = delete_subaccount("test_account1")
    # Will fail with - Not allowed with internal-transfers-disabled permissions
    
    assert tr['error']=='Not allowed with internal-transfers-disabled permissions'

def test_markets():
    start_len = len(api_limit_track_get)
    m = symbols()
    assert m['success']
    assert 'result' in m
    m = quote('BTC/USD')
    end_len = len(api_limit_track_get)
    assert m['success']
    assert 'result' in m
    assert m['result']['name']=='BTC/USD'
    assert end_len-start_len == 2


def test_order_book():
    o = order_book("BTC/USD", depth=30)
    assert o['success']
    assert len(o['result']['bids'])==30
    o = order_book("BTC/USD", depth=30, start_time=1559881511, end_time=1559881711)
    assert o['success']

def test_trade():
    t = trades('BTC/USD')
    assert t['success']
    assert len(t['result']) > 0
    assert "side" in t['result'][0]
    assert "size" in t['result'][0]


def test_history():
    h = history('BTC/USD', resolution=300, start_time=1641007122, end_time=1641093522)
    assert h['success']
    assert len(h['result']) >0
    assert "open" in h['result'][0]
    assert "close" in h['result'][0]


def test_account():
    a = account()
    assert a['success']
    assert "username" in a['result']
    assert "positions" in a['result']
    # Account specific test to check if private APIs are wroking
    assert a['result']['username'] == "xerxys300@gmail.com"
    p = positions()
    assert p['success']
    assert "result" in p # There will be no positions to test in demo account

def test_leverage():
    l = set_leverage(leverage=5)
    print(l)
    assert l['success']
    a = account()
    assert a['result']['leverage'] == 5

def test_coins():
    c = coins()
    assert c['success']
    assert len(c['result']) > 0

def test_balances():
    b = balances()
    assert b['success']
    assert len(b['result']) > 0
    b = balances_all_accounts()
    assert b['success']
    assert len(b['result']) > 0
    assert 'main' in b['result']

def test_deposit_address():
    d = deposit_address("USDT", "erc20")
    # Needs id verification to pass
    print(d)
    assert d['success']
    assert 'address' in d['result']

def test_deposit_history():
    d = deposit_history()
    print(d)
    assert d['success']

def test_request_withdrawals():
    # Needs permissions
    wd = request_withdrawal(coin="BTC", size=0, address="0x83a127952d266A6eA306c40Ac62A4a70668FE3BE")
    print(wd)
    assert wd['error'] == "Not allowed with withdrawal-disabled permissions"

def test_withdrwala_fees():
    f = withdrawal_fees(coin="BTC", size=0, address="0x83a127952d266A6eA306c40Ac62A4a70668FE3BE")
    print(f)
    assert f['success']

def test_saved_address():
    f = saved_addresses()
    assert f['success']

def test_open_orders():
    o = open_orders()
    assert o['success']

def test_order_history():
    o = order_history()
    assert o['success']

def test_open_trigger_orders():
    o = open_trigger_orders()
    assert o['success']

def test_trigger_order_info():
    o = trigger_order_info(333)
    assert o['error'] == "No conditional order found"

def test_trigger_order_history():
    o = trigger_order_history()
    assert o['success']

def test_place_order():
    o = place_order(market="BTC/USD", side="buy",
        price=46916.5, type="limit", size=0)
    print(o)
    assert o['error'] == "Size too small"

def test_place_trigger_order():
    o = place_trigger_order(market="BTC/USD", side="buy",
        size=0, type="stop", triggerPrice=46918)
    print(o)
    assert o['error'] == "Size too small"

def test_modify_order():
    o = modify_order(3234, price=0.3234, size=0)
    print(o)
    assert o['error'] == 'Order not found'

def test_order_status():
    o = order_status(23413)
    print(o)
    assert o['error'] == 'Order not found'

def test_cancel_order():
    o = cancel_order(234234)
    assert o['error'] == 'Order not found'
    o = cancel_all_orders()
    print(o)
    assert o['success']

def test_fills():
    f = fills(market="BTC/USD")
    print(f)
    assert f['success']

def test_stakes():
    s = get_stakes()
    print(s)
    assert s['success']

def test_unstake_request():
    s = unstake_request(coin="SRM", size=0)
    print(s)
    assert s['error']=="Size must be positive"

def test_stake_balances():
    s = stake_balance()
    print(s)
    assert s['success']
    assert len(s['result']) > 0

def test_stake_unstake_request():
    s = stake_request(coin="SRM", size=0)
    assert s['error'] == "Invalid size"

    s = unstake_request(coin="SRM", size=0)
    print(s)
    assert s['error'] == 'Size must be positive'

    s = stake_rewards()
    print(s)

    # Not working
    s = cancel_unstake_request(2343)
    print(s)
    assert s['success']

def test_spot():
    x = lending_history()
    print(x)
    assert x['success']
    assert len(x['result']) > 0

    x = borrow_rates()
    print(x)
    assert x['success']
    assert len(x['result']) > 0

    x = lending_rates()
    print(x)
    assert x['success']
    assert len(x['result']) > 0

    x = daily_borrow_summary()
    print(x)
    assert x['success']
    assert len(x['result']) > 0

    x = spot_market_info(market="BTC/USD")
    print(x)
    ## This returns None if SPOT margin is not enabled
    assert x['success']

    x = my_borrow_history()
    print(x)
    ## This returns None if SPOT margin is not enabled
    assert x['success']
    
    x = my_lending_history()
    print(x)
    ## This returns None if SPOT margin is not enabled
    assert x['success']
    
    x = lending_offers()
    print(x)
    ## This returns None if SPOT margin is not enabled
    assert x['success']

    x = lending_info()
    print(x)
    ## This returns None if SPOT margin is not enabled
    assert x['success']
    assert len(x['result']) > 0

    x = submit_lending_offer(coin="USD", size=0, rate=1e-6)
    print(x)
    assert x['success']
    
    
    


    

    


