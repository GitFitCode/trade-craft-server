from config import config
from abc import ABC, abstractmethod


class TradingProvider(ABC):
    """Abstract base class for trading providers"""
    
    @abstractmethod
    def get_client(self):
        """Get trading client"""
        pass
    
    @abstractmethod
    def get_positions(self):
        """Get account positions"""
        pass
    
    @abstractmethod
    def get_account_info(self):
        """Get account information"""
        pass
    
    @abstractmethod
    def submit_order(self, order_data):
        """Submit a trading order"""
        pass


class TradierTradingProvider(TradingProvider):
    """Tradier trading provider implementation"""
    
    def get_client(self):
        from connectors.tradier.rest.client import tradier_rest_client
        return tradier_rest_client
    
    def get_positions(self):
        client = self.get_client()
        return client.get_positions()
    
    def get_account_info(self):
        client = self.get_client()
        return client.get_balances()
    
    def submit_order(self, order_data):
        client = self.get_client()
        # Convert order_data to Tradier format if needed
        return client.submit_order(order_data)


class TraderStationTradingProvider(TradingProvider):
    """TraderStation trading provider implementation"""
    
    def get_client(self):
        from connectors.traderstation.rest.client import traderstation_client
        return traderstation_client
    
    def get_positions(self):
        client = self.get_client()
        return client.get_positions()
    
    def get_account_info(self):
        client = self.get_client()
        return client.get_account_balances()
    
    def submit_order(self, order_data):
        client = self.get_client()
        return client.submit_order(order_data)


class AlpacaTradingProvider(TradingProvider):
    """Alpaca trading provider implementation (for comparison/fallback)"""
    
    def get_client(self):
        from connectors.alpaca.rest.client import alpaca_rest_client
        return alpaca_rest_client
    
    def get_positions(self):
        client = self.get_client()
        return client.get_all_positions()
    
    def get_account_info(self):
        client = self.get_client()
        return client.get_account()
    
    def submit_order(self, order_data):
        client = self.get_client()
        return client.submit_order(order_data)


class TradingProviderFactory:
    """Factory to create the appropriate trading provider based on feature flags"""
    
    @staticmethod
    def create_trading_provider() -> TradingProvider:
        """Create trading provider based on feature flags"""
        
        if config["FEATURES"]["USE_TRADERSTATION_FOR_TRADING"]:
            print("Using TraderStation for trading")
            return TraderStationTradingProvider()
        elif config["FEATURES"]["USE_TRADIER_FOR_TRADING"]:
            print("Using Tradier for trading")
            return TradierTradingProvider()
        else:
            # Default to Tradier if no flags are set
            print("Defaulting to Tradier for trading")
            return TradierTradingProvider()


# Global instance
trading_provider = TradingProviderFactory.create_trading_provider()