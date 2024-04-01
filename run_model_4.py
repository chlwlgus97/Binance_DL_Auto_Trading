import asyncio
import pandas as pd
from datetime import timedelta
import numpy as np
import joblib
import time
from tensorflow.keras.models import load_model
import warnings
warnings.filterwarnings("ignore")
#####################################################################################
# Import Relational File
import binance_real as binance_real
import preprocess_
import trading_logic_real as trading_logic_real
#####################################################################################
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT']
REG_MODEL_PATH = '/home/zero/test1/FinalProject/model/reg_model'
CLS_MODEL_PATH = '/home/zero/test1/FinalProject/model/cls_model'
SCALER_TARGET_PATH = '/home/zero/test1/FinalProject/scaler'
SEQUENCE_LENGTH = 20
ASSET = 0
positions = {'BTCUSDT': None, 'ETHUSDT': None, 'XRPUSDT': None}
positions_amount = {'BTCUSDT': 0, 'ETHUSDT': 0, 'XRPUSDT': 0}
positions_count = {'BTCUSDT': 0, 'ETHUSDT': 0, 'XRPUSDT': 0}
#####################################################################################
def reg_diff(reg_predictions_dict):
    # BTC 변동률 계산
    btc_diff = ((reg_predictions_dict['BTCUSDT'][5] - reg_predictions_dict['BTCUSDT'][0]) / reg_predictions_dict['BTCUSDT'][0]) * 100
    
    # ETH 변동률 계산
    eth_diff = ((reg_predictions_dict['ETHUSDT'][5] - reg_predictions_dict['ETHUSDT'][0]) / reg_predictions_dict['ETHUSDT'][0]) * 100
    
    # XRP 변동률 계산
    xrp_diff = ((reg_predictions_dict['XRPUSDT'][5] - reg_predictions_dict['XRPUSDT'][0]) / reg_predictions_dict['XRPUSDT'][0]) * 100
        
    return btc_diff, eth_diff, xrp_diff


def cls_value(cls_predictions_dict):
    if cls_predictions_dict['BTCUSDT'][0] > 0.5:
        cls_btc = 1
    else:
        cls_btc = 0
    
    if cls_predictions_dict['ETHUSDT'][0] > 0.5:
        cls_eth = 1
    else:
        cls_eth = 0

    if cls_predictions_dict['XRPUSDT'][0] > 0.5:
        cls_xrp = 1
    else:
        cls_xrp = 0    
    
    return cls_btc, cls_eth, cls_xrp
    



async def main_process(): 
    global ASSET
    global positions, positions_amount, positions_count
    
    # 모델 로드
    reg_model = load_model(f'{REG_MODEL_PATH}')
    cls_model = load_model(f'{CLS_MODEL_PATH}')
    
    # 바이낸스 API 설정
    exchange = binance_real.set_binance()
    
    # 레버리지 설정
    binance_real.set_leverage(exchange)
    
    # 바이낸스 시간
    current_minute, next_minute, wait_time = binance_real.get_cur_nex_wait_time()
    
    if(wait_time < 15):
        print(f'다음 {wait_time}초 기다리는중...')
        time.sleep(wait_time)
        current_minute, next_minute, wait_time = binance_real.get_cur_nex_wait_time()
        
    # 과거 t분 시간 저장
    t = 45
    hist_time_60 = current_minute - timedelta(minutes=t)
    temp_end = current_minute - timedelta(minutes=1)
    start_str = str(int(hist_time_60.timestamp() * 1000))
    end_str = str(int(temp_end.timestamp() * 1000))
    
    
    data_frames = {}
    for symbol in SYMBOLS:
        df = binance_real.get_data(start_str, end_str, symbol)
        data_frames[symbol] = df
    
    ASSET = binance_real.get_usdt_balance(exchange)
    print(f'시드머니 : {ASSET}')
    
    count = 0
    while count < 60:
        current_minute, next_minute, wait_time = binance_real.get_cur_nex_wait_time()
         
        print(f'다음 {wait_time}초 기다리는중...')
        time.sleep(wait_time)    
        
        start_str = str(int(current_minute.timestamp() * 1000))
        end_str = str(int(next_minute.timestamp() * 1000)) 
        
        reg_X_final = []
        reg_X_final_symbol = []
        cls_X_final = []
        cls_X_final_symbol = []        
        
        for symbol in SYMBOLS:
            df_real = binance_real.get_data(start_str, end_str, symbol)
            data_frames[symbol] = pd.concat([data_frames[symbol], df_real], ignore_index=True)
            data_frames[symbol] = data_frames[symbol].drop(df.index[0])
            # 전처리
            reg_X, reg_X_symbol = preprocess_.reg_preprocess(data_frames[symbol], symbol)
            reg_X_final.extend(reg_X)
            reg_X_final_symbol.extend(reg_X_symbol)
            cls_X, cls_X_symbol = preprocess_.cls_preprocess(data_frames[symbol], symbol)
            cls_X_final.extend(cls_X)
            cls_X_final_symbol.extend(cls_X_symbol)
            
            
        reg_X_final = np.array(reg_X_final)
        reg_X_final_symbol = np.array(reg_X_final_symbol)
        cls_X_final = np.array(cls_X_final)
        cls_X_final_symbol = np.array(cls_X_final_symbol)        
        

        # 모델 예측
        reg_predictions = reg_model.predict([reg_X_final, reg_X_final_symbol])
        cls_predictions = cls_model.predict([cls_X_final, cls_X_final_symbol])
        reg_predictions_dict = {}
        cls_predictions_dict = {}

        for symbol in SYMBOLS:
            reg_test_indices = np.where(reg_X_final_symbol[:, SYMBOLS.index(symbol)] == 1)[0]
            cls_test_indices = np.where(cls_X_final_symbol[:, SYMBOLS.index(symbol)] == 1)[0]
            
            scaler_load_path = f'{SCALER_TARGET_PATH}/scaler_target_{symbol}.save'
            scaler_target = joblib.load(scaler_load_path)
            # 단일 예측값을 추출하여 저장
            reg_prediction = scaler_target.inverse_transform(reg_predictions[reg_test_indices].reshape(-1, 1)).flatten()
            reg_predictions_dict[symbol] = reg_prediction
            
            cls_predictions_dict[symbol] = cls_predictions[cls_test_indices]
        

        
        btc_diff, eth_diff, xrp_diff = reg_diff(reg_predictions_dict)
        cls_btc, cls_eth, cls_xrp = cls_value(cls_predictions_dict)  
        
        print(btc_diff, eth_diff, xrp_diff)  
        print(cls_btc, cls_eth, cls_xrp)
        print(f'시간 : {next_minute}')
        
        
                
        for symbol, diff, cls_pred in [('BTCUSDT', btc_diff, cls_btc), ('ETHUSDT', eth_diff, cls_eth), ('XRPUSDT', xrp_diff, cls_xrp)]:
            if positions[symbol] is None:  # 현재 포지션이 없는 경우
                # Open Order 확인
                if binance_real.open_order_count(symbol) == True:
                    print('지정가 실패. 시장가 던짐')
                    binance_real.close_position_market(symbol, positions, positions_amount, exchange)
                    exchange.cancelAllOrders(symbol)
                    positions[symbol], positions_amount[symbol], positions_count[symbol] = None, 0, 0
                binance_real.check_and_cancel_open_futures_orders(symbol)

                # 포지션 진입
                positions[symbol], positions_amount[symbol] = trading_logic_real.open_position(symbol, diff, cls_pred, exchange)
            else:  
                # 포지션 종료(5분)
                positions[symbol], positions_amount[symbol], positions_count[symbol] = trading_logic_real.close_position(
                    symbol
                    , positions[symbol]
                    , positions_amount[symbol]
                    , positions_count[symbol]
                    , exchange
                    )
        
        count = count + 1
        
           
async def main():
    await main_process()

if __name__ == "__main__":
    asyncio.run(main())