import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# MongoDB client
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
users_collection = database.get_collection("users")
zakat_collection = database.get_collection("zakat_entries")


async def connect_to_mongo():
    """Test MongoDB connection"""
    try:
        await client.admin.command('ping')
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")


async def close_mongo_connection():
    """Close MongoDB connection"""
    client.close()
    print("MongoDB connection closed")