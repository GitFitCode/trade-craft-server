import math
import pandas as pd
from datetime import datetime, timedelta
from providers import data_provider
from config import config


class MovingAverageCrossoverStrategy:
    def __init__(self, sma_fast_hours, sma_slow_hours):
        super().__init__()
        self._sma_fast_hours = sma_fast_hours
        self._sma_slow_hours = sma_slow_hours
        self._data_client = data_provider.get_rest_client()

    @staticmethod
    def _get_sma(series, periods):
        return series.rolling(periods).mean()

    @staticmethod
    def _get_signal(fast, slow):
        if len(fast) == 0 or len(slow) == 0:
            return False
        print(f"Fast {fast.iloc[-1]} / Slow: {slow.iloc[-1]}")
        return fast.iloc[-1] > slow.iloc[-1]

    def _get_bars(self, symbol):
        print(f"Bar Received: {symbol}")

        now = datetime.now()
        sma_slow_days = math.ceil(self._sma_slow_hours / 24)
        delta = timedelta(days=sma_slow_days + 1)
        start = now - delta

        try:
            if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
                # Polygon implementation
                from polygon.rest.models import Timespan
                
                # Convert symbol to Polygon format if needed
                polygon_symbol = f"X:{symbol}USD" if not symbol.startswith("X:") else symbol
                
                bars_data = self._data_client.get_aggs(
                    ticker=polygon_symbol,
                    multiplier=1,
                    timespan=Timespan.HOUR,
                    from_=start,
                    to=now
                )
                
                # Convert to DataFrame
                bars_list = []
                for bar in bars_data:
                    bars_list.append({
                        'timestamp': bar.timestamp,
                        'open': bar.open,
                        'high': bar.high,
                        'low': bar.low,
                        'close': bar.close,
                        'volume': bar.volume
                    })
                
                bars = pd.DataFrame(bars_list)
                if not bars.empty:
                    bars.set_index('timestamp', inplace=True)
                
            else:
                # Alpaca implementation
                from alpaca.data.requests import CryptoBarsRequest
                from alpaca.data.timeframe import TimeFrame
                from alpaca.data import CryptoHistoricalDataClient
                
                # Initialize Alpaca data client
                crypto_client = CryptoHistoricalDataClient(
                    config["ALPACA"]["PAPER"]["API_KEY"], 
                    config["ALPACA"]["PAPER"]["SECRET_KEY"]
                )
                
                # Convert symbol to Alpaca format
                alpaca_symbol = f"{symbol}/USD" if "/" not in symbol else symbol
                
                request_params = CryptoBarsRequest(
                    symbol_or_symbols=alpaca_symbol,
                    timeframe=TimeFrame.Hour,
                    start=start
                )
                
                bars_data = crypto_client.get_crypto_bars(request_params)
                
                # Convert to DataFrame
                if alpaca_symbol in bars_data:
                    bars_list = []
                    for bar in bars_data[alpaca_symbol]:
                        bars_list.append({
                            'timestamp': bar.timestamp,
                            'open': bar.open,
                            'high': bar.high,
                            'low': bar.low,
                            'close': bar.close,
                            'volume': bar.volume
                        })
                    
                    bars = pd.DataFrame(bars_list)
                    if not bars.empty:
                        bars.set_index('timestamp', inplace=True)
                else:
                    bars = pd.DataFrame()

            if bars.empty:
                print(f"No bars found for {symbol}")
                return pd.DataFrame()

            # Calculate SMAs
            bars['sma_fast'] = self._get_sma(bars['close'], self._sma_fast_hours)
            bars['sma_slow'] = self._get_sma(bars['close'], self._sma_slow_hours)
            
            return bars

        except Exception as e:
            print(f"Error getting bars for {symbol}: {e}")
            return pd.DataFrame()

    async def process_bar(self, bar):
        # Handle different data formats (dict vs object)
        if isinstance(bar, dict):
            bar_symbol = bar.get('symbol', '')
        else:
            bar_symbol = getattr(bar, 'symbol', '')
        
        # Handle different symbol formats
        if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
            symbol = bar_symbol.replace("X:", "").replace("USD", "")  # X:BTCUSD -> BTC
        else:
            symbol = bar_symbol.replace("/", "").replace("USD", "")  # BTC/USD -> BTC

        bars = self._get_bars(symbol=symbol)
        
        if bars.empty:
            return False
            
        signal = self._get_signal(bars['sma_fast'], bars['sma_slow'])
        return signal

