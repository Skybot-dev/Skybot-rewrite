from motor.motor_asyncio import AsyncIOMotorClient
from utils.util import get_config
from loguru import logger
@logger.catch()
def init_client(loop):
    logger.info("Connecting to Database...")
    config = get_config()["database"]
    return AsyncIOMotorClient(f"mongodb://{config['username']}:{config['password']}@{config['address']}/{config['default_db']}?retryWrites=true&w=majority", io_loop=loop)