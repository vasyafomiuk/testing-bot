# Functional Testing Agent

A comprehensive testing agent that integrates with Jira, Confluence, and Playwright to automatically generate test cases from user stories and execute automated web and API tests through a Slack bot interface.

## Features

🤖 **AI-Powered Test Generation**: Generate comprehensive test cases from Jira user stories using OpenAI GPT-4
📋 **Interactive Workflow**: Slack bot interface with approval workflow for test cases
🌐 **Web Automation**: Automated web testing using Playwright with video recording and screenshots
🔧 **API Testing**: Automated API testing capabilities
📊 **Comprehensive Reporting**: PDF reports with test results, videos, and screenshots
🔗 **Atlassian Integration**: Direct integration with Jira and Confluence via MCP

## Architecture

The system consists of several key components:

- **Testing Agent**: Core orchestrator using OpenAI SDK and agents library
- **MCP Clients**: Integration with Atlassian MCP and Playwright MCP servers
- **Slack Bot**: Interactive interface for the testing workflow
- **Automation Engine**: Executes generated test scripts with reporting

## Prerequisites

1. **Python 3.8+**
2. **OpenAI API Key**
3. **Slack App with Bot Token**
4. **Atlassian (Jira/Confluence) Access**
5. **Node.js** (for Playwright MCP)

## Installation

You can run the Testing Agent either locally or using Docker. Docker is the recommended approach for production deployments.

### Option 1: Docker Deployment (Recommended)

#### Prerequisites
- Docker and Docker Compose installed
- Git (to clone the repository)

#### Quick Start with Docker

1. **Clone and Setup**
```bash
git clone <repository-url>
cd testing-bot
```

2. **Configure Environment**
```bash
# Copy the Docker environment template
cp env.docker.example .env

# Edit .env with your configuration
nano .env  # or use your preferred editor
```

3. **Build and Start**
```bash
# Make the Docker script executable
chmod +x docker-run.sh

# Build the Docker image
./docker-run.sh build

# Start the application
./docker-run.sh start
```

4. **Monitor the Application**
```bash
# View logs
./docker-run.sh logs

# Check status
./docker-run.sh status
```

#### Production Deployment

For production environments, use the production Docker Compose configuration:

```bash
# Build and start in production mode
./docker-run.sh build --prod
./docker-run.sh start --prod

# Monitor production deployment
./docker-run.sh logs --prod
./docker-run.sh status --prod
```

The production configuration includes:
- Enhanced security settings
- Optimized resource limits
- Read-only root filesystem
- Improved logging configuration
- Health check monitoring

#### Docker Management Commands

```bash
./docker-run.sh build      # Build the Docker image
./docker-run.sh start      # Start the application
./docker-run.sh stop       # Stop the application
./docker-run.sh restart    # Restart the application
./docker-run.sh logs       # View application logs
./docker-run.sh status     # Show application status
./docker-run.sh shell      # Open shell in container
./docker-run.sh cleanup    # Remove containers and volumes
./docker-run.sh help       # Show help
```

### Option 2: Local Development Setup

#### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

#### Setup Steps

1. **Clone and Setup**
```bash
git clone <repository-url>
cd testing-bot
pip install -r requirements.txt
```

2. **Environment Configuration**
```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_APP_TOKEN=xapp-your-slack-app-token
SLACK_SIGNING_SECRET=your_slack_signing_secret

# Atlassian Configuration
JIRA_URL=https://your-company.atlassian.net
CONFLUENCE_URL=https://your-company.atlassian.net/wiki
ATLASSIAN_EMAIL=your-email@company.com
ATLASSIAN_API_TOKEN=your_atlassian_api_token

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO
```

3. **Install MCP Servers**
```bash
# Run the setup script
./setup_mcp.sh

# Or install manually:
# pip install mcp-atlassian
# npm install -g @microsoft/playwright-mcp
# npx playwright install
```

4. **Validate Setup**
```bash
python quickstart.py
```

### Slack App Setup (Required for Both Options)

Create a Slack app with the following configuration:

#### Bot Token Scopes:
- `app_mentions:read`
- `channels:history`
- `chat:write`
- `files:write`
- `users:read`

#### Event Subscriptions:
- `app_mention`
- `message.channels`

#### Socket Mode:
Enable Socket Mode and generate an App-Level Token with `connections:write` scope.

## Usage

### 1. Start the Application

#### Using Docker (Recommended)
```bash
# Start the application
./docker-run.sh start

# View logs to confirm it's running
./docker-run.sh logs
```

#### Using Local Installation
```bash
python main.py
```

### 2. Slack Bot Commands

#### Generate Test Cases
```
generate tests for PROJ-123
```

#### Get Help
```
help
```

### 3. Workflow

1. **Provide Jira User Story**: Message the bot with a Jira issue key
2. **Review Test Cases**: The bot generates and displays test cases in markdown format
3. **Approve or Regenerate**: Use buttons to approve test cases or request regeneration
4. **Choose Automation**: Select whether to automate web/API tests or keep them manual
5. **Get Results**: Receive test execution results with videos, screenshots, and reports

## Example Workflow

```
User: generate tests for STORY-456

Bot: 🔄 Generating test cases for STORY-456. This might take a moment...

Bot: ✅ Test cases generated for STORY-456

I've created 8 test cases. Please review them below:

# Test Suite for STORY-456
**User Story:** STORY-456: User Login Functionality
**Description:** Generated test cases for user story: User Login Functionality
**Created:** 2024-01-15 14:30:00

## Test Cases

### 1. Valid Login Test
**Type:** Web UI
**Priority:** High
**Description:** Test successful login with valid credentials
**Steps:**
1. Navigate to login page
2. Enter valid username and password
3. Click login button
**Expected Result:** User should be redirected to dashboard

[✅ Approve Tests] [❌ Regenerate]

User: *clicks Approve Tests*

Bot: 🎯 Test cases approved!
I found 6 automatable tests and 2 manual tests.
Would you like me to automate the web and API tests?

[🤖 Automate Tests] [📋 Manual Only]

User: *clicks Automate Tests*

Bot: 🤖 Starting test automation. This may take several minutes...
Bot: 🤖 Executing test 1/6: Valid Login Test...
Bot: 🤖 Executing test 2/6: Invalid Password Test...
...
Bot: 📊 Generating test report...

Bot: 🎯 Test Automation Complete!
📊 Results Summary:
• Total Tests: 6
• Passed: 5 ✅
• Failed: 1 ❌  
• Success Rate: 83.3%

📋 Generated Files:
• Test Report: ./reports/test_report_20240115_143000.md
• Videos and screenshots available in test results

*Bot uploads video files and screenshots*
```

## Project Structure

```
testing-bot/
├── agents/
│   ├── __init__.py
│   └── testing_agent.py          # Main testing agent
├── mcp_clients/
│   ├── __init__.py
│   ├── atlassian_client.py        # Atlassian MCP client
│   └── playwright_client.py       # Playwright MCP client
├── slack_bot/
│   ├── __init__.py
│   └── bot.py                     # Slack bot implementation
├── utils/
│   ├── __init__.py
│   └── logging_config.py          # Logging configuration
├── config.py                      # Configuration management
├── main.py                        # Application entry point
├── requirements.txt               # Python dependencies
├── env.example                    # Environment template (local)
├── env.docker.example             # Environment template (Docker)
├── Dockerfile                     # Docker image configuration
├── docker-compose.yml             # Docker Compose configuration (development)
├── docker-compose.prod.yml        # Docker Compose configuration (production)
├── .dockerignore                  # Docker build exclusions
├── docker-run.sh                  # Docker management script
├── setup_mcp.sh                   # MCP servers setup script
├── quickstart.py                  # Setup validation script
└── README.md                      # This file
```

## Configuration Options

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for test generation | Yes |
| `SLACK_BOT_TOKEN` | Slack bot token | Yes |
| `SLACK_APP_TOKEN` | Slack app-level token | Yes |
| `SLACK_SIGNING_SECRET` | Slack signing secret | Yes |
| `JIRA_URL` | Jira instance URL | Yes |
| `CONFLUENCE_URL` | Confluence instance URL | Yes |
| `ATLASSIAN_EMAIL` | Atlassian account email | Yes |
| `ATLASSIAN_API_TOKEN` | Atlassian API token | Yes |
| `DEBUG` | Enable debug mode | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | No |

### Test Types

The agent supports three types of tests:

1. **Web UI Tests**: Automated using Playwright with browser automation
2. **API Tests**: Automated using HTTP requests and response validation
3. **Manual Tests**: Cannot be automated and require manual execution

## Troubleshooting

### Common Issues

1. **MCP Connection Errors**
   - Ensure Atlassian MCP and Playwright MCP are installed
   - Check your Atlassian credentials and permissions
   - Verify Jira/Confluence URLs are correct

2. **Slack Bot Not Responding**
   - Check Slack app configuration and permissions
   - Verify Socket Mode is enabled
   - Ensure the bot is added to the channel

3. **Test Generation Fails**
   - Verify OpenAI API key is valid
   - Check Jira issue exists and is accessible
   - Ensure sufficient OpenAI API credits

4. **Automation Failures**
   - Check browser dependencies for Playwright
   - Verify network connectivity to test targets
   - Review generated automation scripts for errors

### Docker-Specific Issues

1. **Container Won't Start**
   ```bash
   # Check container logs
   ./docker-run.sh logs
   
   # Check container status
   ./docker-run.sh status
   
   # Rebuild the image
   ./docker-run.sh cleanup
   ./docker-run.sh build
   ```

2. **Permission Errors**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ./data
   chmod -R 755 ./data
   ```

3. **Out of Memory Errors**
   - Increase memory limits in `docker-compose.yml`
   - Check Docker Desktop memory allocation
   ```yaml
   deploy:
     resources:
       limits:
         memory: 4G  # Increase from 2G
   ```

4. **Port Conflicts**
   - Change exposed ports in `docker-compose.yml` if needed
   - Check if ports are already in use: `netstat -tulpn`

5. **Environment Variables Not Loading**
   ```bash
   # Verify .env file exists and has correct format
   cat .env
   
   # Check container environment
   ./docker-run.sh shell
   env | grep -E "(OPENAI|SLACK|JIRA)"
   ```

### Logs and Debugging

#### Local Development
Enable debug logging by setting:
```bash
LOG_LEVEL=DEBUG
DEBUG=true
```

#### Docker Environment
```bash
# View real-time logs
./docker-run.sh logs

# View logs with timestamps
docker-compose logs -t testing-agent

# View last 100 lines
docker-compose logs --tail=100 testing-agent

# Enable debug logging
# Set LOG_LEVEL=DEBUG in your .env file and restart
./docker-run.sh restart
```

Logs will show detailed information about:
- MCP client connections
- Test case generation process
- Automation execution steps
- Slack bot interactions
- Docker container health status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue on the repository 