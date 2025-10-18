from threading import Thread
from polygon import WebSocketClient
from polygon.websocket.models import Market
from config import config


class PolygonWebSocketClient:
    def __init__(self):
        super().__init__()
        self._api_key = config["POLYGON"]["API_KEY"]
        self._crypto_client = WebSocketClient(
            api_key=self._api_key,
            market=Market.Crypto
        )
        self._stocks_client = WebSocketClient(
            api_key=self._api_key,
            market=Market.Stocks
        )
        self._crypto_handler = None
        self._stocks_handler = None

    def _raw_data_handler(self, raw_message):
        """Handle raw WebSocket messages"""
        # Route messages to the appropriate handler
        try:
            import json
            if isinstance(raw_message, bytes):
                message = json.loads(raw_message.decode('utf-8'))
            elif isinstance(raw_message, str):
                message = json.loads(raw_message)
            else:
                message = raw_message
            
            # Check message type and route to appropriate handler
            if isinstance(message, list):
                for msg in message:
                    self._process_message(msg)
            else:
                self._process_message(message)
        except Exception as e:
            print(f"Error processing Polygon message: {e}")
            print(f"Raw message: {raw_message}")

    def _process_message(self, message):
        """Process individual messages based on their type"""
        if not isinstance(message, dict):
            return
            
        msg_type = message.get('ev')  # Event type
        
        if msg_type == 'XA':  # Crypto aggregate (bar)
            if self._crypto_handler:
                # Convert Polygon format to standardized format
                bar_data = {
                    'symbol': message.get('pair', ''),
                    'timestamp': message.get('s'),  # Start timestamp
                    'open': message.get('o'),
                    'high': message.get('h'),
                    'low': message.get('l'),
                    'close': message.get('c'),
                    'volume': message.get('v'),
                    'trade_count': message.get('n'),
                    'vwap': message.get('vw')
                }
                self._crypto_handler(bar_data)
        elif msg_type == 'A':  # Stock aggregate (bar)
            if self._stocks_handler:
                # Convert Polygon format to standardized format
                bar_data = {
                    'symbol': message.get('sym', ''),
                    'timestamp': message.get('s'),  # Start timestamp
                    'open': message.get('o'),
                    'high': message.get('h'),
                    'low': message.get('l'),
                    'close': message.get('c'),
                    'volume': message.get('v'),
                    'trade_count': message.get('n'),
                    'vwap': message.get('vw')
                }
                self._stocks_handler(bar_data)
        elif msg_type == 'status':
            # Connection status message
            print(f"Polygon WebSocket status: {message.get('message', 'Unknown')}")
        else:
            # Other message types (trades, quotes, etc.)
            pass

    def _run_crypto_websocket(self):
        print("Connecting to Polygon crypto websocket...")
        try:
            self._crypto_client.run(self._raw_data_handler)
        except Exception as e:
            print(f"Error in crypto websocket: {e}")
            import traceback
            traceback.print_exc()

    def _run_stocks_websocket(self):
        print("Connecting to Polygon stocks websocket...")
        try:
            self._stocks_client.run(self._raw_data_handler)
        except Exception as e:
            print(f"Error in stocks websocket: {e}")
            import traceback
            traceback.print_exc()

    def subscribe_trades(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_handler = handler
            for ticker in tickers:
                self._crypto_client.subscribe(ticker, "XT")  # XT for crypto trades
        elif asset_type == "stock":
            self._stocks_handler = handler
            for ticker in tickers:
                self._stocks_client.subscribe(ticker, "T")  # T for stock trades

    def subscribe_quotes(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_handler = handler
            for ticker in tickers:
                self._crypto_client.subscribe(ticker, "XQ")  # XQ for crypto quotes
        elif asset_type == "stock":
            self._stocks_handler = handler
            for ticker in tickers:
                self._stocks_client.subscribe(ticker, "Q")  # Q for stock quotes

    def subscribe_bars(self, asset_type, tickers, handler):
        if asset_type == "crypto":
            self._crypto_handler = handler
            for ticker in tickers:
                # Polygon WebSocket format: "XA.{symbol}"
                subscription = f"XA.{ticker}"
                self._crypto_client.subscribe(subscription)
        elif asset_type == "stock":
            self._stocks_handler = handler
            for ticker in tickers:
                # Polygon WebSocket format: "A.{symbol}"
                subscription = f"A.{ticker}"
                self._stocks_client.subscribe(subscription)

    def connect(self):
        crypto_websocket_thread = Thread(target=self._run_crypto_websocket)
        crypto_websocket_thread.daemon = True

        stocks_websocket_thread = Thread(target=self._run_stocks_websocket)
        stocks_websocket_thread.daemon = True

        crypto_websocket_thread.start()
        stocks_websocket_thread.start()