from config import config
from abc import ABC, abstractmethod


class DataProvider(ABC):
    """Abstract base class for data providers"""
    
    @abstractmethod
    def get_rest_client(self):
        """Get REST client for market data"""
        pass
    
    @abstractmethod
    def get_websocket_client(self):
        """Get WebSocket client for real-time data"""
        pass


class AlpacaDataProvider(DataProvider):
    """Alpaca data provider implementation"""
    
    def get_rest_client(self):
        # Import here to avoid circular imports
        from connectors.alpaca.rest.client import alpaca_rest_client
        return alpaca_rest_client
    
    def get_websocket_client(self):
        from connectors.alpaca.websocket.client import AlpacaWebSocketClient
        return AlpacaWebSocketClient()


class PolygonDataProvider(DataProvider):
    """Polygon data provider implementation"""
    
    def get_rest_client(self):
        from connectors.polygon.rest.client import polygon_rest_client
        return polygon_rest_client
    
    def get_websocket_client(self):
        from connectors.polygon.websocket.client import PolygonWebSocketClient
        return PolygonWebSocketClient()


class DataProviderFactory:
    """Factory to create the appropriate data provider based on feature flags"""
    
    @staticmethod
    def create_data_provider() -> DataProvider:
        """Create data provider based on feature flags"""
        
        if config["FEATURES"]["USE_POLYGON_FOR_DATA"]:
            print("Using Polygon for data")
            return PolygonDataProvider()
        elif config["FEATURES"]["USE_ALPACA_FOR_DATA"]:
            print("Using Alpaca for data")
            return AlpacaDataProvider()
        else:
            # Default to Alpaca if no flags are set
            print("Defaulting to Alpaca for data")
            return AlpacaDataProvider()


# Global instance
data_provider = DataProviderFactory.create_data_provider()