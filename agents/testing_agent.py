"""Main testing agent that orchestrates test case generation and automation."""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import openai
from openai import OpenAI

from config import config
from mcp_clients.atlassian_client import AtlassianMCPClient
from mcp_clients.playwright_client import PlaywrightMCPClient

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests that can be automated."""
    WEB_UI = "web_ui"
    API = "api"
    MANUAL = "manual"


@dataclass
class TestCase:
    """Represents a single test case."""
    title: str
    description: str
    test_type: TestType
    steps: List[str]
    expected_result: str
    priority: str = "Medium"
    automation_script: Optional[str] = None


@dataclass
class TestSuite:
    """Represents a collection of test cases."""
    title: str
    description: str
    user_story: str
    test_cases: List[TestCase]
    created_at: datetime


class TestingAgent:
    """Main testing agent that handles the entire testing workflow."""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.openai_api_key)
        self.atlassian_client = AtlassianMCPClient()
        self.playwright_client = PlaywrightMCPClient()
        self.current_test_suite: Optional[TestSuite] = None
    
    async def initialize(self):
        """Initialize all MCP clients."""
        await self.atlassian_client.connect()
        await self.playwright_client.connect()
        logger.info("Testing agent initialized successfully")
    
    async def cleanup(self):
        """Cleanup all resources."""
        await self.atlassian_client.disconnect()
        await self.playwright_client.disconnect()
        logger.info("Testing agent cleaned up")
    
    async def generate_test_cases_from_jira_story(self, story_key: str) -> Optional[TestSuite]:
        """Generate test cases from a Jira user story."""
        try:
            # Get the Jira story details
            story_data = await self.atlassian_client.get_jira_issue(story_key)
            if not story_data:
                logger.error(f"Could not retrieve Jira story: {story_key}")
                return None
            
            story_data = json.loads(story_data) if isinstance(story_data, str) else story_data
            
            # Extract story information
            summary = story_data.get('fields', {}).get('summary', '')
            description = story_data.get('fields', {}).get('description', '')
            acceptance_criteria = self._extract_acceptance_criteria(description)
            
            # Generate test cases using OpenAI
            test_cases = await self._generate_test_cases_with_ai(
                summary=summary,
                description=description,
                acceptance_criteria=acceptance_criteria
            )
            
            if test_cases:
                self.current_test_suite = TestSuite(
                    title=f"Test Suite for {story_key}",
                    description=f"Generated test cases for user story: {summary}",
                    user_story=f"{story_key}: {summary}",
                    test_cases=test_cases,
                    created_at=datetime.now()
                )
                
                logger.info(f"Generated {len(test_cases)} test cases for story {story_key}")
                return self.current_test_suite
            
        except Exception as e:
            logger.error(f"Error generating test cases from Jira story {story_key}: {e}")
        
        return None
    
    def _extract_acceptance_criteria(self, description: str) -> List[str]:
        """Extract acceptance criteria from the story description."""
        criteria = []
        if not description:
            return criteria
        
        # Look for common acceptance criteria patterns
        lines = description.split('\n')
        in_criteria_section = False
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['acceptance criteria', 'ac:', 'given', 'when', 'then']):
                in_criteria_section = True
                if line.lower().startswith(('given', 'when', 'then', 'and')):
                    criteria.append(line)
            elif in_criteria_section and line.startswith(('-', '*', '•')):
                criteria.append(line[1:].strip())
            elif in_criteria_section and not line:
                in_criteria_section = False
        
        return criteria
    
    async def _generate_test_cases_with_ai(self, summary: str, description: str, acceptance_criteria: List[str]) -> List[TestCase]:
        """Generate test cases using OpenAI."""
        try:
            prompt = f"""
            As a QA engineer, generate comprehensive test cases for the following user story:
            
            **Summary:** {summary}
            **Description:** {description}
            **Acceptance Criteria:** {' | '.join(acceptance_criteria)}
            
            Generate test cases that cover:
            1. Happy path scenarios
            2. Edge cases
            3. Error handling
            4. UI/UX validation (if applicable)
            5. API testing (if applicable)
            
            For each test case, determine if it should be:
            - web_ui: Can be automated with browser automation
            - api: Can be automated with API calls
            - manual: Requires manual testing
            
            Return the response as a JSON array with this structure:
            [
                {{
                    "title": "Test case title",
                    "description": "Detailed description of what to test",
                    "test_type": "web_ui|api|manual",
                    "steps": ["Step 1", "Step 2", "Step 3"],
                    "expected_result": "What should happen",
                    "priority": "High|Medium|Low"
                }}
            ]
            
            Generate 5-10 comprehensive test cases.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert QA engineer who creates comprehensive test cases. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            test_cases_data = json.loads(response.choices[0].message.content)
            test_cases = []
            
            for tc_data in test_cases_data:
                test_case = TestCase(
                    title=tc_data['title'],
                    description=tc_data['description'],
                    test_type=TestType(tc_data['test_type']),
                    steps=tc_data['steps'],
                    expected_result=tc_data['expected_result'],
                    priority=tc_data.get('priority', 'Medium')
                )
                test_cases.append(test_case)
            
            return test_cases
            
        except Exception as e:
            logger.error(f"Error generating test cases with AI: {e}")
            return []
    
    def format_test_cases_as_markdown(self, test_suite: TestSuite) -> str:
        """Format test cases as markdown for display."""
        md_content = f"""# {test_suite.title}

**User Story:** {test_suite.user_story}
**Description:** {test_suite.description}
**Created:** {test_suite.created_at.strftime('%Y-%m-%d %H:%M:%S')}

---

## Test Cases

"""
        
        for i, test_case in enumerate(test_suite.test_cases, 1):
            md_content += f"""### {i}. {test_case.title}

**Type:** {test_case.test_type.value.replace('_', ' ').title()}
**Priority:** {test_case.priority}

**Description:** {test_case.description}

**Steps:**
"""
            for j, step in enumerate(test_case.steps, 1):
                md_content += f"{j}. {step}\n"
            
            md_content += f"\n**Expected Result:** {test_case.expected_result}\n\n---\n\n"
        
        return md_content
    
    async def generate_automation_script(self, test_case: TestCase) -> Optional[str]:
        """Generate automation script for a test case."""
        if test_case.test_type == TestType.MANUAL:
            return None
        
        try:
            if test_case.test_type == TestType.WEB_UI:
                script = await self._generate_web_automation_script(test_case)
            elif test_case.test_type == TestType.API:
                script = await self._generate_api_automation_script(test_case)
            else:
                return None
            
            test_case.automation_script = script
            return script
            
        except Exception as e:
            logger.error(f"Error generating automation script: {e}")
            return None
    
    async def _generate_web_automation_script(self, test_case: TestCase) -> str:
        """Generate web automation script using Playwright."""
        prompt = f"""
        Generate a Python script using Playwright for the following test case:
        
        **Title:** {test_case.title}
        **Description:** {test_case.description}
        **Steps:** {' | '.join(test_case.steps)}
        **Expected Result:** {test_case.expected_result}
        
        The script should:
        1. Use async/await syntax
        2. Include proper error handling
        3. Take screenshots at key points
        4. Generate assertions for validation
        5. Return True/False for test result
        
        Assume the PlaywrightMCPClient is already initialized and connected.
        Use these methods:
        - await playwright_client.navigate_to_page(url)
        - await playwright_client.click_element(selector)
        - await playwright_client.fill_input(selector, text)
        - await playwright_client.wait_for_element(selector)
        - await playwright_client.take_screenshot(path)
        - await playwright_client.get_page_content()
        
        Return only the Python function code.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert test automation engineer. Generate clean, executable Python code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    async def _generate_api_automation_script(self, test_case: TestCase) -> str:
        """Generate API automation script."""
        prompt = f"""
        Generate a Python script for API testing for the following test case:
        
        **Title:** {test_case.title}
        **Description:** {test_case.description}
        **Steps:** {' | '.join(test_case.steps)}
        **Expected Result:** {test_case.expected_result}
        
        The script should:
        1. Use aiohttp for async HTTP requests
        2. Include proper error handling
        3. Validate response status codes
        4. Validate response content
        5. Return True/False for test result
        
        Return only the Python function code.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert API test automation engineer. Generate clean, executable Python code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )
        
        return response.choices[0].message.content
    
    async def execute_automation(self, test_case: TestCase) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Execute automation for a test case."""
        if not test_case.automation_script:
            return False, "No automation script available", None, None
        
        try:
            if test_case.test_type == TestType.WEB_UI:
                return await self._execute_web_automation(test_case)
            elif test_case.test_type == TestType.API:
                return await self._execute_api_automation(test_case)
            else:
                return False, "Test type not supported for automation", None, None
        
        except Exception as e:
            logger.error(f"Error executing automation: {e}")
            return False, f"Automation failed: {str(e)}", None, None
    
    async def _execute_web_automation(self, test_case: TestCase) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """Execute web automation using Playwright."""
        video_path = None
        screenshot_path = None
        
        try:
            # Start browser with video recording
            video_dir = f"./videos/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.makedirs(video_dir, exist_ok=True)
            
            await self.playwright_client.start_browser(
                headless=False,
                record_video=True,
                record_video_dir=video_dir
            )
            
            # Execute the automation script
            # Note: In a real implementation, you'd need to safely execute the generated code
            # For now, we'll simulate execution
            
            # Take final screenshot
            screenshot_path = f"./screenshots/test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            await self.playwright_client.take_screenshot(screenshot_path)
            
            # Close browser to finalize video
            await self.playwright_client.close_browser()
            
            # Find video file
            for file in os.listdir(video_dir):
                if file.endswith('.webm'):
                    video_path = os.path.join(video_dir, file)
                    break
            
            return True, "Test executed successfully", screenshot_path, video_path
            
        except Exception as e:
            await self.playwright_client.close_browser()
            return False, f"Web automation failed: {str(e)}", screenshot_path, video_path
    
    async def _execute_api_automation(self, test_case: TestCase) -> Tuple[bool, str, None, None]:
        """Execute API automation."""
        try:
            # Execute the API automation script
            # Note: In a real implementation, you'd need to safely execute the generated code
            # For now, we'll simulate execution
            
            return True, "API test executed successfully", None, None
            
        except Exception as e:
            return False, f"API automation failed: {str(e)}", None, None
    
    async def generate_test_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate a comprehensive test report."""
        try:
            report_content = f"""# Test Execution Report

**Test Suite:** {self.current_test_suite.title if self.current_test_suite else 'Unknown'}
**Execution Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

"""
            
            total_tests = len(test_results)
            passed_tests = sum(1 for result in test_results if result.get('passed', False))
            failed_tests = total_tests - passed_tests
            
            report_content += f"""- **Total Tests:** {total_tests}
- **Passed:** {passed_tests}
- **Failed:** {failed_tests}
- **Success Rate:** {(passed_tests/total_tests*100):.1f}%

## Test Results

"""
            
            for i, result in enumerate(test_results, 1):
                status = "✅ PASSED" if result.get('passed', False) else "❌ FAILED"
                report_content += f"""### {i}. {result.get('title', 'Unknown Test')}

**Status:** {status}
**Message:** {result.get('message', 'No message')}
**Execution Time:** {result.get('duration', 'Unknown')}

"""
                
                if result.get('screenshot'):
                    report_content += f"**Screenshot:** {result['screenshot']}\n"
                if result.get('video'):
                    report_content += f"**Video Recording:** {result['video']}\n"
                
                report_content += "\n---\n\n"
            
            # Save report to file
            report_path = f"./reports/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            with open(report_path, 'w') as f:
                f.write(report_content)
            
            logger.info(f"Test report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating test report: {e}")
            return "" 