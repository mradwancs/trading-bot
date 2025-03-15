import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from fetch_data import fetch_data

def main():
# Fetch stock data
    stock_symbol = 'GOOGL'
    data = fetch_data(stock_symbol)

    #ensure data is not empty
    if data is not None:
        # Calculate moving averages
        data['SMA10'] = data['Close'].rolling(window=10).mean()
        data['SMA50'] = data['Close'].rolling(window=50).mean()
    else:
        print(f"No data found for stock symbol: {stock_symbol}")
        return
    
    initial_cash = 10000
    
    # Backtest strategy
    trade_log, final_balance, shares_held, portfolio_values, buy_signals, sell_signals = backtest_strategy(data, initial_cash)
    total_portfolio_value, roi = eval(data, final_balance, shares_held, initial_cash)
    
    print("=== Backtest Strategy Results ===")
    print("\n".join(trade_log))
    print(f"Final balance: {final_balance:.2f}")
    print(f"Total portfolio value: {total_portfolio_value:.2f}")
    print(f"Return on investment: {roi:.2f}%\n")

    # Buy and hold strategy    

    print("=== Buy and Hold Strategy Results ===")
    bh_shares = buy_and_hold(data, initial_cash)
    bh_total_portfolio_value, bh_roi = eval(data, 0, bh_shares, initial_cash)
    print(f"Total portfolio value: {bh_total_portfolio_value:.2f}")
    print(f"Return on investment: {bh_roi:.2f}%\n")

    # Plot initial data
    plot_data(data, buy_signals, sell_signals)

    # Compare strategies
    compare_strategies(data, portfolio_values, bh_total_portfolio_value)


# function for backtesting
def backtest_strategy(data, initial_cash=10000):
    cash = initial_cash
    shares_held = 0
    trade_log = []
    portfolio_values = []
    buy_signals = []
    sell_signals = []


    # Prepend NaN values for days before the 50th row to match data length
    portfolio_values.extend([None] * 50)

    # loop through data starting from 50th day
    for i in range(50, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        # print(row['SMA10'].item(), row['SMA50'].item())
        # print(prev_row['SMA10'].item(), prev_row['SMA50'].item())
        # print(row['Close'].item())

        # Buy condition, i.e. when SMA10 crosses above SMA50
        if prev_row['SMA10'].item() < prev_row['SMA50'].item() and row['SMA10'].item() >= row['SMA50'].item():
            shares_bought = cash // row['Close'].item()
            shares_held += shares_bought
            cash -= shares_bought * row['Close'].item()
            trade_log.append(f"BUY {shares_bought} shares at {row['Close'].item()} on {row.name.date()}")
            buy_signals.append(row)

        # Sell condition i.e. when SMA10 crosses below SMA50
        elif row['SMA10'].item() <= row['SMA50'].item() and prev_row['SMA10'].item() > prev_row['SMA50'].item() and shares_held > 0:
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

def plot_data(data, buy_signals, sell_signals):
    plt.figure(figsize=(12, 6))
    plt.plot(data['Close'], label='Close Price', color='black')
    plt.plot(data['SMA10'], label='SMA10', color='red')
    plt.plot(data['SMA50'], label='SMA50', color='blue')

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