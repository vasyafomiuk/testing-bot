"""Slack bot implementation for the testing agent."""
import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Dict, List, Optional

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from config import config
from agents.testing_agent import TestingAgent, TestType

logger = logging.getLogger(__name__)


class TestingSlackBot:
    """Slack bot for the testing agent workflow."""
    
    def __init__(self):
        self.app = AsyncApp(
            token=config.slack_bot_token,
            signing_secret=config.slack_signing_secret
        )
        self.testing_agent = TestingAgent()
        self.user_sessions: Dict[str, Dict] = {}
        
        # Register event handlers
        self._register_handlers()
    
    def _register_handlers(self):
        """Register all Slack event handlers."""
        
        @self.app.message(re.compile(r"(hi|hello|hey)", re.IGNORECASE))
        async def handle_greeting(message, say):
            """Handle greeting messages."""
            await say(
                text="Hello! 👋 I'm your testing automation assistant!",
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Hello! 👋 I'm your testing automation assistant!\n\nI can help you generate test cases from Jira user stories and automate them. Here's how to get started:"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "📝 *To generate test cases:*\n`generate tests for JIRA-123`\n\n🤖 *To automate tests:*\nFirst generate test cases, then I'll ask if you want to automate them!"
                        }
                    }
                ]
            )
        
        @self.app.message(re.compile(r"generate tests for ([A-Z]+-\d+)", re.IGNORECASE))
        async def handle_generate_tests(message, say):
            """Handle test generation requests."""
            user_id = message['user']
            channel_id = message['channel']
            
            # Extract Jira issue key
            match = re.search(r"([A-Z]+-\d+)", message['text'], re.IGNORECASE)
            if not match:
                await say("❌ Please provide a valid Jira issue key (e.g., PROJ-123)")
                return
            
            jira_key = match.group(1).upper()
            
            # Show loading message
            loading_response = await say("🔄 Generating test cases for `{}`. This might take a moment...".format(jira_key))
            
            try:
                # Generate test cases
                test_suite = await self.testing_agent.generate_test_cases_from_jira_story(jira_key)
                
                if not test_suite:
                    await self.app.client.chat_update(
                        channel=channel_id,
                        ts=loading_response['ts'],
                        text="❌ Failed to generate test cases. Please check the Jira issue key and try again."
                    )
                    return
                
                # Store session data
                self.user_sessions[user_id] = {
                    'test_suite': test_suite,
                    'jira_key': jira_key,
                    'channel_id': channel_id,
                    'step': 'review_tests'
                }
                
                # Format test cases as markdown
                test_cases_md = self.testing_agent.format_test_cases_as_markdown(test_suite)
                
                # Update the loading message with results
                await self.app.client.chat_update(
                    channel=channel_id,
                    ts=loading_response['ts'],
                    text="✅ Test cases generated successfully!",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"✅ *Test cases generated for {jira_key}*\n\nI've created {len(test_suite.test_cases)} test cases. Please review them below:"
                            }
                        },
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"```{test_cases_md[:2900]}{'...' if len(test_cases_md) > 2900 else ''}```"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "✅ Approve Tests"},
                                    "style": "primary",
                                    "action_id": "approve_tests",
                                    "value": user_id
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "❌ Regenerate"},
                                    "action_id": "regenerate_tests",
                                    "value": user_id
                                }
                            ]
                        }
                    ]
                )
                
            except Exception as e:
                logger.error(f"Error generating test cases: {e}")
                await self.app.client.chat_update(
                    channel=channel_id,
                    ts=loading_response['ts'],
                    text="❌ An error occurred while generating test cases. Please try again."
                )
        
        @self.app.action("approve_tests")
        async def handle_approve_tests(ack, body, say):
            """Handle test approval."""
            await ack()
            
            user_id = body['user']['id']
            if user_id not in self.user_sessions:
                await say("❌ Session expired. Please generate test cases again.")
                return
            
            session = self.user_sessions[user_id]
            test_suite = session['test_suite']
            
            # Count automatable tests
            automatable_tests = [tc for tc in test_suite.test_cases if tc.test_type in [TestType.WEB_UI, TestType.API]]
            manual_tests = [tc for tc in test_suite.test_cases if tc.test_type == TestType.MANUAL]
            
            if automatable_tests:
                await say(
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"🎯 *Test cases approved!*\n\nI found {len(automatable_tests)} automatable tests and {len(manual_tests)} manual tests.\n\nWould you like me to automate the web and API tests?"
                            }
                        },
                        {
                            "type": "actions",
                            "elements": [
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "🤖 Automate Tests"},
                                    "style": "primary",
                                    "action_id": "automate_tests",
                                    "value": user_id
                                },
                                {
                                    "type": "button",
                                    "text": {"type": "plain_text", "text": "📋 Manual Only"},
                                    "action_id": "manual_only",
                                    "value": user_id
                                }
                            ]
                        }
                    ]
                )
                session['step'] = 'choose_automation'
            else:
                await say("📋 All test cases are manual tests. No automation is possible for this story.")
                # Clean up session
                del self.user_sessions[user_id]
        
        @self.app.action("regenerate_tests")
        async def handle_regenerate_tests(ack, body, say):
            """Handle test regeneration."""
            await ack()
            
            user_id = body['user']['id']
            await say("🔄 Please provide the Jira issue key again to regenerate test cases.")
            
            # Clean up session
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]
        
        @self.app.action("automate_tests")
        async def handle_automate_tests(ack, body, say):
            """Handle test automation."""
            await ack()
            
            user_id = body['user']['id']
            if user_id not in self.user_sessions:
                await say("❌ Session expired. Please generate test cases again.")
                return
            
            session = self.user_sessions[user_id]
            test_suite = session['test_suite']
            
            # Show automation progress
            progress_response = await say("🤖 Starting test automation. This may take several minutes...")
            
            try:
                await self._execute_automation(user_id, test_suite, progress_response)
                
            except Exception as e:
                logger.error(f"Error during automation: {e}")
                await self.app.client.chat_update(
                    channel=session['channel_id'],
                    ts=progress_response['ts'],
                    text="❌ An error occurred during test automation. Please try again."
                )
            finally:
                # Clean up session
                if user_id in self.user_sessions:
                    del self.user_sessions[user_id]
        
        @self.app.action("manual_only")
        async def handle_manual_only(ack, body, say):
            """Handle manual-only test execution."""
            await ack()
            
            user_id = body['user']['id']
            if user_id not in self.user_sessions:
                await say("❌ Session expired. Please generate test cases again.")
                return
            
            await say("📋 Test cases saved for manual execution. You can find them in the test case document.")
            
            # Clean up session
            del self.user_sessions[user_id]
        
        @self.app.message(re.compile(r"help", re.IGNORECASE))
        async def handle_help(message, say):
            """Handle help requests."""
            await say(
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🤖 *Testing Bot Help*\n\nHere's what I can do for you:"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": "*Generate Test Cases:*\n`generate tests for PROJ-123`"
                            },
                            {
                                "type": "mrkdwn",
                                "text": "*Get Help:*\n`help`"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "🔄 *Workflow:*\n1. Provide a Jira user story\n2. Review generated test cases\n3. Approve or regenerate\n4. Choose automation or manual execution\n5. Get reports with videos and screenshots"
                        }
                    }
                ]
            )
    
    async def _execute_automation(self, user_id: str, test_suite, progress_response):
        """Execute test automation and generate reports."""
        session = self.user_sessions[user_id]
        channel_id = session['channel_id']
        
        # Get automatable tests
        automatable_tests = [tc for tc in test_suite.test_cases if tc.test_type in [TestType.WEB_UI, TestType.API]]
        
        test_results = []
        
        for i, test_case in enumerate(automatable_tests, 1):
            # Update progress
            await self.app.client.chat_update(
                channel=channel_id,
                ts=progress_response['ts'],
                text=f"🤖 Executing test {i}/{len(automatable_tests)}: {test_case.title}..."
            )
            
            try:
                # Generate automation script
                script = await self.testing_agent.generate_automation_script(test_case)
                if not script:
                    test_results.append({
                        'title': test_case.title,
                        'passed': False,
                        'message': 'Failed to generate automation script',
                        'duration': '0s',
                        'screenshot': None,
                        'video': None
                    })
                    continue
                
                # Execute automation
                start_time = datetime.now()
                success, message, screenshot, video = await self.testing_agent.execute_automation(test_case)
                end_time = datetime.now()
                duration = str(end_time - start_time)
                
                test_results.append({
                    'title': test_case.title,
                    'passed': success,
                    'message': message,
                    'duration': duration,
                    'screenshot': screenshot,
                    'video': video
                })
                
            except Exception as e:
                logger.error(f"Error executing test {test_case.title}: {e}")
                test_results.append({
                    'title': test_case.title,
                    'passed': False,
                    'message': f'Execution failed: {str(e)}',
                    'duration': '0s',
                    'screenshot': None,
                    'video': None
                })
        
        # Generate test report
        await self.app.client.chat_update(
            channel=channel_id,
            ts=progress_response['ts'],
            text="📊 Generating test report..."
        )
        
        report_path = await self.testing_agent.generate_test_report(test_results)
        
        # Calculate summary
        total_tests = len(test_results)
        passed_tests = sum(1 for result in test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Send final results
        await self.app.client.chat_update(
            channel=channel_id,
            ts=progress_response['ts'],
            text="✅ Test automation completed!",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"🎯 *Test Automation Complete!*\n\n📊 **Results Summary:**\n• Total Tests: {total_tests}\n• Passed: {passed_tests} ✅\n• Failed: {failed_tests} ❌\n• Success Rate: {success_rate:.1f}%"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📋 **Generated Files:**\n• Test Report: `{report_path}`\n• Videos and screenshots available in test results"
                    }
                }
            ]
        )
        
        # Upload files if they exist
        for result in test_results:
            if result.get('video') and os.path.exists(result['video']):
                try:
                    await self.app.client.files_upload(
                        channels=channel_id,
                        file=result['video'],
                        title=f"Video - {result['title']}",
                        initial_comment=f"🎥 Test execution video for: *{result['title']}*"
                    )
                except Exception as e:
                    logger.error(f"Error uploading video: {e}")
            
            if result.get('screenshot') and os.path.exists(result['screenshot']):
                try:
                    await self.app.client.files_upload(
                        channels=channel_id,
                        file=result['screenshot'],
                        title=f"Screenshot - {result['title']}",
                        initial_comment=f"📸 Test screenshot for: *{result['title']}*"
                    )
                except Exception as e:
                    logger.error(f"Error uploading screenshot: {e}")
    
    async def start(self):
        """Start the Slack bot."""
        await self.testing_agent.initialize()
        
        handler = AsyncSocketModeHandler(self.app, config.slack_app_token)
        await handler.start_async()
        
        logger.info("Testing Slack Bot started successfully")
    
    async def stop(self):
        """Stop the Slack bot."""
        await self.testing_agent.cleanup()
        logger.info("Testing Slack Bot stopped") 