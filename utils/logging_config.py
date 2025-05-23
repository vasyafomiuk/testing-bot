"""Logging configuration for the testing agent."""
import logging
import sys
from config import config


def setup_logging():
    """Setup logging configuration for the application."""
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.upper()))
    root_logger.addHandler(console_handler)
    
    # Configure specific loggers
    loggers = [
        'agents.testing_agent',
        'mcp_clients.atlassian_client',
        'mcp_clients.playwright_client',
        'slack_bot.bot'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Reduce noise from external libraries
    logging.getLogger('slack_bolt').setLevel(logging.WARNING)
    logging.getLogger('slack_sdk').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    logging.info("Logging configured successfully") 