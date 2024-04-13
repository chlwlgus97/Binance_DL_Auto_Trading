import pandas as pd
from datetime import datetime, timedelta
from binance.client import Client
import requests
import ccxt
from pprint import pprint
import time
import hmac
import hashlib
from urllib.parse import urlencode
#####################################################################################
# 바이낸스 Funcion 
# API 키 수정 필요
api_key = ''
api_secret = '' 
#####################################################################################

# Binance Server Time
def get_server_time():
    url = 'https://fapi.binance.com/fapi/v1/time'
    response = requests.get(url)
    data = response.json()
    server_time = int(data['serverTime'])
    server_time = datetime.fromtimestamp(server_time / 1000)

    return server_time


def get_cur_nex_wait_time():
    server_time = get_server_time()
    current_minute = server_time.replace(second=0, microsecond=0)
    next_minute =  current_minute + timedelta(minutes=1)
    wait_time = (next_minute - server_time).total_seconds()
    
    return current_minute, next_minute, wait_time


# Get Binance DataFrame
def get_data(start_date, end_date, symbol):
    client = Client(api_key=api_key, api_secret=api_secret)
    data = client.futures_historical_klines(
        symbol=symbol,
        interval='1m',
        start_str=start_date,
        end_str=end_date
    )
    COLUMNS = ['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore']
    df = pd.DataFrame(data, columns=COLUMNS)
    df['open_time'] = df.apply(lambda x: datetime.fromtimestamp(x['open_time'] // 1000), axis=1)
    df = df.drop(columns=['close_time', 'ignore'])
    df['symbol'] = symbol
    df.loc[:, 'open':'tb_quote_av'] = df.loc[:, 'open':'tb_quote_av'].astype(float)
    df['trades'] = df['trades'].astype(int)
    
    return df

def set_binance():
    # 바이낸스 선물 계좌 객체 생성
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'
        }
    })
    
    return exchange

def get_price2(symbol):
    url = f'https://fapi.binance.com/fapi/v1/ticker/price?symbol={symbol}'
    response = requests.get(url)
    data = response.json()
    return float(data['price'])


def set_leverage(exchange):
    symbol1 = 'BTC/USDT:USDT'
    symbol2 = 'ETH/USDT:USDT'
    symbol3 = 'XRP/USDT:USDT'
    leverage = 10  
    params = {'marginMode': 'isolated'}  
    
    try:
        response1 = exchange.setLeverage(leverage, symbol1, params)
        response2 = exchange.setLeverage(leverage, symbol2, params)
        response3 = exchange.setLeverage(leverage, symbol3, params)
        print('Leverage set successfully:', response1, response2, response3)
    except Exception as e:
        print('Error setting leverage:', e)
         

def generate_signature(query_string, api_secret):
    return hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

def check_and_cancel_open_futures_orders(symbol):
    base_url = "https://fapi.binance.com"
    
    # 열린 주문 조회
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }
    query_string = urlencode(params)
    signature = generate_signature(query_string, api_secret)
    params['signature'] = signature

    open_orders_url = f"{base_url}/fapi/v1/openOrders?{urlencode(params)}"
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.get(open_orders_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching open futures orders: {response.json()}")
        return

    open_orders = response.json()
    if not open_orders:
        print("No open orders.")
        return
    
    # 각 열린 주문에 대해 개별 취소 요청 실행
    for order in open_orders:
        cancel_order_url = f"{base_url}/fapi/v1/order"
        params = {
            'symbol': symbol,
            'orderId': order['orderId'],
            'timestamp': int(time.time() * 1000)
        }
        query_string = urlencode(params)
        signature = generate_signature(query_string, api_secret)
        params['signature'] = signature

        requests.delete(cancel_order_url, headers=headers, params=params)
            
def open_order_count(symbol):
    base_url = "https://fapi.binance.com"
    
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }
    query_string = urlencode(params)
    signature = generate_signature(query_string, api_secret)
    params['signature'] = signature

    open_orders_url = f"{base_url}/fapi/v1/openOrders?{urlencode(params)}"
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.get(open_orders_url, headers=headers)
    if response.status_code != 200:
        print(f"Error fetching open futures orders: {response.json()}")
        return

    open_orders = response.json()
    if len(open_orders) == 1:
        return True
    else:
        return False  
    
def close_position_market(symbol, positions, amount, exchange):
    if positions=='buy':
        exchange.createMarketSellOrder(symbol, amount)
    elif positions=='sell':   
        exchange.createMarketBuyOrder(symbol, amount)

def get_usdt_balance(exchange):
    balance = exchange.fetch_balance()
    usdt_balance = balance['total']['USDT']
    
    return usdt_balance



def start_position(symbol, ASSET, price, positions, exchange):
    orders = [None] * 3
    parts = symbol.split('USDT')
    formatted_symbol = parts[0] + '/USDT'
    type = "LIMIT" 

    if symbol == 'BTCUSDT':
        start_amount = 130
    else:
        start_amount = ASSET * 10 * 0.4

    amount = start_amount / price

    if positions == 'buy':
        op_side = 'sell'
        tp_price = price * 1.004
        sl_price = price * 0.996
    elif positions == 'sell':
        op_side = 'buy'
        tp_price = price * 0.996
        sl_price = price * 1.004

    for i, order_params in enumerate([
        {"type": type, "side": positions, "price": price},
        {"type": "TAKE_PROFIT", "side": op_side, "price": price, "params": {'stopPrice': tp_price}},
        {"type": "STOP_MARKET", "side": op_side, "price": price, "params": {'stopPrice': sl_price}}
    ]):
        try:
            # 포지션, Take Profit, Stop Loss 주문
            orders[i] = exchange.create_order(
                symbol=formatted_symbol, 
                amount=amount, 
                **order_params
            )
        except ccxt.InsufficientFunds as e:
            print(f"Insufficient Funds for order {i}: {e}")
        except Exception as e:
            print(f"An error occurred with order {i}: {e}")

    return amount    

def close_position(symbol, positions, amount, exchange):
    parts = symbol.split('USDT')
    formatted_symbol = parts[0] + '/USDT'
    order_type = "LIMIT"

    if positions=='buy':
        op_side = 'sell'
        price = get_book_sell(symbol)
    elif positions=='sell':   
        op_side = 'buy'
        price = get_book_buy(symbol)
         
    # 지정가 주문 생성
    try:
        exchange.create_order(
            symbol=formatted_symbol, 
            type=order_type, 
            side=op_side, 
            amount=amount, 
            price=price
        )
    except ccxt.InsufficientFunds as e:
        print(f"Insufficient Funds: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
        

def get_position_his(symbol, exchange):
    parts = symbol.split('USDT')
    formatted_symbol = parts[0] + '/USDT'
    position = exchange.fetchMyTrades(
        symbol=formatted_symbol
    )
    return position

def fetch_positions(symbol):
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v2/positionRisk"
    
    params = {
        'symbol': symbol,
        'timestamp': int(time.time() * 1000)
    }
    query_string = urlencode(params)
    signature = generate_signature(query_string, api_secret)
    params['signature'] = signature

    url = f"{base_url}{endpoint}?{urlencode(params)}"
    headers = {'X-MBX-APIKEY': api_key}

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        positions = response.json()
        return any(float(position['positionAmt']) != 0 for position in positions)
    return None
    
    
def get_available_balance():
    base_url = "https://fapi.binance.com"
    endpoint = "/fapi/v2/account"
    headers = {"X-MBX-APIKEY": api_key}

    params = {
        'timestamp': int(time.time() * 1000)
    }

    query_string = urlencode(params)
    signature = hmac.new(api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    params['signature'] = signature

    url = f"{base_url}{endpoint}?{urlencode(params)}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        account_info = response.json()
        return account_info.get('availableBalance', 0) # 사용 가능한 잔액 바로 반환
    return None


def get_book_buy(symbol):
    # 클라이언트 객체 생성
    client = Client(api_key, api_secret)

    # BTCUSDT 선물 거래의 최신 호가창 정보 불러오기
    depth = client.futures_order_book(symbol=symbol, limit=5)

    # Buy 1칸과 Sell 1칸 호가창 가격 출력
    buy_price = float(depth['bids'][0][0]) # 첫 번째 buy 호가

    return buy_price

def get_book_sell(symbol):
    # 클라이언트 객체 생성
    client = Client(api_key, api_secret)

    # BTCUSDT 선물 거래의 최신 호가창 정보 불러오기
    depth = client.futures_order_book(symbol=symbol, limit=5)
    
    sell_price = float(depth['asks'][0][0]) # 첫 번째 sell 호가

    return sell_price
