from fastapi import APIRouter
from config import get_trading_provider_status, config

router = APIRouter(prefix="/api/setup")


@router.get("/status")
async def get_setup_status():
    """Get current configuration status and setup instructions"""
    is_configured, status_message = get_trading_provider_status()
    
    response = {
        "is_configured": is_configured,
        "status_message": status_message,
        "current_provider": "Unknown",
        "setup_instructions": {},
        "features": {
            "options_trading_enabled": config["FEATURES"]["ENABLE_OPTIONS_TRADING"],
            "options_only_mode": config["FEATURES"]["OPTIONS_ONLY_MODE"],
        }
    }
    
    # Determine current provider
    if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
        response["current_provider"] = "TraderStation"
        response["setup_instructions"] = {
            "provider": "TraderStation",
            "required_env_vars": [
                "TRADERSTATION_API_KEY",
                "TRADERSTATION_API_SECRET", 
                "TRADERSTATION_ACCOUNT_ID"
            ],
            "instructions": [
                "1. Sign up for TraderStation API access",
                "2. Get your API credentials from TraderStation developer portal",
                "3. Add the credentials to your .env file",
                "4. Restart the server"
            ]
        }
    elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
        mode = "PAPER" if not config["TRADIER"]["ENABLE_LIVE_TRADING"] else "LIVE"
        response["current_provider"] = f"Tradier ({mode})"
        response["setup_instructions"] = {
            "provider": f"Tradier {mode}",
            "required_env_vars": [
                f"TRADIER_{mode}_ACCOUNT_NUMBER",
                f"TRADIER_{mode}_ACCESS_TOKEN"
            ],
            "instructions": [
                "1. Sign up for Tradier brokerage account",
                "2. Enable API access in Tradier dashboard", 
                "3. Get your account number and access token",
                "4. Add the credentials to your .env file:",
                f"   TRADIER_{mode}_ACCOUNT_NUMBER=your_account_number",
                f"   TRADIER_{mode}_ACCESS_TOKEN=your_access_token",
                "5. Restart the server"
            ]
        }
    else:  # Alpaca
        mode = "PAPER" if not config["ALPACA"]["ENABLE_LIVE_TRADING"] else "LIVE"
        response["current_provider"] = f"Alpaca ({mode})"
        response["setup_instructions"] = {
            "provider": f"Alpaca {mode}",
            "required_env_vars": [
                f"ALPACA_{mode}_API_KEY",
                f"ALPACA_{mode}_API_SECRET"
            ],
            "instructions": [
                "1. Sign up for Alpaca account",
                "2. Generate API keys in Alpaca dashboard",
                "3. Add the credentials to your .env file:",
                f"   ALPACA_{mode}_API_KEY=your_api_key",
                f"   ALPACA_{mode}_API_SECRET=your_api_secret", 
                "4. Restart the server"
            ]
        }
    
    return response


@router.get("/mongodb-status")
async def get_mongodb_status():
    """Check MongoDB connection status"""
    try:
        from models.trade import db
        if db is not None:
            # Test connection
            await db.command("ping")
            return {
                "status": "connected",
                "message": "MongoDB is connected and ready"
            }
        else:
            return {
                "status": "not_configured", 
                "message": "MongoDB URL not configured",
                "instructions": [
                    "1. Install MongoDB: brew install mongodb-community",
                    "2. Start MongoDB: brew services start mongodb-community",
                    "3. Add to .env: MONGODB_URL=mongodb://localhost:27017/trading",
                    "4. Restart the server"
                ]
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"MongoDB connection error: {str(e)}",
            "instructions": [
                "1. Check if MongoDB is running: brew services start mongodb-community",
                "2. Verify connection string in .env file",
                "3. Check MongoDB logs for errors"
            ]
        }