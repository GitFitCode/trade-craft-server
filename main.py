from providers import data_provider
from config import config
from bot import Bot
from fastapi import FastAPI
from fastapi_socketio import SocketManager
from routes import account, market, portfolio, trades, setup
from fastapi.middleware.cors import CORSMiddleware
import sentry_sdk

sentry_dsn = config["SENTRY_DSN"]
if sentry_dsn and sentry_dsn.strip() and not sentry_dsn.startswith("your_"):
    sentry_sdk.init(dsn=sentry_dsn, traces_sample_rate=1.0)

app = FastAPI()
app.include_router(account.router)
app.include_router(market.router)
app.include_router(portfolio.router)
app.include_router(trades.router)
app.include_router(setup.router)

origins = [config["CLIENT_URL"]]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

socket_manager = SocketManager(app=app, mount_location="/")
bot = Bot(max_allocation=10000)

# Only start WebSocket clients if not in options-only mode
if not config["FEATURES"]["OPTIONS_ONLY_MODE"]:
    print("Starting real-time data feeds...")
    # Use the appropriate WebSocket client based on feature flags
    websocket_client = data_provider.get_websocket_client()

    if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
        # Polygon crypto format
        websocket_client.subscribe_bars("crypto", ["X:BTCUSD"], bot.process_bar)
    else:
        # Alpaca crypto format (default)
        websocket_client.subscribe_bars("crypto", ["BTC/USD"], bot.process_bar)

    websocket_client.connect()
else:
    print("Running in OPTIONS ONLY mode - WebSocket feeds disabled")
