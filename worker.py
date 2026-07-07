import asyncio
import logging
# from app.config.database import engine
from app.config.redis import init_redis, close_redis
from app.messaging.rabbitmq import connect_rabbitmq, close_rabbitmq
from app.messaging.consumer import start_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

async def main():
    logger.info("Starting background worker...")
    
    
    await init_redis()
    await connect_rabbitmq()
    
   
    await start_consumer()
    
    try:
        
        await asyncio.Future()  
    except asyncio.CancelledError:
        logger.info("Worker shutting down...")
    finally:
        await close_redis()
        await close_rabbitmq()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker stopped manually.")