
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
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from tasks import scan_sitemap_task, app as celery_app

# Configure logging to match the worker's format and shared log file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("debug_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Flask")

app = Flask(__name__)

@app.route('/')
def index():
    template_path = os.path.join(app.root_path, 'templates', 'index.html')
    mtime = os.path.getmtime(template_path)
    last_updated = datetime.fromtimestamp(mtime).astimezone().strftime('%B %-d, %Y %-I:%M %p %Z')
    return render_template('index.html', last_updated=last_updated)

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    data = request.json
    sitemap_url = data.get('sitemap_url')
    search_string = data.get('search_string')
    search_all = data.get('search_all', False)
    
    if not sitemap_url or not search_string:
        return jsonify({'error': 'Missing parameters'}), 400
        
    logger.info(f"Received scan request for: {sitemap_url}")
    task = scan_sitemap_task.delay(sitemap_url, search_string, search_all)
    return jsonify({'task_id': task.id}), 202

@app.route('/api/status/<task_id>')
def get_status(task_id):
    task_result = celery_app.AsyncResult(task_id)
    result = {
        "state": task_result.state,
        "status": "Processing...",
        "percent": 0
    }
    
    if task_result.state == 'PROGRESS':
        result.update(task_result.info)
    elif task_result.state == 'SUCCESS':
        result.update({
            "status": "Complete",
            "percent": 100,
            "result": task_result.result
        })
    elif task_result.state == 'FAILURE':
        result.update({
            "status": "Error",
            "error": str(task_result.info)
        })
        
    return jsonify(result)

if __name__ == '__main__':
    # use_reloader=False prevents conflicts with the VSCode debugger (debugpy).
    # To reload after changes when debugging, use the restart button in VSCode.
    # The reloader is still active when running via run.sh / run.zsh directly.
    import sys
    use_reloader = sys.gettrace() is None  # False when debugger is attached
    app.run(debug=True, port=5001, use_reloader=use_reloader)