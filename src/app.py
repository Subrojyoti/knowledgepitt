from fastapi import FastAPI
from contextlib import asynccontextmanager
from config.common_config import options
from src.utils.Logger import Logger

logger = Logger().get_simple_logger("KnowledgePitt")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    yield
    logger.info("Shutting down application...")
    
app = FastAPI(lifespan=lifespan)
