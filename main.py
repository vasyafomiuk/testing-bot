"""Main entry point for the testing agent application."""
import asyncio
import logging
import os
import signal
import sys
from typing import Optional

from utils.logging_config import setup_logging
from slack_bot.bot import TestingSlackBot

logger = logging.getLogger(__name__)


class TestingAgentApp:
    """Main application class for the testing agent."""
    
    def __init__(self):
        self.bot: Optional[TestingSlackBot] = None
        self.running = False
    
    async def start(self):
        """Start the testing agent application."""
        try:
            logger.info("Starting Testing Agent Application...")
            
            # Create necessary directories
            os.makedirs('./videos', exist_ok=True)
            os.makedirs('./screenshots', exist_ok=True)
            os.makedirs('./reports', exist_ok=True)
            
            # Initialize and start the Slack bot
            self.bot = TestingSlackBot()
            self.running = True
            
            logger.info("Testing Agent Application started successfully")
            await self.bot.start()
            
        except Exception as e:
            logger.error(f"Failed to start Testing Agent Application: {e}")
            sys.exit(1)
    
    async def stop(self):
        """Stop the testing agent application."""
        if self.running and self.bot:
            logger.info("Stopping Testing Agent Application...")
            await self.bot.stop()
            self.running = False
            logger.info("Testing Agent Application stopped")
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function."""
    # Setup logging
    setup_logging()
    
    # Create and start the application
    app = TestingAgentApp()
    app.setup_signal_handlers()
    
    try:
        await app.start()
        
        # Keep the application running
        while app.running:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    # Check for required environment variables
    required_env_vars = [
        'OPENAI_API_KEY',
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN',
        'SLACK_SIGNING_SECRET',
        'JIRA_URL',
        'CONFLUENCE_URL',
        'ATLASSIAN_EMAIL',
        'ATLASSIAN_API_TOKEN'
    ]
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please check your .env file or environment configuration.")
        sys.exit(1)
    
    print("🚀 Starting Testing Agent Application...")
    asyncio.run(main()) 