from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.config import config

logger = logging.getLogger(__name__)

class DatabaseWorker:
    client: AsyncIOMotorClient = None
    db = None

db_worker = DatabaseWorker()

async def connect_to_mongo():
    if not config.MONGODB_URI:
        logger.warning("MONGODB_URI is not set. Database connection skipped.")
        return

    try:
        db_worker.client = AsyncIOMotorClient(config.MONGODB_URI)
        db_worker.db = db_worker.client[config.MONGODB_DB_NAME]
        
        # Ping to confirm the connection is successful
        await db_worker.db.command("ping")
        logger.info(f"Successfully connected to MongoDB Atlas database: {config.MONGODB_DB_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB Atlas: {e}")
        raise

async def close_mongo_connection():
    if db_worker.client:
        db_worker.client.close()
        logger.info("Closed MongoDB connection.")

def get_db():
    if db_worker.db is None:
        raise ConnectionError("Database is not connected.")
    return db_worker.db
