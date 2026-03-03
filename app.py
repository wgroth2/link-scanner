from flask import Flask, render_template, request, jsonify
from tasks import scan_sitemap_task

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/scan', methods=['POST'])
def start_scan():
    data = request.get_json()
    sitemap_url = data.get('sitemap_url')
    search_string = data.get('search_string')
    search_all = data.get('search_all', False)

    if not sitemap_url or not search_string:
        return jsonify({'error': 'Missing required fields'}), 400

    # Trigger the Celery task asynchronously
    task = scan_sitemap_task.delay(sitemap_url, search_string, search_all)
    
    return jsonify({'task_id': task.id}), 202

@app.route('/api/status/<task_id>')
def task_status(task_id):
    # Retrieve the task result object using the ID
    task = scan_sitemap_task.AsyncResult(task_id)
    
    response = {
        'state': task.state,
    }

    if task.state == 'PENDING':
        # Job is waiting in the queue
        response.update({
            'current': 0,
            'total': 1,
            'status': 'Pending...',
            'percent': 0
        })
    elif task.state == 'PROGRESS':
        # Job is running, return metadata set by self.update_state() in tasks.py
        response.update({
            'current': task.info.get('current', 0),
            'total': task.info.get('total', 1),
            'status': task.info.get('status', ''),
            'percent': task.info.get('percent', 0)
        })
    elif task.state == 'SUCCESS':
        # Job finished successfully
        response.update({
            'status': 'Scan Complete!',
            'percent': 100,
            'result': task.result  # This contains the dict returned by the task
        })
    else:
        # FAILURE, REVOKED, etc.
        response.update({
            'status': 'Error occurred',
            'error': str(task.info)
        })

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True, port=5000)