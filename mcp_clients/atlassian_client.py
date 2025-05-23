"""Atlassian MCP client for Jira and Confluence integration."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from config import config

logger = logging.getLogger(__name__)


class AtlassianMCPClient:
    """Client for interacting with Atlassian services through MCP."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.connected = False
    
    async def connect(self) -> bool:
        """Connect to the Atlassian MCP server."""
        try:
            server_params = StdioServerParameters(
                command="uvx",
                args=[
                    "mcp-atlassian",
                    "--jira-url", config.jira_url,
                    "--confluence-url", config.confluence_url,
                    "--jira-email", config.atlassian_email,
                    "--jira-api-token", config.atlassian_api_token,
                    "--confluence-email", config.atlassian_email,
                    "--confluence-api-token", config.atlassian_api_token,
                ],
                env=None
            )
            
            self.session = await stdio_client(server_params).__aenter__()
            await self.session.initialize()
            self.connected = True
            logger.info("Connected to Atlassian MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Atlassian MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                await self.session.__aexit__(None, None, None)
                self.connected = False
                logger.info("Disconnected from Atlassian MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from Atlassian MCP server: {e}")
    
    async def get_jira_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get details of a specific Jira issue."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "jira_get_issue",
                arguments={"issue_key": issue_key}
            )
            return result.content[0].text if result.content else None
        except Exception as e:
            logger.error(f"Error getting Jira issue {issue_key}: {e}")
            return None
    
    async def search_jira_issues(self, jql: str, max_results: int = 50) -> Optional[List[Dict[str, Any]]]:
        """Search Jira issues using JQL."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "jira_search",
                arguments={"jql": jql, "max_results": max_results}
            )
            if result.content:
                return json.loads(result.content[0].text)
            return None
        except Exception as e:
            logger.error(f"Error searching Jira issues: {e}")
            return None
    
    async def create_confluence_page(self, space_key: str, title: str, content: str, parent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Create a new Confluence page."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            args = {
                "space_key": space_key,
                "title": title,
                "content": content
            }
            if parent_id:
                args["parent_id"] = parent_id
            
            result = await self.session.call_tool(
                "confluence_create_page",
                arguments=args
            )
            if result.content:
                return json.loads(result.content[0].text)
            return None
        except Exception as e:
            logger.error(f"Error creating Confluence page: {e}")
            return None
    
    async def update_confluence_page(self, page_id: str, title: str, content: str, version: int) -> Optional[Dict[str, Any]]:
        """Update an existing Confluence page."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "confluence_update_page",
                arguments={
                    "page_id": page_id,
                    "title": title,
                    "content": content,
                    "version": version
                }
            )
            if result.content:
                return json.loads(result.content[0].text)
            return None
        except Exception as e:
            logger.error(f"Error updating Confluence page: {e}")
            return None
    
    async def search_confluence_content(self, cql: str, limit: int = 25) -> Optional[List[Dict[str, Any]]]:
        """Search Confluence content using CQL."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "confluence_search",
                arguments={"cql": cql, "limit": limit}
            )
            if result.content:
                return json.loads(result.content[0].text)
            return None
        except Exception as e:
            logger.error(f"Error searching Confluence content: {e}")
            return None 