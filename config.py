"""Configuration management for the testing agent."""
import os
from typing import Optional
from pydantic import BaseSettings, Field


class Config(BaseSettings):
    """Application configuration."""
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    
    # Slack Configuration
    slack_bot_token: str = Field(..., env="SLACK_BOT_TOKEN")
    slack_app_token: str = Field(..., env="SLACK_APP_TOKEN")
    slack_signing_secret: str = Field(..., env="SLACK_SIGNING_SECRET")
    
    # Atlassian Configuration
    jira_url: str = Field(..., env="JIRA_URL")
    confluence_url: str = Field(..., env="CONFLUENCE_URL")
    atlassian_email: str = Field(..., env="ATLASSIAN_EMAIL")
    atlassian_api_token: str = Field(..., env="ATLASSIAN_API_TOKEN")
    
    # MCP Server Configuration
    atlassian_mcp_port: int = Field(8001, env="ATLASSIAN_MCP_PORT")
    playwright_mcp_port: int = Field(8002, env="PLAYWRIGHT_MCP_PORT")
    
    # Application Configuration
    debug: bool = Field(False, env="DEBUG")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global configuration instance
config = Config() 