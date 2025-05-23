#!/bin/bash

echo "🚀 Setting up MCP servers for Testing Agent..."

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install Python and pip first."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install Node.js first."
    exit 1
fi

echo "📦 Installing Atlassian MCP server..."
pip install mcp-atlassian

if [ $? -eq 0 ]; then
    echo "✅ Atlassian MCP server installed successfully"
else
    echo "❌ Failed to install Atlassian MCP server"
    exit 1
fi

echo "📦 Installing Playwright MCP server..."
npm install -g @microsoft/playwright-mcp

if [ $? -eq 0 ]; then
    echo "✅ Playwright MCP server installed successfully"
else
    echo "❌ Failed to install Playwright MCP server"
    exit 1
fi

echo "📦 Installing Playwright browsers..."
npx playwright install

if [ $? -eq 0 ]; then
    echo "✅ Playwright browsers installed successfully"
else
    echo "❌ Failed to install Playwright browsers"
    exit 1
fi

echo "🎉 MCP servers setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Copy env.example to .env and configure your settings"
echo "2. Set up your Slack app with the required permissions"
echo "3. Run 'python main.py' to start the testing agent" 