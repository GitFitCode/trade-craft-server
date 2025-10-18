# Trader Craft Server

# Extended By Devs @ <a href="https://www.gitfitcode.com" target="_blank">gitfitcode</a> and huge thanks to <a href="https://github.com/robertjosephwayne" target="_blank">Robert</a> who developed <a href="https://www.financebrain.ai/" target="_blank">FinanceBrain</a> for the initial idea and implementation.

## Common Development Commands

### Running the Server
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally with uvicorn
uvicorn main:app --reload

# Run with specified host and port
uvicorn --host 0.0.0.0 --port 8000 main:app --workers 1
```

### Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (macOS/Linux)
source venv/bin/activate

# Activate virtual environment (Windows)
venv\Scripts\activate
```

### Dependencies
- FastAPI framework for REST API endpoints
- Socket.IO for real-time WebSocket communication
- Alpaca API for crypto/stock trading (alpaca-py, alpaca-trade-api)
- Tradier API for options/stock trading (tradier-python)
- pandas/numpy for data processing
- Sentry for error tracking

## High-Level Architecture

### Core Components

1. **Trading Connectors** (`/connectors/`)
   - **Alpaca**: REST and WebSocket clients for crypto/stock trading
   - **Tradier**: REST client for stock/options trading
   - Trading mode (PAPER/LIVE) controlled via environment variables

2. **Bot System** (`bot.py`)
   - Main trading bot that processes market data bars
   - Implements position management and risk controls
   - Processes both crypto bars (24/7) and stock bars (market hours)
   - Uses strategies (e.g., MovingAverageCrossoverStrategy) for trading signals

3. **API Routes** (`/routes/`)
   - **Account**: Account summary, positions, history, gain/loss, orders
   - **Market**: Market data endpoints
   - **Portfolio**: Portfolio management endpoints  
   - **Trades**: Trade execution endpoints
   - All routes prefixed with `/api/`

4. **Models** (`/models/`)
   - Data models that interface with trading connectors
   - Abstraction layer between routes and external APIs

5. **Strategies** (`/strategies/`)
   - Trading strategy implementations
   - MovingAverageCrossoverStrategy configured with SMA parameters

### Configuration System
- Environment variables loaded via `python-dotenv`
- Dual-mode configuration (PAPER/LIVE) for both Alpaca and Tradier
- API keys and secrets stored in environment variables
- CORS configured for client URL specified in environment

### Real-time Architecture
- FastAPI with Socket.IO integration for WebSocket support
- Alpaca WebSocket client subscribes to crypto bar data (e.g., BTC/USD)
- Bot processes incoming bars in real-time

### Deployment
- Heroku deployment configured via `Procfile`
- Single worker process to maintain WebSocket connections
- Sentry integration for production error tracking

## Key Behaviors

### Trading Logic
- Bot maintains maximum position allocation limits
- Checks non-marginable buying power before trading
- Implements stop-loss and take-profit logic for short positions
- Relative strength trading against ETF benchmarks (SPY/QQQ)

### API Integration Patterns
- Tradier used as primary broker for account/portfolio data
- Alpaca used for crypto trading and market data
- All API responses passed through directly to frontend

