from binance.spot import Spot
import pandas as pd
import requests
class CryptoDataService:
    def __init__(self, api_url="https://api.binance.com/api/v3"):
        self.api_url = api_url
        self.available_pairs = []
        self.load_available_pairs()
    
    def load_available_pairs(self):
        """Load available trading pairs from Binance"""
        try:
            response = requests.get(f"{self.api_url}/exchangeInfo", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.available_pairs = [
                    s['symbol'] for s in data['symbols'] 
                    if s['status'] == 'TRADING' and s['symbol'].endswith('USDT')
                ][:100]  # Limit to top 100
                self.available_pairs.sort()
            else:
                self.available_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
        except:
            self.available_pairs = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "ADA/USDT"]
    
    def get_klines_data(self, symbol, interval, limit=500):
        """Fetch klines data from Binance"""
        try:
            # Format symbol for Binance API
            binance_symbol = symbol.replace('/', '')
            
            params = {
                'symbol': binance_symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(f"{self.api_url}/klines", params=params, timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
            
            # Convert to numeric and datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['open'] = pd.to_numeric(df['open'])
            df['high'] = pd.to_numeric(df['high'])
            df['low'] = pd.to_numeric(df['low'])
            df['close'] = pd.to_numeric(df['close'])
            df['volume'] = pd.to_numeric(df['volume'])
            
            df.set_index('timestamp', inplace=True)
            df = df[['open', 'high', 'low', 'close', 'volume']]
            
            return df

        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
