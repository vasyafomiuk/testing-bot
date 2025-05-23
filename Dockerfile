# Use official Python image with Node.js
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    NODE_VERSION=18

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libxss1 \
    libgconf-2-4 \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# Install uvx (modern uv-based tool runner)
RUN pip install --no-cache-dir uv uvx

# Create app directory and user
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP servers
RUN pip install --no-cache-dir mcp-atlassian
RUN npm install -g @microsoft/playwright-mcp

# Install Playwright browsers
RUN npx playwright install chromium firefox webkit
RUN npx playwright install-deps

# Copy application code
COPY --chown=app:app . .

# Create necessary directories
RUN mkdir -p videos screenshots reports logs \
    && chown -R app:app /home/app

# Switch to non-root user
USER app

# Create volume mount points
VOLUME ["/home/app/videos", "/home/app/screenshots", "/home/app/reports", "/home/app/logs"]

# Expose port (if needed for health checks)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entry point
ENTRYPOINT ["python", "main.py"] 