from config import config
from alpaca.trading.client import TradingClient

trading_mode = "PAPER"
if config["ALPACA"]["ENABLE_LIVE_TRADING"]:
    trading_mode = "LIVE"

api_key = config["ALPACA"][trading_mode]["API_KEY"]
secret_key = config["ALPACA"][trading_mode]["SECRET_KEY"]
paper = trading_mode == "PAPER"

alpaca_rest_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
