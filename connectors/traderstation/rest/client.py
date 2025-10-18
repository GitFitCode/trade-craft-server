import requests
from datetime import datetime
from config import config


class TraderStationClient:
    def __init__(self):
        self.api_key = config["TRADERSTATION"]["API_KEY"]
        self.api_secret = config["TRADERSTATION"]["API_SECRET"]
        self.account_id = config["TRADERSTATION"]["ACCOUNT_ID"]
        self.base_url = config["TRADERSTATION"]["BASE_URL"]
        self.access_token = None
        self.token_expiry = None
        
    def _authenticate(self):
        """Get or refresh access token"""
        if self.access_token and self.token_expiry and datetime.now() < self.token_expiry:
            return
            
        # TraderStation OAuth2 flow
        auth_url = f"{self.base_url}/v3/security/authorize"
        token_url = f"{self.base_url}/v3/security/token"
        
        # For paper trading, TraderStation provides a simplified auth flow
        # This is a placeholder - actual implementation depends on TraderStation's auth requirements
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.api_secret,
            "scope": "trade"
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Set token expiry
            expires_in = token_data.get("expires_in", 3600)
            self.token_expiry = datetime.now().timestamp() + expires_in
        else:
            raise Exception(f"Authentication failed: {response.text}")
    
    def _request(self, method, endpoint, data=None, params=None):
        """Make authenticated request to TraderStation API"""
        self._authenticate()
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=headers, json=data, params=params)
        
        if response.status_code >= 400:
            raise Exception(f"API request failed: {response.text}")
            
        return response.json()
    
    def get_account(self):
        """Get account information"""
        return self._request("GET", f"/v3/brokerage/accounts/{self.account_id}")
    
    def get_positions(self):
        """Get all positions"""
        return self._request("GET", f"/v3/brokerage/accounts/{self.account_id}/positions")
    
    def get_orders(self, status=None):
        """Get orders with optional status filter"""
        params = {"status": status} if status else {}
        return self._request("GET", f"/v3/brokerage/accounts/{self.account_id}/orders", params=params)
    
    def submit_order(self, order_data):
        """Submit a new order"""
        # Transform order_data to TraderStation format
        ts_order = {
            "AccountID": self.account_id,
            "Symbol": order_data.get("symbol"),
            "Quantity": order_data.get("qty"),
            "OrderType": order_data.get("order_type", "Market"),
            "TradeAction": order_data.get("side", "BUY").upper(),
            "TimeInForce": {
                "GTC": "GoodTillCanceled",
                "DAY": "DayOrder",
                "IOC": "ImmediateOrCancel"
            }.get(order_data.get("time_in_force", "DAY"), "DayOrder"),
            "Route": "Intelligent"  # TraderStation's smart routing
        }
        
        return self._request("POST", "/v3/brokerage/orders", data=ts_order)
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        return self._request("DELETE", f"/v3/brokerage/orders/{order_id}")
    
    def get_account_balances(self):
        """Get account balances"""
        return self._request("GET", f"/v3/brokerage/accounts/{self.account_id}/balances")
    
    def get_market_hours(self, market="EQUITY"):
        """Get market hours"""
        return self._request("GET", f"/v3/marketdata/markets/{market}/hours")


# Initialize the TraderStation client
traderstation_client = TraderStationClient()