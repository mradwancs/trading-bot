import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from fetch_data import fetch_data

def main():
# Fetch stock data
    stock_symbol = 'NVDA'
    start_date = '2024-03-15'
    end_date = '2025-03-14'
    interval = '1d'  # '1d', '1wk', '1mo'
    data = fetch_data(stock_symbol, start_date, end_date, interval)

    #ensure data is not empty
    if data is None:
        print(f"Failed to fetch data for {stock_symbol}")
        return
    
    # Define initial cash
    initial_cash = 10000

    # Define SMA combinations to test
    sma_combinations = [(5,20), (10, 50), (20, 100), (50, 200)]
    best_combination = None
    best_roi = float('-inf')
    best_buy_signals = None
    best_sell_signals = None
    best_trade_log = None
    best_final_balance = None
    best_portfolio_values = None
    best_total_portfolio_value = None

    
    # Backtest strategy with different SMA combinations
    for short, long in sma_combinations:
        #check if long is greater than total data, if so skip that combination
        if long >= len(data):
            continue

        trade_log, final_balance, shares_held, portfolio_values, buy_signals, sell_signals = backtest_strategy(data, short, long, initial_cash)
        total_portfolio_value, roi = eval(data, final_balance, shares_held, initial_cash)

        if roi > best_roi:
            best_roi = roi
            best_combination = (short, long)
            best_buy_signals = buy_signals
            best_sell_signals = sell_signals
            best_trade_log = trade_log
            best_final_balance = final_balance
            best_portfolio_values = portfolio_values
            best_total_portfolio_value = total_portfolio_value
        
        print(f"=== Backtest Strategy Results for SMA{short} and SMA{long} values ===")
        print("\n".join(trade_log))
        print(f"Final balance: {final_balance:.2f}")
        print(f"Total portfolio value: {total_portfolio_value:.2f}")
        print(f"Return on investment: {roi:.2f}%\n")

    # Print best strategy results
    print("=============================")
    print("=== Best Strategy Results ===")
    print("=============================")
    print(f"Best SMA combination: SMA{best_combination[0]} and SMA{best_combination[1]}")
    print(f"Best ROI: {best_roi:.2f}%\n")
    print("\n".join(best_trade_log))
    print(f"Final balance: {best_final_balance:.2f}")
    print(f"Total portfolio value: {best_total_portfolio_value:.2f}")

    # Buy and hold strategy
    print("=====================================")
    print("=== Buy and Hold Strategy Results ===")
    print("=====================================")
    bh_shares = buy_and_hold(data, initial_cash)
    bh_total_portfolio_value, bh_roi = eval(data, 0, bh_shares, initial_cash)
    print(f"Total portfolio value: {bh_total_portfolio_value:.2f}")
    print(f"Return on investment: {bh_roi:.2f}%\n")

    # Plot best sma values with buy and sell signals
    plot_data(data, best_combination, best_buy_signals, best_sell_signals)

    # Compare best sma values to buy and hold strategy
    compare_strategies(data, best_portfolio_values, bh_total_portfolio_value)


# function for backtesting
def backtest_strategy(data, short, long, initial_cash=10000):
    cash = initial_cash
    shares_held = 0
    trade_log = []
    portfolio_values = []
    buy_signals = []
    sell_signals = []

    data[f'SMA{short}'] = data['Close'].rolling(window=short).mean()
    data[f'SMA{long}'] = data['Close'].rolling(window=long).mean()

    # Prepend NaN values for days before the 50th row to match data length
    portfolio_values.extend([None] * long)

    # loop through data starting from 50th day
    for i in range(long, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        # print(row['SMA10'].item(), row['SMA50'].item())
        # print(prev_row['SMA10'].item(), prev_row['SMA50'].item())
        # print(row['Close'].item())

        # Buy condition, i.e. when SMA10 crosses above SMA50
        if prev_row[f'SMA{short}'].item() < prev_row[f'SMA{long}'].item() and row[f'SMA{short}'].item() >= row[f'SMA{long}'].item():
            shares_bought = cash // row['Close'].item()
            shares_held += shares_bought
            cash -= shares_bought * row['Close'].item()
            trade_log.append(f"BUY {shares_bought} shares at {row['Close'].item()} on {row.name.date()}")
            buy_signals.append(row)

        # Sell condition i.e. when SMA10 crosses below SMA50
        elif row[f'SMA{short}'].item() <= row[f'SMA{long}'].item() and prev_row[f'SMA{short}'].item() > prev_row[f'SMA{long}'].item() and shares_held > 0:
            cash += shares_held * row['Close'].item()
            trade_log.append(f"SELL {shares_held} shares at {row['Close'].item()} on {row.name.date()}")
            shares_held = 0
            sell_signals.append(row)
        
        # track portfolio value per day
        portfolio_value = cash + shares_held * row['Close'].item()
        portfolio_values.append(portfolio_value)



    return trade_log, cash, shares_held, portfolio_values, buy_signals, sell_signals

# evaluate performance
def eval(data, final_balance, shares_held, initial_cash):
    # Calculate total value of shares held
    total_value = shares_held * data['Close'].iloc[-1].item()

    # Calculate total value of portfolio
    total_portfolio_value = total_value + final_balance

    # Calculate return on investment
    roi = ((total_portfolio_value - initial_cash) / initial_cash) * 100

    return total_portfolio_value, roi

# buy and hold strategy
def buy_and_hold(data, initial_cash=10000):
    # Buy and hold strategy
    initial_price = data['Close'].iloc[0].item()
    final_price = data['Close'].iloc[-1].item()

    shares_bought = initial_cash / initial_price

    # print amount of stocks bought
    print(f"BUY {shares_bought} shares at {initial_price} on {data.index[0].date()}")
    print(f"SELL {shares_bought} shares at {final_price} on {data.index[-1].date()}")
    
    return shares_bought

# Plot comparison using existing results
def compare_strategies(data, portfolio_values, bh_value):
    data = data.copy()
    data['Portfolio_Value'] = portfolio_values
    
    plt.figure(figsize=(12, 6))
    plt.plot(data['Portfolio_Value'], label='Backtest Strategy', color='blue')
    plt.axhline(y=bh_value, color='green', linestyle='--', label='Buy and Hold Strategy (Final Value)')
    plt.title('Strategy Comparison')
    plt.xlabel('Date')
    plt.ylabel('Value ($)')
    plt.legend()
    plt.show()

def plot_data(data, sma, buy_signals, sell_signals):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Close'], label='Close Price', color='black')
    plt.plot(data[f'SMA{sma[0]}'], label=f'SMA{sma[0]}', color='red')
    plt.plot(data[f'SMA{sma[1]}'], label=f'SMA{sma[1]}', color='blue')

    for buy_signal in buy_signals:
        plt.scatter(buy_signal.name, buy_signal['Close'], color='green', marker='^', s=100)
        plt.axvline(x=buy_signal.name, color='green', linestyle='--')
    for sell_signal in sell_signals:
        plt.scatter(sell_signal.name, sell_signal['Close'], color='red', marker='v', s=100)
        plt.axvline(x=sell_signal.name, color='red', linestyle='--')

    # Highlight the crossover points
    plt.title('Stock Data with Buy and Sell Signals')
    plt.xlabel('Date')
    plt.ylabel('Price')
    plt.legend(loc='best')

    plt.show()

if __name__ == '__main__':
    main()