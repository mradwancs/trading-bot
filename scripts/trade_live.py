import time
import logging
import os
import pandas as pd
from fetch_data import fetch_data
from dotenv import load_dotenv

# Import the new Alpaca SDK
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Load environment variables
load_dotenv()

# API credentials
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')

# trading parameters
symbol = 'AAPL'
SMA_SHORT = 5
SMA_LONG = 20

# initialize REST API
trading_client = TradingClient(API_KEY, API_SECRET, paper=True)
data_client = StockHistoricalDataClient(API_KEY, API_SECRET)

# setup logging
os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/trade_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

# check position
def check_position(symbol):
    try:
        positions = trading_client.get_all_positions()
        for position in positions:
            if position.symbol == symbol:
                return int(position.qty)
    except Exception as e:
        logging.error(f"Error checking position {e}")
        return 0

# get cash balance
def get_cash():
    account = trading_client.get_account()
    return float(account.cash)

# place a buy order
def place_buy_order(symbol, qty):
    print(f"Placing buy order for {qty} shares of {symbol} on {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Buy order placed for {qty} shares of {symbol} on {time.strftime('%Y-%m-%d %H:%M:%S')}")

    market_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side = OrderSide.BUY,
        time_in_force = TimeInForce.GTC,
    )

    trading_client.submit_order(order_data=market_order_data)

# place a sell order
def place_sell_order(symbol, qty):
    print(f"Placing sell order for {qty} shares of {symbol} on {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logging.info(f"Sell order placed for {qty} shares of {symbol} on {time.strftime('%Y-%m-%d %H:%M:%S')}")

    market_order_data = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side = OrderSide.SELL,
        time_in_force = TimeInForce.GTC,
    )

    trading_client.submit_order(order_data=market_order_data)

# fetch data based on sma long value
def fetch_live_data(symbol, short, long):
    from datetime import datetime, timedelta
    # calculate start date based on long sma value
    end_date = datetime.now()
    calendar_days = int(long * 1.5) # multiply by 1.5 to account for weekends and holidays
    start_date = end_date - timedelta(days=calendar_days)
    
    data = fetch_data(symbol, start_date, end_date, '1d')

    if data is None:
        return pd.DataFrame()

    # calculate short and long SMAs
    data[f'SMA{short}'] = data['Close'].rolling(window=short).mean()
    data[f'SMA{long}'] = data['Close'].rolling(window=long).mean()

    return data



# main trading logic
def trade(symbol, short, long):
    # fetch live data
    data = fetch_live_data(symbol, short, long)

    # Check if we have enough data
    if data.empty or len(data) < 2:
        logging.error(f"Not enough data to make trading decisions on date {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("Not enough data to make trading decisions")
        return

    # get latest data
    latest_data = data.iloc[-1]
    previous_data = data.iloc[-2]

    # check shares held and cash balance
    shares_held = check_position(symbol)
    cash = get_cash()

    # buy condition
    if previous_data[f'SMA{short}'].item() < previous_data[f'SMA{long}'].item() and latest_data[f'SMA{short}'].item() >= latest_data[f'SMA{long}'].item() and shares_held == 0:
        shares_to_buy = cash // latest_data['close'].item()
        buy_qty = int(shares_to_buy)

        if buy_qty > 0:
            place_buy_order(symbol, buy_qty)
        
    # sell condition    
    elif previous_data[f'SMA{short}'].item() > previous_data[f'SMA{long}'].item() and latest_data[f'SMA{short}'].item() <= latest_data[f'SMA{long}'].item() and shares_held > 0:
        place_sell_order(symbol, shares_held)

def main():
    while True:
        print('Attempting to trade...')
        trade(symbol, SMA_SHORT, SMA_LONG)
        time.sleep(60 * 60 * 24) # sleep for 12 hours
    
if __name__ == '__main__':
    main()