import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from fetch_data import fetch_data

def main():
# Fetch stock data
    stock_symbol = 'NVDA'
    data = fetch_data(stock_symbol)

    #ensure data is not empty
    if data is not None:
        # Calculate moving averages
        data['SMA10'] = data['Close'].rolling(window=10).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
    else:
        print(f"No data found for stock symbol: {stock_symbol}")
    
    trade_log, final_balance, shares_held = backtest_strategy(data, 10000)
    print(trade_log)
    print(f"Final balance: {final_balance}")
    print(f"Shares held: {shares_held}")
    print("\n")
    total_portfolio_Value, roi = eval(data, final_balance, shares_held, 10000)
    print(f"Total portfolio value: {total_portfolio_Value}")
    print(f"Return on investment: {roi:.2f}%")

# function for backtesting
def backtest_strategy(data, initial_cash=10000):
    cash = initial_cash
    shares_held = 0
    trade_log = []

    # loop through data starting from 50th day
    for i in range(50, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        # print(row['SMA10'].item(), row['SMA50'].item())
        # print(prev_row['SMA10'].item(), prev_row['SMA50'].item())
        # print(row['Close'].item())

        # Buy condition, i.e. when SMA10 crosses above SMA50
        if prev_row['SMA10'].item() <= prev_row['SMA50'].item() and row['SMA10'].item() > row['SMA50'].item():
            shares_bought = cash // row['Close'].item()
            shares_held += shares_bought
            cash -= shares_bought * row['Close'].item()
            trade_log.append(f"BUY {shares_bought} shares at {row['Close'].item()} on {row.name.date()}")

        # Sell condition i.e. when SMA10 crosses below SMA50
        elif row['SMA10'].item() < row['SMA50'].item() and prev_row['SMA10'].item() >= prev_row['SMA50'].item() and shares_held > 0:
            cash += shares_held * row['Close'].item()
            trade_log.append(f"SELL {shares_held} shares at {row['Close'].item()} on {row.name.date()}")
            shares_held = 0


    return trade_log, cash, shares_held

# evaluate performance
def eval(data, final_balance, shares_held, initial_cash):
    # Calculate total value of shares held
    total_value = shares_held * data['Close'].iloc[-1].item()

    # Calculate total value of portfolio
    total_portfolio_value = total_value + final_balance

    # Calculate return on investment
    roi = ((total_portfolio_value - initial_cash) / initial_cash) * 100

    return total_portfolio_value, roi

if __name__ == '__main__':
    main()