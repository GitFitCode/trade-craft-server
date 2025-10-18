# Trade Craft Server

**Advanced Multi-Provider Trading Platform with Flexible Feature Flags**

Extended by Devs @ [gitfitcode](https://www.gitfitcode.com) and huge thanks to [Robert](https://github.com/robertjosephwayne) who developed [FinanceBrain](https://www.financebrain.ai/) for the initial idea and implementation.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MongoDB (for trade history)
- Trading API credentials (see [Setup Guide](#setup-guide))

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API credentials and feature flags
# See Setup Guide below for detailed instructions
```

### Running the Server
```bash
# Run locally with uvicorn
uvicorn main:app --reload

# Run with specified host and port
uvicorn --host 0.0.0.0 --port 4000 main:app --workers 1

# Check setup status (helpful for configuration)
curl http://localhost:4000/api/setup/status
```

## 🎛️ Feature Flags & Providers

### Supported Data Providers
| Provider | Features | WebSocket | Options | Requirements |
|----------|----------|-----------|---------|--------------|
| **Polygon.io** | Comprehensive market data, real-time quotes, historical data | ✅ (Paid plans only) | ✅ | API Key |
| **Alpaca** | Stocks, crypto, real-time data | ✅ (Free) | ❌ | API Key + Secret |

### Supported Trading Providers
| Provider | Features | Paper Trading | Live Trading | Options | Requirements |
|----------|----------|---------------|--------------|---------|--------------|
| **Tradier** | Advanced options, stocks, real-time data | ✅ | ✅ | ✅ | Account Number + Access Token |
| **TraderStation** | Professional trading platform | ✅ | ✅ | ✅ | API Key + Secret + Account ID |
| **Alpaca** | Commission-free stocks and crypto | ✅ | ✅ | ❌ | API Key + Secret |

### Feature Flag Configuration
Configure your setup using environment variables in `.env`:

```bash
# === DATA PROVIDER SELECTION ===
USE_POLYGON_FOR_DATA=false          # Use Polygon.io for market data
USE_ALPACA_FOR_DATA=true            # Use Alpaca for market data (default)

# === TRADING PROVIDER SELECTION ===
USE_TRADERSTATION_FOR_TRADING=false # Use TraderStation for trading
USE_TRADIER_FOR_TRADING=true        # Use Tradier for trading (default)

# === TRADING FEATURES ===
ENABLE_OPTIONS_TRADING=true         # Enable options trading functionality
OPTIONS_ONLY_MODE=false             # Disable crypto/stock WebSockets (options focus)

# === TRADING MODES ===
TRADIER_ENABLE_LIVE_TRADING=false   # Use paper trading (recommended)
ALPACA_ENABLE_LIVE_TRADING=false    # Use paper trading (recommended)
```

### Dependencies
- **Core Framework**: FastAPI + Socket.IO for REST API and WebSocket support
- **Data Providers**: polygon-api-client, alpaca-py 
- **Trading Providers**: tradier-python, alpaca-py
- **Database**: MongoDB (motor) for trade history
- **Processing**: pandas, numpy for data analysis
- **Monitoring**: Sentry for error tracking

## 🏗️ Architecture Overview

### Core Components

1. **Provider Factory System** (`/providers/`)
   - **DataProviderFactory**: Dynamically selects between Polygon and Alpaca for market data
   - **TradingProviderFactory**: Dynamically selects between TraderStation, Tradier, and Alpaca for trading
   - Feature flags control which providers are used at runtime

2. **Trading Connectors** (`/connectors/`)
   - **Polygon**: REST and WebSocket clients for comprehensive market data
   - **TraderStation**: REST client for professional trading platform integration
   - **Alpaca**: REST and WebSocket clients for commission-free trading
   - **Tradier**: REST client for advanced options and stock trading

3. **Bot System** (`bot.py`)
   - Multi-mode trading bot with provider-agnostic architecture
   - **Options-Only Mode**: Disables WebSocket feeds for options-focused trading
   - **Crypto/Stock Mode**: Real-time processing of market data bars
   - Position management and risk controls across all providers
   - Strategy-based trading signals (MovingAverageCrossoverStrategy)

4. **API Routes** (`/routes/`)
   - **Account**: Account summary, positions, history, gain/loss, orders
   - **Market**: Market data, quotes, option chains, strikes, expirations
   - **Portfolio**: Portfolio management and performance analytics
   - **Trades**: Multi-provider trade execution
   - **Setup**: Configuration status and guidance
   - All routes prefixed with `/api/`

5. **Models** (`/models/`)
   - Provider-agnostic data models with automatic fallbacks
   - Intelligent routing based on feature flags
   - Graceful error handling for missing credentials

6. **Strategies** (`/strategies/`)
   - Modular trading strategy implementations
   - Provider-agnostic data format handling
   - Support for both real-time and historical data analysis

### Configuration System
- **Feature-Flag Driven**: Runtime provider selection without code changes
- **Multi-Mode Support**: PAPER/LIVE trading modes for all providers
- **Credential Validation**: Automatic detection of missing/invalid API credentials
- **Environment Variables**: Secure configuration via `.env` files
- **CORS Configuration**: Configurable client URL for frontend integration

### Real-time Architecture
- **Dynamic WebSocket Selection**: Provider-specific WebSocket clients based on feature flags
- **Options-Only Mode**: Disables resource-intensive WebSocket feeds for options trading
- **Multi-Asset Support**: Simultaneous crypto, stock, and options data processing
- **Format Normalization**: Unified data format across different provider APIs

## 🛠️ Setup Guide

### MongoDB Setup (Required)
```bash
# Install MongoDB
brew install mongodb-community

# Start MongoDB service
brew services start mongodb-community

# Verify connection
mongosh --eval "db.runCommand('ping')"
```

### Provider Credentials Setup

#### Tradier (Recommended for Options)
1. Sign up at [Tradier](https://brokerage.tradier.com/)
2. Enable API access in your account dashboard
3. Get your account number and access token
4. Add to `.env`:
```bash
TRADIER_PAPER_ACCOUNT_NUMBER=your_account_number
TRADIER_PAPER_ACCESS_TOKEN=your_access_token
```

#### Polygon.io (Premium Data)
1. Sign up at [Polygon.io](https://polygon.io/)
2. Get your API key from the dashboard
3. Add to `.env`:
```bash
POLYGON_API_KEY=your_api_key
```

#### Alpaca (Free Alternative)
1. Sign up at [Alpaca](https://alpaca.markets/)
2. Generate API keys in your dashboard
3. Add to `.env`:
```bash
ALPACA_PAPER_API_KEY=your_api_key
ALPACA_PAPER_API_SECRET=your_api_secret
```

### Configuration Validation
Visit `/api/setup/status` after starting the server for real-time configuration guidance and troubleshooting.

## 🔧 Advanced Features

### Trading Modes
- **Options-Only Mode**: Perfect for options trading with Tradier's advanced features
- **Multi-Asset Mode**: Real-time crypto, stocks, and options trading
- **Paper Trading**: Safe testing environment with all providers
- **Live Trading**: Production trading when ready

### Error Handling
- **Graceful API Failures**: Informative error messages instead of crashes
- **Credential Validation**: Automatic detection of configuration issues
- **MongoDB Fallbacks**: Optional database integration
- **Rate Limit Management**: Intelligent API request handling

### Deployment
- **Heroku Ready**: Configured via `Procfile` for easy deployment
- **Docker Compatible**: Containerized deployment support
- **Production Monitoring**: Sentry integration for error tracking
- **Health Checks**: Setup status endpoints for monitoring

## 📋 Common Configuration Examples

### Options Trading Focus (Recommended)
```bash
# Enable advanced options trading with Tradier
USE_POLYGON_FOR_DATA=false
USE_ALPACA_FOR_DATA=true
USE_TRADIER_FOR_TRADING=true
ENABLE_OPTIONS_TRADING=true
OPTIONS_ONLY_MODE=true

# Tradier credentials
TRADIER_PAPER_ACCOUNT_NUMBER=your_account
TRADIER_PAPER_ACCESS_TOKEN=your_token
```

### Comprehensive Trading Setup
```bash
# Use Polygon for premium data, Tradier for trading
USE_POLYGON_FOR_DATA=true
USE_ALPACA_FOR_DATA=false
USE_TRADIER_FOR_TRADING=true
ENABLE_OPTIONS_TRADING=true
OPTIONS_ONLY_MODE=false

# Provider credentials
POLYGON_API_KEY=your_polygon_key
TRADIER_PAPER_ACCOUNT_NUMBER=your_account
TRADIER_PAPER_ACCESS_TOKEN=your_token
```

### Budget-Friendly Setup
```bash
# Use free Alpaca for both data and trading
USE_POLYGON_FOR_DATA=false
USE_ALPACA_FOR_DATA=true
USE_TRADIER_FOR_TRADING=false
ENABLE_OPTIONS_TRADING=false
OPTIONS_ONLY_MODE=false

# Alpaca credentials
ALPACA_PAPER_API_KEY=your_api_key
ALPACA_PAPER_API_SECRET=your_api_secret
```

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Check MongoDB is running: `brew services start mongodb-community`
- Verify Python 3.13+ is installed: `python --version`
- Check for missing dependencies: `pip install -r requirements.txt`

**API Authentication Errors:**
- Visit `/api/setup/status` for specific guidance
- Verify credentials are not placeholder values
- Check provider documentation for correct format

**WebSocket Connection Issues:**
- Polygon WebSocket requires paid plan
- Use `OPTIONS_ONLY_MODE=true` to disable WebSocket feeds
- Check firewall settings for WebSocket connections

**Options Trading Not Working:**
- Ensure `ENABLE_OPTIONS_TRADING=true`
- Use Tradier provider: `USE_TRADIER_FOR_TRADING=true`
- Verify Tradier account has options permissions

### Support Endpoints
- **Setup Status**: `GET /api/setup/status` - Configuration guidance
- **MongoDB Status**: `GET /api/setup/mongodb-status` - Database connection
- **Health Check**: `GET /api/account/summary` - API connectivity test

### Getting Help
- Check the setup status endpoint first
- Review the [CLAUDE.md](./CLAUDE.md) file for detailed troubleshooting
- Ensure all environment variables are properly configured

