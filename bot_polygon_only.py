import math
from connectors.polygon.rest.client import polygon_rest_client
from connectors.traderstation.rest.client import traderstation_client
from strategies.moving_average_crossover import MovingAverageCrossoverStrategy
from datetime import datetime, timedelta
from polygon.rest.models import Timespan

moving_average_crossover = MovingAverageCrossoverStrategy(
    sma_fast_hours=79, sma_slow_hours=143
)


class Bot:
    def __init__(self, max_allocation):
        super().__init__()
        self._max_allocation = max_allocation

    @staticmethod
    def _get_position(symbol):
        """Get current position for a symbol from TraderStation"""
        try:
            positions = traderstation_client.get_positions()
            for position in positions:
                if position.get("Symbol") == symbol:
                    return float(position.get("Quantity", 0))
            return 0
        except Exception as e:
            print(f"Error getting position for {symbol}: {e}")
            return 0

    @staticmethod
    def _get_buying_power():
        """Get available buying power from TraderStation"""
        try:
            balances = traderstation_client.get_account_balances()
            return float(balances.get("BuyingPower", 0))
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

        signal = await moving_average_crossover.process_bar(bar)
        symbol = bar.symbol.replace("/", "")

        position = self._get_position(symbol=symbol)
        max_position = self._get_max_position()

        print(f"Current position: {position}")
        print(f"Max position: {max_position}")
        print(f"Signal: {signal}")

        try:
            if position == 0 and signal:
                print(f"Symbol: {symbol} / Side: BUY / Notional Amount: {max_position}")
                order_data = {
                    "symbol": symbol,
                    "qty": max_position,
                    "side": "BUY",
                    "order_type": "Market",
                    "time_in_force": "GTC"
                }
                traderstation_client.submit_order(order_data)
            elif position > 0 and not signal:
                print(f"Symbol: {symbol} / Side: SELL / Quantity: {position}")
                order_data = {
                    "symbol": symbol,
                    "qty": position,
                    "side": "SELL",
                    "order_type": "Market",
                    "time_in_force": "GTC"
                }
                traderstation_client.submit_order(order_data)
        except Exception as e:
            print(f"Error submitting order for {symbol}: {e}")

    async def process_stock_bar(self, bar):
        print("Processing stock bar...")

        try:
            # Check if market is open
            market_hours = traderstation_client.get_market_hours()
            if not market_hours.get("IsMarketOpen", False):
                print("Market is closed. Skipping...")
                return

            positions = traderstation_client.get_positions()
            
            # Get historical data for ETFs using Polygon
            trading_start = datetime.now() - timedelta(days=90)
            
            etf_historical_prices = {}
            etf_tickers = ['SPY', 'QQQ']
            for etf_ticker in etf_tickers:
                try:
                    bars = polygon_rest_client.get_aggs(
                        ticker=etf_ticker,
                        multiplier=1,
                        timespan=Timespan.MINUTE,
                        from_=trading_start,
                        to=datetime.now()
                    )
                    etf_historical_prices[etf_ticker] = bars
                except Exception as e:
                    print(f"Error fetching historical data for {etf_ticker}: {e}")
                    continue

            etf_latest_price = {}
            for etf_ticker in etf_tickers:
                try:
                    # Get latest price from Polygon
                    quote = polygon_rest_client.get_last_quote(etf_ticker)
                    etf_latest_price[etf_ticker] = quote.bid_price if quote else 0
                except Exception as e:
                    print(f"Error fetching latest price for {etf_ticker}: {e}")
                    continue

            for position in positions:
                if position.get("LongShort") == "Short":
                    self._process_short_position(position, etf_historical_prices, etf_latest_price)

        except Exception as e:
            print(f"Error in process_stock_bar: {e}")

    def _process_short_position(self, position, etf_historical_prices, etf_latest_price):
        """Process short position for stop loss and take profit"""
        try:
            stop_percent = 7
            symbol = position.get("Symbol")
            
            position_current_price = float(position.get("CurrentPrice", 0))
            position_average_entry_price = float(position.get("AveragePrice", 0))

            # Determine appropriate ETF based on exchange
            # Note: TraderStation might use different exchange naming
            exchange = position.get("Exchange", "")
            if "NASDAQ" in exchange.upper():
                etf = 'QQQ'
            else:
                etf = 'SPY'

            if etf not in etf_latest_price or etf not in etf_historical_prices:
                print(f"Missing ETF data for {etf}")
                return

            # Calculate relative performance
            # This is a simplified version - you may need to adjust based on actual data structure
            etf_current_price = etf_latest_price[etf]
            # You would need to find the ETF price at the time of entry
            # This is simplified for demonstration
            etf_entry_price = etf_current_price * 0.95  # Placeholder

            ratio_average_entry = (position_average_entry_price / etf_entry_price) * 100
            ratio_today = (position_current_price / etf_current_price) * 100
            ratio_percent_change = (ratio_today / ratio_average_entry - 1) * 100

            print(f'Ratio change for {symbol}: {ratio_percent_change}%')

            # Submit stop loss orders
            should_place_stop_loss_order = ratio_percent_change >= stop_percent

            if should_place_stop_loss_order:
                print(f"Submitting stop loss order for {symbol}")
                qty = abs(float(position.get("Quantity", 0)))
                
                # Cover short position
                order_data = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": "BUY",
                    "order_type": "Market",
                    "time_in_force": "DAY"
                }
                traderstation_client.submit_order(order_data)

                # Sell corresponding ETF
                etf_order_data = {
                    "symbol": etf,
                    "qty": qty,  # Simplified - you might want to calculate based on dollar value
                    "side": "SELL",
                    "order_type": "Market",
                    "time_in_force": "DAY"
                }
                traderstation_client.submit_order(etf_order_data)

            # Take profit logic
            take_profit_threshold = -stop_percent * 1.1
            if ratio_percent_change <= take_profit_threshold:
                print(f"Submitting take profit order for {symbol}")
                qty = abs(float(position.get("Quantity", 0))) * 0.5  # Take 50% profit
                
                order_data = {
                    "symbol": symbol,
                    "qty": qty,
                    "side": "BUY",
                    "order_type": "Market",
                    "time_in_force": "DAY"
                }
                traderstation_client.submit_order(order_data)

        except Exception as e:
            print(f"Error processing short position for {position.get('Symbol', 'unknown')}: {e}")