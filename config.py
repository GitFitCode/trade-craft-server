import os
from dotenv import load_dotenv
from distutils.util import strtobool

load_dotenv()

def is_valid_credential(value):
    """Check if a credential value is properly configured (not placeholder)"""
    if not value:
        return False
    if value.startswith("your_"):
        return False
    if value in ["test_token", "test_account", "123456789"]:
        return False
    return True

config = {
    # Feature flags to choose providers
    "FEATURES": {
        "USE_POLYGON_FOR_DATA": strtobool(os.environ.get("USE_POLYGON_FOR_DATA", "false")),
        "USE_TRADERSTATION_FOR_TRADING": strtobool(os.environ.get("USE_TRADERSTATION_FOR_TRADING", "false")),
        "USE_ALPACA_FOR_DATA": strtobool(os.environ.get("USE_ALPACA_FOR_DATA", "true")),
        "USE_TRADIER_FOR_TRADING": strtobool(os.environ.get("USE_TRADIER_FOR_TRADING", "true")),
        "ENABLE_OPTIONS_TRADING": strtobool(os.environ.get("ENABLE_OPTIONS_TRADING", "false")),
        "OPTIONS_ONLY_MODE": strtobool(os.environ.get("OPTIONS_ONLY_MODE", "false")),
    },
    
    # Polygon.io Configuration (Market Data)
    "POLYGON": {
        "API_KEY": os.environ.get("POLYGON_API_KEY"),
        "ACCESS_KEY_ID": os.environ.get("POLYGON_ACCESS_KEY_ID"),
        "SECRET_ACCESS_KEY": os.environ.get("POLYGON_SECRET_ACCESS_KEY"),
        "S3_ENDPOINT": os.environ.get("POLYGON_S3_ENDPOINT", "https://files.polygon.io"),
        "S3_BUCKET": os.environ.get("POLYGON_S3_BUCKET", "flatfiles"),
    },
    
    # TraderStation Configuration (Trading)
    "TRADERSTATION": {
        "API_KEY": os.environ.get("TRADERSTATION_API_KEY"),
        "API_SECRET": os.environ.get("TRADERSTATION_API_SECRET"),
        "ACCOUNT_ID": os.environ.get("TRADERSTATION_ACCOUNT_ID"),
        "BASE_URL": os.environ.get("TRADERSTATION_BASE_URL", "https://api.tradestation.com"),
    },
    
    # Alpaca Configuration (Original)
    "ALPACA": {
        "ENABLE_LIVE_TRADING": strtobool(os.environ.get("ALPACA_ENABLE_LIVE_TRADING", "false")),
        "LIVE": {
            "API_KEY": os.environ.get("ALPACA_LIVE_API_KEY"),
            "SECRET_KEY": os.environ.get("ALPACA_LIVE_API_SECRET"),
            "ENDPOINT": "https://api.alpaca.markets"
        },
        "PAPER": {
            "API_KEY": os.environ.get("ALPACA_PAPER_API_KEY"),
            "SECRET_KEY": os.environ.get("ALPACA_PAPER_API_SECRET"),
            "ENDPOINT": "https://paper-api.alpaca.markets"
        },
    },
    
    # Tradier Configuration (Original)
    "TRADIER": {
        "ENABLE_LIVE_TRADING": strtobool(os.environ.get("TRADIER_ENABLE_LIVE_TRADING", "false")),
        "LIVE": {
            "ACCOUNT_NUMBER": os.environ.get("TRADIER_LIVE_ACCOUNT_NUMBER"),
            "ACCESS_TOKEN": os.environ.get("TRADIER_LIVE_ACCESS_TOKEN"),
        },
        "PAPER": {
            "ACCOUNT_NUMBER": os.environ.get("TRADIER_PAPER_ACCOUNT_NUMBER"),
            "ACCESS_TOKEN": os.environ.get("TRADIER_PAPER_ACCESS_TOKEN"),
        },
    },
    
    # Other Configuration
    "CLIENT_URL": os.environ.get("CLIENT_URL", "http://localhost:3000"),
    "SENTRY_DSN": os.environ.get("SENTRY_DSN"),
    "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
    "OPENAI_MODEL": os.environ.get("OPENAI_MODEL", "gpt-4o"),
    "FED_API_KEY": os.environ.get("FED_API_KEY"),
    "MONGODB_URL": os.environ.get("MONGODB_URL"),
    "PORT": int(os.environ.get("PORT", 4000)),
    "HOST": os.environ.get("HOST", "127.0.0.1"),
}

def get_trading_provider_status():
    """Check if the current trading provider has valid credentials"""
    if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
        api_key = config["TRADERSTATION"]["API_KEY"]
        api_secret = config["TRADERSTATION"]["API_SECRET"]
        account_id = config["TRADERSTATION"]["ACCOUNT_ID"]
        if not all([is_valid_credential(api_key), is_valid_credential(api_secret), is_valid_credential(account_id)]):
            return False, "TraderStation credentials not configured"
        return True, "TraderStation configured"
    
    elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
        mode = "PAPER" if not config["TRADIER"]["ENABLE_LIVE_TRADING"] else "LIVE"
        account_number = config["TRADIER"][mode]["ACCOUNT_NUMBER"]
        access_token = config["TRADIER"][mode]["ACCESS_TOKEN"]
        if not all([is_valid_credential(account_number), is_valid_credential(access_token)]):
            return False, f"Tradier {mode} credentials not configured"
        return True, f"Tradier {mode} configured"
    
    else:  # Alpaca
        mode = "PAPER" if not config["ALPACA"]["ENABLE_LIVE_TRADING"] else "LIVE"
        api_key = config["ALPACA"][mode]["API_KEY"]
        secret_key = config["ALPACA"][mode]["SECRET_KEY"]
        if not all([is_valid_credential(api_key), is_valid_credential(secret_key)]):
            return False, f"Alpaca {mode} credentials not configured"
        return True, f"Alpaca {mode} configured"
