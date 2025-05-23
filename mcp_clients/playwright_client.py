"""Playwright MCP client for web automation and testing."""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class PlaywrightMCPClient:
    """Client for web automation using Playwright through MCP."""
    
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.connected = False
        self.browser_context = None
    
    async def connect(self) -> bool:
        """Connect to the Playwright MCP server."""
        try:
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@microsoft/playwright-mcp"],
                env=None
            )
            
            self.session = await stdio_client(server_params).__aenter__()
            await self.session.initialize()
            self.connected = True
            logger.info("Connected to Playwright MCP server")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Playwright MCP server: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if self.session:
            try:
                # Close browser context if open
                if self.browser_context:
                    await self.close_browser()
                
                await self.session.__aexit__(None, None, None)
                self.connected = False
                logger.info("Disconnected from Playwright MCP server")
            except Exception as e:
                logger.error(f"Error disconnecting from Playwright MCP server: {e}")
    
    async def start_browser(self, headless: bool = True, record_video: bool = True, record_video_dir: str = "./videos") -> bool:
        """Start a new browser instance."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            options = {
                "headless": headless,
                "record_video": record_video
            }
            if record_video:
                options["record_video_dir"] = record_video_dir
            
            result = await self.session.call_tool(
                "playwright_launch_browser",
                arguments=options
            )
            
            if result.content:
                self.browser_context = True
                logger.info("Browser started successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error starting browser: {e}")
            return False
    
    async def close_browser(self) -> bool:
        """Close the browser instance."""
        if not self.connected or not self.session:
            return False
        
        try:
            result = await self.session.call_tool(
                "playwright_close_browser",
                arguments={}
            )
            self.browser_context = None
            logger.info("Browser closed successfully")
            return True
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return False
    
    async def navigate_to_page(self, url: str) -> bool:
        """Navigate to a specific URL."""
        if not self.connected or not self.session:
            await self.connect()
        
        try:
            result = await self.session.call_tool(
                "playwright_goto",
                arguments={"url": url}
            )
            logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    async def click_element(self, selector: str, timeout: int = 30000) -> bool:
        """Click on an element."""
        if not self.connected or not self.session:
            return False
        
        try:
            result = await self.session.call_tool(
                "playwright_click",
                arguments={"selector": selector, "timeout": timeout}
            )
            logger.info(f"Clicked element: {selector}")
            return True
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    async def fill_input(self, selector: str, text: str, timeout: int = 30000) -> bool:
        """Fill an input field with text."""
        if not self.connected or not self.session:
            return False
        
        try:
            result = await self.session.call_tool(
                "playwright_fill",
                arguments={"selector": selector, "text": text, "timeout": timeout}
            )
            logger.info(f"Filled input {selector} with text")
            return True
        except Exception as e:
            logger.error(f"Error filling input {selector}: {e}")
            return False
    
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """Wait for an element to be visible."""
        if not self.connected or not self.session:
            return False
        
        try:
            result = await self.session.call_tool(
                "playwright_wait_for_selector",
                arguments={"selector": selector, "timeout": timeout}
            )
            logger.info(f"Element {selector} is visible")
            return True
        except Exception as e:
            logger.error(f"Error waiting for element {selector}: {e}")
            return False
    
    async def take_screenshot(self, path: str = "screenshot.png") -> Optional[str]:
        """Take a screenshot of the current page."""
        if not self.connected or not self.session:
            return None
        
        try:
            result = await self.session.call_tool(
                "playwright_screenshot",
                arguments={"path": path, "full_page": True}
            )
            logger.info(f"Screenshot saved to {path}")
            return path
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None
    
    async def get_page_content(self) -> Optional[str]:
        """Get the HTML content of the current page."""
        if not self.connected or not self.session:
            return None
        
        try:
            result = await self.session.call_tool(
                "playwright_get_content",
                arguments={}
            )
            if result.content:
                return result.content[0].text
            return None
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return None
    
    async def evaluate_script(self, script: str) -> Any:
        """Execute JavaScript on the page."""
        if not self.connected or not self.session:
            return None
        
        try:
            result = await self.session.call_tool(
                "playwright_evaluate",
                arguments={"script": script}
            )
            if result.content:
                return json.loads(result.content[0].text)
            return None
        except Exception as e:
            logger.error(f"Error evaluating script: {e}")
            return None
    
    async def generate_pdf_report(self, path: str = "test_report.pdf") -> Optional[str]:
        """Generate a PDF report of the current page."""
        if not self.connected or not self.session:
            return None
        
        try:
            result = await self.session.call_tool(
                "playwright_pdf",
                arguments={
                    "path": path,
                    "format": "A4",
                    "print_background": True,
                    "margin": {
                        "top": "1cm",
                        "right": "1cm",
                        "bottom": "1cm",
                        "left": "1cm"
                    }
                }
            )
            logger.info(f"PDF report generated: {path}")
            return path
        except Exception as e:
            logger.error(f"Error generating PDF report: {e}")
            return None 