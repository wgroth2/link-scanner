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
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
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
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

## Setup

Use the provided run script to start all three components (Redis, Celery worker, Flask) in one command:

```bash
./run.sh
```

All output is sent to syslog under the tag `link-scanner`. To tail logs:

```bash
# macOS
log stream --predicate 'senderImagePath contains "logger"' --info | grep "link-scanner"

# Ubuntu
journalctl -f -t "link-scanner"
```

## Stopping the Application

Press `Ctrl+C` in the terminal running `run.sh`. This will cleanly shut down all three processes.

## Manual Setup (Alternative)

If you prefer to run each component separately:

1. **Redis Server**:
   ```bash
   redis-server
   ```

2. **Celery Worker**:
   ```bash
   source .venv/bin/activate
   celery -A tasks worker --loglevel=info
   ```

3. **Flask App**:
   ```bash
   source .venv/bin/activate
   python3 app.py
   ```

## Command Line Usage (scanner.py)

`scanner.py` can be run directly from the command line to scan a sitemap for a search string.

```
python3 scanner.py <sitemap_url> <search_string> [options]
```
### Comment about search strings

<Search_string> can be a regular expression.
### Positional Arguments

| Argument | Description |
|---|---|
| `sitemap_url` | The URL of the sitemap to scan (e.g. `https://example.com/sitemap.xml`) |
| `search_string` | The string (or regex) to search for |

### Options

| Flag | Description |
|---|---|
| `-s`, `--silent` | Suppress "skip" messages for 4xx HTTP errors |
| `-a`, `--all` | Search the entire HTML source text instead of only `<a href>` attributes |
| `-t`, `--timeout <seconds>` | Request timeout in seconds (default: 10) |
| `-d`, `--debug` | Enable debug logging to stdout |
| `-u`, `--url` | Print each URL as it is being scanned |

### Output

Results are written to stdout as CSV with columns: `Index`, `URL`, `Found Text`.

### Examples

Search all page links for `mailto:`:
```bash
python3 scanner.py https://example.com/sitemap.xml "mailto:"
```

Search full HTML source for a phone number pattern, with debug output:
```bash
python3 scanner.py https://example.com/sitemap.xml "\d{3}-\d{4}" --all --debug
```

Redirect results to a file:
```bash
python3 scanner.py https://example.com/sitemap.xml "contact" -s > results.csv
```

## Notes

---

## License

Copyright 2026 Bill Roth

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
