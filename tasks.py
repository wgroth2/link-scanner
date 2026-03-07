# Copyright 2026 Bill Roth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import logging
from celery import Celery
# Import the logic from your existing scanner.py.
# This keeps the core logic separate from the task queue implementation.
from scanner import get_sitemap_urls, find_contact_links

# Configure logging to a shared file for debugging
# This ensures logs from the worker process are captured in the same file as the Flask app.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("debug_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Worker")

# Initialize Celery
# This sets up the connection to the Redis message broker.
# 'broker': Where tasks are sent (Redis).
# 'backend': Where results are stored (Redis).
app = Celery('scanner_worker',
             broker=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
             backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'))

@app.task(bind=True)
def scan_sitemap_task(self, sitemap_url, search_string, search_all=False):
    """
    Celery task to scan a sitemap for a specific string.
    Returns a dictionary containing the results.
    """
    # 1. Update state: Starting (SENDING DATA TO REDIS)
    # self.update_state() sends a message to Redis so the frontend can poll the status.
    logger.info(f"Starting task for sitemap: {sitemap_url}")
    self.update_state(state='PROGRESS', meta={'status': 'Fetching sitemap...', 'current': 0, 'total': 0})
    
    # Reuse the logic from scanner.py to get the list of URLs
    # Note: This function prints to stdout, which will appear in your worker logs.
    urls = get_sitemap_urls(sitemap_url)
    if urls is None:
        logger.error(f"Task failed: {sitemap_url} is not a valid sitemap.")
        raise ValueError(f"Could not fetch sitemap: {sitemap_url}. Check the URL and try again.")

    total = len(urls)
    results = []
    timed_out = []

    # 2. Iterate and Scan
    for i, url in enumerate(urls):
        # Update progress state every 5 iterations to reduce overhead
        # (SENDING DATA TO REDIS) - Updates the 'meta' dictionary in Redis with current progress.
        if i % 5 == 0:
            self.update_state(state='PROGRESS', meta={
                'current': i,
                'total': total,
                'status': f'Scanning {i}/{total} URLs...',
                'percent': int((i / total) * 100) if total > 0 else 0
            })

        # Run the check using the existing function
        # silent=True prevents printing "Skip" messages to the worker logs
        # Returns None on timeout, False if not found, True if found
        result = find_contact_links(url, search_string, silent=True, search_all=search_all)
        if result is None:
            timed_out.append(url)
        elif result:
            results.append(url)

    # 3. Return Results
    # The return value is serialized and stored in Redis as the task result.
    logger.info(f"Task complete. Found {len(results)} matches. {len(timed_out)} timeouts.")
    return {
        'total_scanned': total,
        'matches_found': len(results),
        'urls': results,
        'timed_out': timed_out
    }