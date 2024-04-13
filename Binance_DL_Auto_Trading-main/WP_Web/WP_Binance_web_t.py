from binance.client import Client
from binance.exceptions import BinanceAPIException
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text
import logging
from datetime import datetime, timedelta
import time
import ccxt

# 로깅 설정
logging.basicConfig(level=logging.INFO)

# Binance API 키와 시크릿 설정
api_key = '' 
api_secret = ''

# 데이터베이스 연결 정보
db_connection_string = "mysql+pymysql://?:??:?/?"

# Binance 클라이언트 인스턴스화
client = Client(api_key, api_secret)

# cctx를 사용해서 선물거래 계좌 객체 생성
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

def update_or_insert_dataframe(df, table_name, engine, unique_column):
    """
    데이터프레임의 내용을 데이터베이스 테이블에 업데이트하거나 삽입합니다.
    이미 있는 데이터는 업데이트하고, 새로운 데이터는 삽입합니다.
    """
    with engine.connect() as connection:  # 연결 생성
        transaction = connection.begin()  # 트랜잭션 시작
        try:
            for _, row in df.iterrows():
                keys = list(row.keys())
                values = [row[key] for key in keys]  # 값의 리스트 생성
                update_statement = ", ".join([f"{key}=VALUES({key})" for key in keys if key != unique_column])
                # placeholders = ", ".join([f":{key}" for key in keys])  # placeholders 수정
                sql_query = f"""INSERT INTO {table_name} ({", ".join(keys)}) VALUES ({", ".join([':' + key for key in keys])})
                    ON DUPLICATE KEY UPDATE {update_statement};"""
                insert_statement = text(sql_query)
                # 딕셔너리를 사용하여 파라미터 전달
                connection.execute(insert_statement, {key: value for key, value in zip(keys, values)})
            transaction.commit()  # 트랜잭션 커밋
        except Exception as e:
            transaction.rollback()  # 에러 발생 시 롤백
            logging.error(f"An error occurred during database operation: {e}")
            raise

# def delete_stale_positions(engine, seconds_stale=5):
#     """
#     특정 시간 동안 업데이트되지 않은 포지션을 데이터베이스에서 삭제합니다.
#     """
#     with engine.connect() as connection:
#         stale_time_limit = datetime.now() - timedelta(seconds=seconds_stale)
#         try:
#             connection.execute(
#                 text("DELETE FROM filtered_positions WHERE updated_at < :stale_time_limit"),
#                 {"stale_time_limit": stale_time_limit}
#             )
#             logging.info("Stale positions successfully deleted from the database.")
#         except Exception as e:
#             logging.error(f"An error occurred during deleting stale positions: {e}")

def fetch_and_store_data():
    try:
        # 계좌 정보 가져오기
        account_info = client.futures_account()

        # assets와 positions 정보를 데이터프레임으로 변환
        assets_df = pd.DataFrame(account_info['assets'])
        positions_df = pd.DataFrame(account_info['positions'])

        # 필터링
        assets_df = assets_df[assets_df['walletBalance'].astype(float) > 0]
        positions_df = positions_df[positions_df['entryPrice'].astype(float) > 0]
        
        # Long/Short 포지션 타입 추가
        positions_df['positionType'] = positions_df['positionAmt'].astype(float).apply(lambda x: 'Long' if x > 0 else 'Short' if x < 0 else 'Flat')
        
        # 현재 시간 추가
        current_time = datetime.now()
        assets_df['updated_at'] = current_time
        positions_df['updated_at'] = current_time
        
        # 데이터베이스에 저장
        engine = create_engine(db_connection_string)
        
        # 데이터 업데이트 또는 삽입
        update_or_insert_dataframe(assets_df, 'filtered_assets', engine, 'asset')
        update_or_insert_dataframe(positions_df, 'filtered_positions', engine, 'symbol')

        # 종료된 포지션 삭제
        # delete_stale_positions(positions_df['symbol'].unique(), engine)

        logging.info("Data successfully stored in the database.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def fetch_and_store_pnl():
    try:
        # 심볼별 PNL 계산
        symbols = ["XRP/USDT", "BTC/USDT", "ETH/USDT"]
        since = 1708659300000  # 기준 시간 설정
        total_realized_pnl = 0

        for symbol in symbols:
            trades = exchange.fetchMyTrades(symbol=symbol, since=since)
            realized_pnl = sum(float(trade['info']['realizedPnl']) for trade in trades)
            total_realized_pnl += realized_pnl

        # 현재 시간
        current_time = datetime.now()

        # 총 PNL을 데이터베이스에 저장
        engine = create_engine(db_connection_string)
        pnl_df = pd.DataFrame({
            'total_pnl': [total_realized_pnl],
            'updated_at': [current_time]
        })
        pnl_df.to_sql('daily_pnl', con=engine, if_exists='append', index=False, method='multi', chunksize=1000)

        logging.info("PNL data successfully stored in the database.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main_loop():
    # 데이터베이스 연결 설정
    engine = create_engine(db_connection_string)
    while True:
        fetch_and_store_data()  # 계좌 정보 수집 및 저장
        fetch_and_store_pnl()  # PNL 계산 및 저장
        # delete_stale_positions(engine, seconds_stale=5)  # 5초 동안 업데이트되지 않은 포지션 삭제
        print('Run Complete')
        time.sleep(5)  # 5초 간격으로 실행

# 메인 루프 실행
if __name__ == "__main__":
    main_loop()