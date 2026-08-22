import asyncio
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("worker")


async def run_worker():
    logger.info("Supply Chain Ops background worker started")
    while True:
        try:
            await asyncio.sleep(30)
            logger.debug("Worker heartbeat...")
        except asyncio.CancelledError:
            logger.info("Worker shutting down")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(run_worker())
