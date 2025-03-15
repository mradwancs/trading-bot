import yfinance as yf
import socket
import logging
import time
import os

# Create a logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)
logging.basicConfig(filename='logs/fetch_data_errors.log', level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data(stock_symbol, start_date='2024-01-01', end_date='2025-01-01', interval='1d', retries=5, delay=3):
    for attempts in range(retries):
        try:
            # Fetch stock data
            stock_data = yf.download(stock_symbol, start_date, end_date, interval)

            # Check if data is empty
            if stock_data.empty:
                raise ValueError(f"No data found for stock symbol: {stock_symbol}")

            return stock_data

        except (ValueError, socket.gaierror) as e:
            attempts += 1
            logging.error(f'Attempt {attempts} failed: {e}')
            if attempts < retries:
                time.sleep(delay)
            else:
                logging.error(f"Failed to fetch data for {stock_symbol} after {retries} attempts")
        except Exception as e:
            logging.error(f"An error occurred: {e}")
            break
        
        return None