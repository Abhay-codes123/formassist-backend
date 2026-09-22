from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
client = None
db = None

async def connect_db():
    global client, db
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client.formassist
    print("✅ MongoDB Connected!")
    return db

async def close_db():
    global client
    if client:
        client.close()

def get_db():
    return db
