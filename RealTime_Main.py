import binance_real
import pymysql
import pytz
from datetime import datetime
#####################################################################################
conn_params = {
    'user': "tmdgh",
    'password': "tmdgh4321",
    'host': "DB IP 주소",
    'port': 3306,
    'database': "wpDB",
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
#####################################################################################
# 포지션을 업데이트하는 로직
def open_position(symbol, diff, cls_pred, exchange):
    if diff > 0.05 and cls_pred == 1:
        # 현재 보유 자산 확인
        asset = int(float(binance_real.get_available_balance()))
        
        # 현재 가격 확인
        hist_price = binance_real.get_book_buy(symbol)
        
        # 'Long' 포지션 진행
        positions = 'buy' 
        
        # 포지션 진입 (심볼, 총자산, 현재가, 롱/숏, exchange) return = 보유 개수
        positions_amount = binance_real.start_position(symbol=symbol, ASSET=asset, price=hist_price, positions=positions, exchange=exchange)
 
    elif diff < -0.05 and cls_pred == 0:
        # 현재 보유 자산 확인
        asset = int(float(binance_real.get_available_balance()))
        
        # 현재 가격 확인
        hist_price = binance_real.get_book_sell(symbol)
        
        # 'Long' 포지션 진행
        positions = 'sell' 
        
        # 포지션 진입 (심볼, 총자산, 현재가, 롱/숏, exchange)
        positions_amount = binance_real.start_position(symbol=symbol, ASSET=asset, price=hist_price, positions=positions, exchange=exchange)

    else:
        positions = None  # 조건에 맞지 않으면 포지션을 열지 않음
        positions_amount = 0

    return positions, positions_amount

def insert_db(position_his):
    try:
        # PyMySQL을 사용하여 데이터베이스 연결
        conn = pymysql.connect(**conn_params)
        cur = conn.cursor()

        # INSERT 쿼리
        insert_query = 'INSERT INTO position_table (symbol, price_before_last, last_price, realizedPnl, datetime) VALUES (%s, %s, %s, %s, %s)'

        # position_his에서 정보 추출
        if len(position_his) >= 2:
            symbol = position_his[-1]['symbol']
            price_before_last = position_his[-2]['price']
            last_price = position_his[-1]['price']
            realizedPnl = position_his[-1]['info']['realizedPnl']
            datetime_str = position_his[-1]['datetime']

            # UTC 시간을 파싱하고 한국 시간(KST, UTC+9)으로 변환
            utc_time = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')
            kst_time = utc_time.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Seoul'))

            # 데이터베이스에 삽입
            cur.execute(insert_query, (symbol, price_before_last, last_price, realizedPnl, kst_time))
            conn.commit()
        else:
            print("position_his 리스트에 충분한 데이터가 없습니다.")

    except pymysql.Error as e:
        print(f"Error: {e}")
    finally:
        # 연결 닫기
        if conn is not None:
            conn.close()
    

def close_position(symbol, positions, positions_amount, positions_count, exchange):    
    positions_count = positions_count + 1
    
    if positions_count == 5:
        if binance_real.fetch_positions(symbol) == False:
            binance_real.check_and_cancel_open_futures_orders(symbol)
            positions, positions_amount, positions_count = None, 0, 0
        else:
            exchange.cancelAllOrders(symbol)
            print('지정가 판매 주문 진행')
            binance_real.close_position(symbol, positions, positions_amount, exchange)
            position_his = binance_real.get_position_his(symbol, exchange)
            insert_db(position_his)
            positions, positions_amount, positions_count = None, 0, 0
    elif binance_real.fetch_positions(symbol) == False:
        print('손절or익절 발생 모든 OpenOrder 삭제')
        binance_real.check_and_cancel_open_futures_orders(symbol)
        positions, positions_amount, positions_count = None, 0, 0 
    else:
        print(f'{symbol}-{positions} {5-positions_count}분 남음...')
        
    return positions, positions_amount, positions_count

