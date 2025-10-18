import math
from providers import data_provider, trading_provider
from strategies.moving_average_crossover import MovingAverageCrossoverStrategy
from datetime import datetime, timedelta
from config import config

moving_average_crossover = MovingAverageCrossoverStrategy(
    sma_fast_hours=79, sma_slow_hours=143
)


class Bot:
    def __init__(self, max_allocation):
        super().__init__()
        self._max_allocation = max_allocation
        self._data_client = data_provider.get_rest_client()
        self._trading_client = trading_provider.get_client()

    def _get_position(self, symbol):
        """Get current position for a symbol"""
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                positions = self._trading_client.get_positions()
                for position in positions:
                    if position.get("Symbol") == symbol:
                        return float(position.get("Quantity", 0))
                return 0
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                positions = self._trading_client.get_positions()
                for position in positions:
                    if position.symbol == symbol:
                        return float(position.quantity)
                return 0
            else:  # Alpaca fallback
                positions = self._trading_client.get_all_positions()
                for position in positions:
                    if position.symbol == symbol:
                        return float(position.qty)
                return 0
        except Exception as e:
            print(f"Error getting position for {symbol}: {e}")
            return 0

    def _get_buying_power(self):
        """Get available buying power"""
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                balances = self._trading_client.get_account_balances()
                return float(balances.get("BuyingPower", 0))
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                balances = self._trading_client.get_balances()
                return float(balances.margin.stock_buying_power)
            else:  # Alpaca fallback
                account = self._trading_client.get_account()
                return float(account.non_marginable_buying_power)
        except Exception as e:
            print(f"Error getting buying power: {e}")
            return 0

    def _get_max_position(self):
        buying_power = self._get_buying_power()
        return math.floor(min(self._max_allocation, buying_power))

    async def process_bar(self, bar):
        await self.process_crypto_bar(bar)
        await self.process_stock_bar(bar)

    async def process_crypto_bar(self, bar):
        print("Processing crypto bar...")
        print(f"Received bar data: {bar}")

        signal = await moving_average_crossover.process_bar(bar)
        
        # Handle different data formats (dict vs object)
        if isinstance(bar, dict):
            bar_symbol = bar.get('symbol', '')
        else:
            bar_symbol = getattr(bar, 'symbol', '')
        
        # Handle different symbol formats
        if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
            symbol = bar_symbol.replace("X:", "").replace("USD", "/USD")  # X:BTCUSD -> BTC/USD
        else:
            symbol = bar_symbol.replace("/", "")  # BTC/USD -> BTCUSD

        position = self._get_position(symbol=symbol)
        max_position = self._get_max_position()

        print(f"Current position: {position}")
        print(f"Max position: {max_position}")
        print(f"Signal: {signal}")

        try:
            if position == 0 and signal:
                print(f"Symbol: {symbol} / Side: BUY / Notional Amount: {max_position}")
                self._submit_order(symbol, max_position, "BUY")
            elif position > 0 and not signal:
                print(f"Symbol: {symbol} / Side: SELL / Quantity: {position}")
                self._submit_order(symbol, position, "SELL")
        except Exception as e:
            print(f"Error submitting order for {symbol}: {e}")

    def _submit_order(self, symbol, quantity, side):
        """Submit order using the appropriate provider"""
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                order_data = {
                    "symbol": symbol,
                    "qty": quantity,
                    "side": side,
                    "order_type": "Market",
                    "time_in_force": "GTC"
                }
                return self._trading_client.submit_order(order_data)
            
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                # Tradier order format
                order_data = {
                    "symbol": symbol,
                    "side": side.lower(),
                    "quantity": quantity,
                    "type": "market",
                    "duration": "gtc"
                }
                return self._trading_client.submit_order(order_data)
            
            else:  # Alpaca fallback
                from alpaca.trading.requests import MarketOrderRequest
                from alpaca.trading.enums import OrderSide, TimeInForce
                
                order_data = MarketOrderRequest(
                    symbol=symbol,
                    qty=quantity,
                    side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
                    time_in_force=TimeInForce.GTC
                )
                return self._trading_client.submit_order(order_data)
                
        except Exception as e:
            print(f"Error submitting {side} order for {symbol}: {e}")
            raise

    async def process_stock_bar(self, bar):
        print("Processing stock bar...")

        try:
            # Check if market is open
            is_market_open = self._check_market_hours()
            if not is_market_open:
                print("Market is closed. Skipping...")
                return

            positions = trading_provider.get_positions()
            
            # Get historical data using the data provider
            etf_historical_prices = {}
            etf_latest_price = {}
            etf_tickers = ['SPY', 'QQQ']
            
            for etf_ticker in etf_tickers:
                try:
                    if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
                        # Polygon implementation
                        from polygon.rest.models import Timespan
                        trading_start = datetime.now() - timedelta(days=90)
                        bars = self._data_client.get_aggs(
                            ticker=etf_ticker,
                            multiplier=1,
                            timespan=Timespan.MINUTE,
                            from_=trading_start,
                            to=datetime.now()
                        )
                        etf_historical_prices[etf_ticker] = bars
                        
                        quote = self._data_client.get_last_quote(etf_ticker)
                        etf_latest_price[etf_ticker] = quote.bid_price if quote else 0
                        
                    else:  # Alpaca implementation
                        from alpaca.data.requests import StockBarsRequest, StockLatestBarRequest
                        from alpaca.data.timeframe import TimeFrame
                        from alpaca.data import StockHistoricalDataClient
                        
                        trading_start = datetime.now() - timedelta(days=90)
                        data_client = StockHistoricalDataClient(
                            config["ALPACA"]["PAPER"]["API_KEY"], 
                            config["ALPACA"]["PAPER"]["SECRET_KEY"]
                        )
                        
                        request_params = StockBarsRequest(
                            symbol_or_symbols=etf_ticker,
                            start=trading_start,
                            timeframe=TimeFrame.Minute
                        )
                        prices = data_client.get_stock_bars(request_params)
                        etf_historical_prices[etf_ticker] = prices[etf_ticker]
                        
                        request_params = StockLatestBarRequest(symbol_or_symbols=etf_ticker)
                        latest_price = data_client.get_stock_latest_bar(request_params)
                        etf_latest_price[etf_ticker] = latest_price[etf_ticker].close
                        
                except Exception as e:
                    print(f"Error fetching data for {etf_ticker}: {e}")
                    continue

            # Process positions for stop loss/take profit
            for position in positions:
                if self._is_short_position(position):
                    self._process_short_position(position, etf_historical_prices, etf_latest_price)

        except Exception as e:
            print(f"Error in process_stock_bar: {e}")

    def _check_market_hours(self):
        """Check if market is open using the appropriate provider"""
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                market_hours = self._trading_client.get_market_hours()
                return market_hours.get("IsMarketOpen", False)
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                clock = self._trading_client.get_clock()
                return clock.is_open
            else:  # Alpaca fallback
                clock = self._trading_client.get_clock()
                return clock.is_open
        except Exception as e:
            print(f"Error checking market hours: {e}")
            return False

    def _is_short_position(self, position):
        """Check if position is short based on provider"""
        if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
            return position.get("LongShort") == "Short"
        elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
            return position.side == "short"
        else:  # Alpaca
            return position.side == "short"

    def _process_short_position(self, position, etf_historical_prices, etf_latest_price):
        """Process short position for stop loss and take profit"""
        try:
            stop_percent = 7
            
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                symbol = position.get("Symbol")
                position_current_price = float(position.get("CurrentPrice", 0))
                position_average_entry_price = float(position.get("AveragePrice", 0))
                exchange = position.get("Exchange", "")
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                symbol = position.symbol
                position_current_price = float(position.current_price)
                position_average_entry_price = float(position.avg_entry_price)
                exchange = position.exchange
            else:  # Alpaca
                symbol = position.symbol
                position_current_price = float(position.current_price)
                position_average_entry_price = float(position.avg_entry_price)
                exchange = position.exchange

            # Determine appropriate ETF
            if "NASDAQ" in exchange.upper():
                etf = 'QQQ'
            else:
                etf = 'SPY'

            if etf not in etf_latest_price or etf not in etf_historical_prices:
                print(f"Missing ETF data for {etf}")
                return

            # Calculate relative performance (simplified)
            etf_current_price = etf_latest_price[etf]
            etf_entry_price = etf_current_price * 0.95  # Placeholder

            ratio_average_entry = (position_average_entry_price / etf_entry_price) * 100
            ratio_today = (position_current_price / etf_current_price) * 100
            ratio_percent_change = (ratio_today / ratio_average_entry - 1) * 100

            print(f'Ratio change for {symbol}: {ratio_percent_change}%')

            # Submit stop loss orders
            if ratio_percent_change >= stop_percent:
                print(f"Submitting stop loss order for {symbol}")
                qty = abs(float(self._get_position_quantity(position)))
                
                # Cover short position
                self._submit_order(symbol, qty, "BUY")
                
                # Sell corresponding ETF
                self._submit_order(etf, qty, "SELL")

            # Take profit logic
            take_profit_threshold = -stop_percent * 1.1
            if ratio_percent_change <= take_profit_threshold:
                print(f"Submitting take profit order for {symbol}")
                qty = abs(float(self._get_position_quantity(position))) * 0.5
                self._submit_order(symbol, qty, "BUY")

        except Exception as e:
            print(f"Error processing short position for {symbol}: {e}")

    def _get_position_quantity(self, position):
        """Get position quantity based on provider"""
        if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
            return position.get("Quantity", 0)
        elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
            return position.quantity
        else:  # Alpaca
            return position.qty