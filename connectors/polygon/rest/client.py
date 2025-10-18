from config import config
from polygon import RESTClient

# Get API key from config
api_key = config["POLYGON"]["API_KEY"]

# Initialize Polygon REST client
polygon_rest_client = RESTClient(api_key=api_key)