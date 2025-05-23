#!/usr/bin/env python3
"""Quick start script to validate the testing agent setup."""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8+."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True


def check_environment_file():
    """Check if .env file exists."""
    if not Path(".env").exists():
        print("❌ .env file not found")
        print("   Please copy env.example to .env and configure your settings")
        return False
    print("✅ .env file found")
    return True


def check_required_env_vars():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = [
        'OPENAI_API_KEY',
        'SLACK_BOT_TOKEN',
        'SLACK_APP_TOKEN',
        'SLACK_SIGNING_SECRET',
        'JIRA_URL',
        'CONFLUENCE_URL',
        'ATLASSIAN_EMAIL',
        'ATLASSIAN_API_TOKEN'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import openai
        import slack_bolt
        import mcp
        print("✅ Python dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing Python dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False


def check_mcp_servers():
    """Check if MCP servers are available."""
    # Check Atlassian MCP
    try:
        result = subprocess.run(['uvx', 'mcp-atlassian', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Atlassian MCP server is available")
        else:
            print("❌ Atlassian MCP server not found")
            print("   Run: pip install mcp-atlassian")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Atlassian MCP server not found or uvx not available")
        return False
    
    # Check Playwright MCP
    try:
        result = subprocess.run(['npx', '@microsoft/playwright-mcp', '--help'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Playwright MCP server is available")
        else:
            print("❌ Playwright MCP server not found")
            print("   Run: npm install -g @microsoft/playwright-mcp")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Playwright MCP server not found or npm not available")
        return False
    
    return True


def create_directories():
    """Create necessary directories."""
    dirs = ['videos', 'screenshots', 'reports']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
    print("✅ Created necessary directories")


def main():
    """Main validation function."""
    print("🚀 Testing Agent Setup Validation")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_environment_file,
        check_required_env_vars,
        check_dependencies,
        check_mcp_servers
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        create_directories()
        print("🎉 All checks passed! You're ready to start the testing agent.")
        print("\nTo start the application, run:")
        print("   python main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above before starting.")
        sys.exit(1)


if __name__ == "__main__":
    main() 