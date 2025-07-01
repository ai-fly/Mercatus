from app.manager import Manager
from app.utils.logging import setup_logger

# Set up main logger
logger = setup_logger(name="main")

async def main():

    try:
        
        logger.info("Initializing manager")
        manager = Manager()
        
        query = "Search for the deepseek wikipedia information and save it to a file."
        logger.info(f"Executing query: {query}")
        
        result = await manager.run(query)

        logger.debug(f"Final result: {result}")
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}", exc_info=True)
    finally:
        logger.info("Cleaning up resources...")



import asyncio
if __name__ == "__main__":
    logger.info("Starting application")
    asyncio.run(main())
    logger.info("Application ended")

