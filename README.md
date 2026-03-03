README.md

# Readme for Website String Search

## Installation: MacOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install & Start Redis**:
   Redis is required for the Celery task queue.
   ```bash
   brew install redis
   brew services start redis
   ```

3. **Install Python Dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install flask celery[redis] requests beautifulsoup4 lxml
   ```

## Installation: Ubuntu

1. **Update Package List and Install Redis**:
   ```bash
   sudo apt update
   sudo apt install redis-server python3-pip python3-venv
   sudo systemctl enable --now redis-server
   ```

2. **Setup Python Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activatere
   pip install flask celery[redis] requests beautifulsoup4 lxml
   ```

## Setup

To run the application, you need to start three separate components:

1. **Redis Server**: Ensure Redis is running. You can start it manually via the command line:
   ```bash
   redis-server
   ```

2. **Celery Worker**:
   In a new terminal, activate the environment and start the worker:
   ```bash
   source venv/bin/activate
   celery -A tasks worker --loglevel=info
   ```
3. **Flask App**:
   In another terminal, activate the environment and start the web server:
   ```bash
   source venv/bin/activate
   python3 app.py
   ```

## Stopping the Application

1. **Stop Flask & Celery**:
   Simply press `Ctrl+C` in the terminal windows where they are running.

2. **Stop Redis**:
   *   If started via Homebrew Services:
       ```bash
       brew services stop redis
       ```
   *   If started directly (`redis-server`):
       *   Foreground: Press `Ctrl+C`.
       *   Background:
           ```bash
           redis-cli shutdown
           ```

## Notes
