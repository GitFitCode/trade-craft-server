from providers import trading_provider
from config import config, get_trading_provider_status


class Account:
    @staticmethod
    async def get_summary():
        # Check if trading provider credentials are configured
        is_configured, status_message = get_trading_provider_status()
        if not is_configured:
            return {
                "error": "Trading provider not configured",
                "message": status_message,
                "cash": 0,
                "long_market_value": 0,
                "short_market_value": 0,
                "market_value": 0,
                "equity": 0,
                "stock_buying_power": 0,
                "option_buying_power": 0,
            }
        
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                account_info = trading_provider.get_account_info()
                summary = {
                    "cash": account_info.get("CashBalance", 0),
                    "long_market_value": account_info.get("LongStockValue", 0),
                    "short_market_value": account_info.get("ShortStockValue", 0),
                    "market_value": account_info.get("MarketValue", 0),
                    "equity": account_info.get("Equity", 0),
                    "stock_buying_power": account_info.get("BuyingPower", 0),
                    "option_buying_power": account_info.get("OptionBuyingPower", 0),
                }
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                balances = trading_provider.get_account_info()
                summary = {
                    "cash": balances.total_cash,
                    "long_market_value": balances.long_market_value,
                    "short_market_value": balances.short_market_value,
                    "market_value": balances.market_value,
                    "equity": balances.total_equity,
                    "stock_buying_power": balances.margin.stock_buying_power,
                    "option_buying_power": balances.margin.option_buying_power,
                }
            else:  # Alpaca fallback
                account = trading_provider.get_account_info()
                summary = {
                    "cash": float(account.cash),
                    "long_market_value": float(account.long_market_value),
                    "short_market_value": float(account.short_market_value),
                    "market_value": float(account.portfolio_value),
                    "equity": float(account.equity),
                    "stock_buying_power": float(account.buying_power),
                    "option_buying_power": float(account.buying_power),
                }

            return summary
        except Exception as e:
            print(f"Error getting account summary: {e}")
            return {
                "error": "API Error",
                "message": str(e),
                "cash": 0,
                "long_market_value": 0,
                "short_market_value": 0,
                "market_value": 0,
                "equity": 0,
                "stock_buying_power": 0,
                "option_buying_power": 0,
            }

    @staticmethod
    async def get_positions():
        try:
            positions = trading_provider.get_positions()
            return positions
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []

    @staticmethod
    async def get_history():
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                # TraderStation doesn't have a direct history endpoint like Tradier
                return []
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                client = trading_provider.get_client()
                return client.get_history()
            else:  # Alpaca fallback
                client = trading_provider.get_client()
                activities = client.get_activities()
                return list(activities)
        except Exception as e:
            print(f"Error getting history: {e}")
            return []

    @staticmethod
    async def get_gain_loss():
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                # TraderStation doesn't have a direct gain/loss endpoint like Tradier
                return {}
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                client = trading_provider.get_client()
                return client.get_gain_loss()
            else:  # Alpaca fallback
                # Alpaca doesn't have a direct gain/loss endpoint
                return {}
        except Exception as e:
            print(f"Error getting gain/loss: {e}")
            return {}

    @staticmethod
    async def get_orders():
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                client = trading_provider.get_client()
                return client.get_orders()
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                client = trading_provider.get_client()
                return client.get_orders()
            else:  # Alpaca fallback
                client = trading_provider.get_client()
                orders = client.get_orders()
                return list(orders)
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    @staticmethod
    async def get_order(order_id: str):
        try:
            if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
                orders = await Account.get_orders()
                for order in orders:
                    if order.get("OrderID") == order_id:
                        return order
                return None
            elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
                client = trading_provider.get_client()
                return client.get_order(order_id)
            else:  # Alpaca fallback
                client = trading_provider.get_client()
                return client.get_order_by_id(order_id)
        except Exception as e:
            print(f"Error getting order {order_id}: {e}")
            return None
