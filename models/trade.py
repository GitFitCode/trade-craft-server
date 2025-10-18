import motor.motor_asyncio
import os
import pydantic
from bson.objectid import ObjectId

# Use MongoDB URL from environment or fallback to None (disable MongoDB features)
mongodb_url = os.environ.get("MONGODB_URL")
if mongodb_url:
    db_client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
    db = db_client.development
    # Pydantic v2 compatibility - ObjectId encoding is handled differently
    pass
else:
    db_client = None
    db = None


class Trade:
    @staticmethod
    async def get_history():
        if db is None:
            # Return empty list if MongoDB is not configured
            print("MongoDB not configured - returning empty trade history")
            return []
        
        history = await db["trades"].find().to_list(1000)
        return history
