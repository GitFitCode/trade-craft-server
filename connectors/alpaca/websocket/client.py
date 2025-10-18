from threading import Thread
from alpaca.data.live import CryptoDataStream, StockDataStream
from alpaca.data.enums import DataFeed
from config import config

trading_mode = "PAPER"
if config["ALPACA"]["ENABLE_LIVE_TRADING"]:
    trading_mode = "LIVE"

api_key = config["ALPACA"][trading_mode]["API_KEY"]
secret_key = config["ALPACA"][trading_mode]["SECRET_KEY"]


class AlpacaWebSocketClient:
    def __init__(self):
        super().__init__()
        self._handle_trade = None
        self._crypto_stream = CryptoDataStream(api_key=api_key, secret_key=secret_key)
        self._stock_stream = StockDataStream(api_key=api_key, secret_key=secret_key, feed=DataFeed.SIP)

    def _run_crypto_websocket(self):
        print("Connecting to Alpaca crypto websocket...")
        self._crypto_stream.run()

    def _run_stock_websocket(self):
        print("Connecting to Alpaca stock websocket...")
        self._stock_stream.run()

    def subscribe_trades(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_stream.subscribe_trades(handler, *tickers)
        elif asset_type == "stock":
            self._stock_stream.subscribe_trades(handler, *tickers)

    def subscribe_quotes(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_stream.subscribe_quotes(handler, *tickers)
        elif asset_type == "stock":
            self._stock_stream.subscribe_quotes(handler, *tickers)

    def subscribe_bars(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_stream.subscribe_bars(handler, *tickers)
        elif asset_type == "stock":
            self._stock_stream.subscribe_bars(handler, *tickers)

    def connect(self):
        crypto_websocket_thread = Thread(target=self._run_crypto_websocket)
        crypto_websocket_thread.daemon = True

        stock_websocket_thread = Thread(target=self._run_stock_websocket)
        stock_websocket_thread.daemon = True

        crypto_websocket_thread.start()
        stock_websocket_thread.start()
