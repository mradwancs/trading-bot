import unittest
from unittest.mock import patch, MagicMock
from trade_live import check_position, get_cash, place_buy_order, place_sell_order, trade
import pandas as pd

class TestTradingBot(unittest.TestCase):

    @patch('trade_live.api.get_position')
    def test_check_position_with_position(self, mock_get_position):
        # mock a successful position response
        mock_get_position.return_value.qty = 10
        result = check_position('AAPL')
        self.assertEqual(result, 10)
    
    @patch('trade_live.api.get_position')
    def test_check_position_without_position(self, mock_get_position):
        # simulate no position (exception raised)
        mock_get_position.side_effect = Exception('No position found')
        result = check_position('NVDA')
        self.assertEqual(result, 0)
    
    @patch('trade_live.api.get_account')
    def test_get_cash(self, mock_get_account):
        # Create a mock account object
        mock_account = MagicMock()
        mock_account.cash = '10000.00'
        mock_get_account.return_value = mock_account

        # Call the function and check the result
        result = get_cash()
        self.assertEqual(result, 10000.00)
    
    @patch('trade_live.api.submit_order')
    def test_place_buy_order(self, mock_submit_order):
        # Call the function
        place_buy_order('AAPL', 5)
            
        mock_submit_order.assert_called_once_with(
            symbol='AAPL',
            qty=5,
            side='buy',
            type='market',
            time_in_force='gtc'
        )
    
    @patch('trade_live.api.submit_order')
    def test_place_sell_order(self, mock_submit_order):
        # Call the function
        place_sell_order('AAPL', 5)
            
        mock_submit_order.assert_called_once_with(
            symbol='AAPL',
            qty=5,
            side='sell',
            type='market',
            time_in_force='gtc'
        )
    
    @patch('trade_live.fetch_live_data')
    @patch('trade_live.check_position', return_value=0)
    @patch('trade_live.get_cash', return_value=10000)
    @patch('trade_live.place_buy_order')
    def test_trade_buy_signal(self, mock_place_buy_order, mock_fetch_live_data):
    
        # Simulate SMA crossover
        mock_fetch_live_data.return_value = pd.DataFrame({
            'close': [150, 152],
            'SMA5': [151, 153],
            'SMA20': [152, 152]
        }, index=pd.to_datetime(['2025-03-16', '2025-03-17']))
        
        trade('AAPL', 5, 20)
        
        # Assert buy order is placed
        mock_place_buy_order.assert_called_once()
    

    
if __name__ == '__main__':
    unittest.main()
