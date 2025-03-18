import time
import logging
import os
import pandas as pd
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
    
    end_date = datetime.now()
    # Request enough calendar days to ensure we get at least 'long' trading days
    # A general rule: multiply by 1.5 to account for weekends and holidays
    calendar_days = int(long * 1.5)
    start_date = end_date - timedelta(days=calendar_days)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start_date,
        end=end_date
    )
    
    try:
        bars_response = data_client.get_stock_bars(request_params)
        bars_df = bars_response.df
        
        # Handle multi-index if present
        if isinstance(bars_df.index, pd.MultiIndex):
            bars_df = bars_df.reset_index(level=0, drop=True)
        
        # Sort by date to ensure chronological order
        bars_df = bars_df.sort_index()
        
        # Take only the last 'long' trading days (or all if less than 'long')
        if len(bars_df) > long:
            bars_df = bars_df.iloc[-long:]
        elif len(bars_df) < long:
            logging.warning(f"Only {len(bars_df)} days of data available, less than requested {long} days")
        
        # Make sure we have the required columns
        data = bars_df[['open', 'high', 'low', 'close', 'volume']].copy()
        
        # Calculate SMA
        data[f'SMA{short}'] = data['close'].rolling(window=short).mean()
        data[f'SMA{long}'] = data['close'].rolling(window=long).mean()
        
        return data
        
    except Exception as e:
        logging.error(f"Error fetching data: {e}\ndate: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        raise e


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
        trade(symbol, SMA_SHORT, SMA_LONG)
        time.sleep(60 * 60 * 24) # sleep for 12 hours
    
if __name__ == '__main__':
    main()