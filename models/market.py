from providers import data_provider
from config import config
from datetime import datetime, timedelta


class Market:
    @staticmethod
    def get_quotes(symbols: str):
        """Get real-time quotes for symbols - use Tradier for options quotes when enabled"""
        try:
            symbol_list = symbols.split(',') if ',' in symbols else [symbols]
            quotes = []
            
            # Check if any symbols are options (contain typical option naming patterns)
            has_options = any('C' in sym or 'P' in sym for sym in symbol_list if len(sym) > 6)
            
            if config["FEATURES"]["ENABLE_OPTIONS_TRADING"] and has_options:
                # Use Tradier for options quotes (real-time data)
                from connectors.tradier.rest.client import tradier_rest_client
                for symbol in symbol_list:
                    quote = tradier_rest_client.get_quotes(symbols=symbol.strip())
                    if quote and 'quotes' in quote and 'quote' in quote['quotes']:
                        quote_data = quote['quotes']['quote']
                        if isinstance(quote_data, list):
                            quote_data = quote_data[0]
                        quotes.append({
                            "symbol": symbol.strip(),
                            "bid": quote_data.get('bid', 0),
                            "ask": quote_data.get('ask', 0),
                            "last": quote_data.get('last', 0),
                            "timestamp": datetime.now()
                        })
            elif config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
                # Polygon implementation for stocks
                client = data_provider.get_rest_client()
                for symbol in symbol_list:
                    quote = client.get_last_quote(symbol.strip())
                    if quote:
                        quotes.append({
                            "symbol": symbol.strip(),
                            "bid": quote.bid_price,
                            "ask": quote.ask_price,
                            "last": quote.bid_price,  # Simplified
                            "timestamp": quote.timestamp
                        })
            else:
                # Alpaca implementation (fallback or when USE_ALPACA_FOR_DATA is true)
                client = data_provider.get_rest_client()
                # Note: Alpaca doesn't have a direct quote API in the same format
                # This would need to be implemented based on Alpaca's actual quote structure
                for symbol in symbol_list:
                    # Placeholder - implement based on Alpaca's quote API
                    quotes.append({
                        "symbol": symbol.strip(),
                        "bid": 0,
                        "ask": 0,
                        "last": 0,
                        "timestamp": datetime.now()
                    })
            
            return quotes
        except Exception as e:
            print(f"Error getting quotes: {e}")
            return []

    @staticmethod
    def get_option_chains(symbol: str, expiration: str, greeks: bool = False):
        """Get option chains using Tradier for advanced options data"""
        try:
            if config["FEATURES"]["ENABLE_OPTIONS_TRADING"]:
                # Use Tradier for options data when options trading is enabled
                from connectors.tradier.rest.client import tradier_rest_client
                
                option_chains = tradier_rest_client.get_option_chains(
                    symbol=symbol,
                    expiration=expiration,
                    greeks=greeks
                )
                return option_chains
            else:
                # Fallback to regular data provider
                if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
                    # Polygon options API - different structure from Tradier
                    return {"message": "Options trading not enabled"}
                else:
                    # Alpaca doesn't have options
                    return {"message": "Options not supported with current data provider"}
                    
        except Exception as e:
            print(f"Error getting option chains: {e}")
            return {}

    @staticmethod
    def get_option_strikes(symbol: str, expiration: str):
        """Get option strikes using Tradier"""
        try:
            if config["FEATURES"]["ENABLE_OPTIONS_TRADING"]:
                from connectors.tradier.rest.client import tradier_rest_client
                option_strikes = tradier_rest_client.get_option_strikes(
                    symbol=symbol,
                    expiration=expiration
                )
                return option_strikes
            else:
                return {"message": "Options trading not enabled"}
        except Exception as e:
            print(f"Error getting option strikes: {e}")
            return []

    @staticmethod
    def get_option_expirations(symbol: str):
        """Get option expirations using Tradier"""
        try:
            if config["FEATURES"]["ENABLE_OPTIONS_TRADING"]:
                from connectors.tradier.rest.client import tradier_rest_client
                option_expirations = tradier_rest_client.get_option_expirations(symbol=symbol)
                return option_expirations
            else:
                return {"message": "Options trading not enabled"}
        except Exception as e:
            print(f"Error getting option expirations: {e}")
            return []

    @staticmethod
    def lookup_option_symbols(underlying: str):
        """Lookup option symbols using Tradier"""
        try:
            if config["FEATURES"]["ENABLE_OPTIONS_TRADING"]:
                from connectors.tradier.rest.client import tradier_rest_client
                option_symbols = tradier_rest_client.lookup_option_symbols(underlying=underlying)
                return option_symbols
            else:
                return {"message": "Options trading not enabled"}
        except Exception as e:
            print(f"Error looking up option symbols: {e}")
            return []

    @staticmethod
    def get_historical_quotes(symbol: str, start: str, end: str, interval: str = "daily"):
        """Get historical quotes/bars"""
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            historical_data = []
            
            if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
                # Polygon implementation
                from polygon.rest.models import Timespan
                client = data_provider.get_rest_client()
                
                timespan = Timespan.DAY if interval == "daily" else Timespan.MINUTE
                
                bars = client.get_aggs(
                    ticker=symbol,
                    multiplier=1,
                    timespan=timespan,
                    from_=start_date,
                    to=end_date
                )
                
                for bar in bars:
                    historical_data.append({
                        "date": bar.timestamp.strftime("%Y-%m-%d"),
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume
                    })
            else:
                # Alpaca implementation (fallback or when USE_ALPACA_FOR_DATA is true)
                from alpaca.data.requests import StockBarsRequest
                from alpaca.data.timeframe import TimeFrame
                from alpaca.data import StockHistoricalDataClient
                
                data_client = StockHistoricalDataClient(
                    config["ALPACA"]["PAPER"]["API_KEY"], 
                    config["ALPACA"]["PAPER"]["SECRET_KEY"]
                )
                
                timeframe = TimeFrame.Day if interval == "daily" else TimeFrame.Minute
                
                request_params = StockBarsRequest(
                    symbol_or_symbols=symbol,
                    start=start_date,
                    end=end_date,
                    timeframe=timeframe
                )
                bars = data_client.get_stock_bars(request_params)
                
                for bar in bars[symbol]:
                    historical_data.append({
                        "date": bar.timestamp.strftime("%Y-%m-%d"),
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume
                    })
            
            return historical_data
        except Exception as e:
            print(f"Error getting historical quotes: {e}")
            return []

    @staticmethod
    def get_time_and_sales(symbol: str, interval: str, start: str, end: str):
        """Get time and sales data"""
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            
            # Use trades endpoint for time and sales
            trades = polygon_rest_client.list_trades(
                ticker=symbol,
                timestamp_gte=start_date,
                timestamp_lte=end_date
            )
            
            time_sales = []
            for trade in trades:
                time_sales.append({
                    "time": trade.timestamp,
                    "price": trade.price,
                    "size": trade.size,
                    "exchange": trade.exchange
                })
            
            return time_sales
        except Exception as e:
            print(f"Error getting time and sales: {e}")
            return []

    @staticmethod
    def get_etb_securities():
        """Get easy-to-borrow securities - not available in Polygon"""
        # This is specific to brokers and not available in market data APIs
        return []

    @staticmethod
    def get_clock():
        """Get market status"""
        try:
            # Polygon doesn't have a direct market clock endpoint
            # Use market holidays and current time to determine status
            # This is a simplified implementation
            now = datetime.now()
            market_hours = {
                "is_open": 9 <= now.hour < 16 and now.weekday() < 5,  # Simplified
                "next_open": "2024-01-01T09:30:00.000Z",  # Placeholder
                "next_close": "2024-01-01T16:00:00.000Z"  # Placeholder
            }
            return market_hours
        except Exception as e:
            print(f"Error getting market clock: {e}")
            return {}

    @staticmethod
    def get_calendar(month: str, year: str):
        """Get market calendar"""
        try:
            # Polygon doesn't have a calendar endpoint like Tradier
            # You would need to implement this using market holidays data
            return []
        except Exception as e:
            print(f"Error getting calendar: {e}")
            return []

    @staticmethod
    def search_companies(query: str):
        """Search companies by name"""
        try:
            # Use Polygon's ticker search
            results = polygon_rest_client.get_ticker_details(query)
            if results:
                return [{
                    "symbol": results.ticker,
                    "name": results.name,
                    "exchange": results.primary_exchange
                }]
            return []
        except Exception as e:
            print(f"Error searching companies: {e}")
            return []

    @staticmethod
    def lookup_symbol(query: str):
        """Lookup symbol"""
        try:
            # Use search_companies for symbol lookup
            results = Market.search_companies(query)
            return results[0] if results else None
        except Exception as e:
            print(f"Error looking up symbol: {e}")
            return None
