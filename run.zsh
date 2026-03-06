#!/bin/zsh

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


# Activate virtual environment
source .venv/bin/activate

# logger helper — pipes stdin to syslog with a tag
log() { sed "s/^/[$1] /" | logger -t "link-scanner"; }

# Trap Ctrl+C and kill all background processes
cleanup() {
    echo ""
    echo "Shutting down..."
    echo "Shutting down all services." | log "main"
    kill $REDIS_PID $CELERY_PID $FLASK_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Start Redis
echo "Starting Redis..."
echo "Starting Redis" | log "main"
redis-server --daemonize no 2>&1 | log "redis" &
REDIS_PID=$!
sleep 1

# Start Celery worker
echo "Starting Celery worker..."
echo "Starting Celery worker" | log "main"
celery -A tasks worker --loglevel=info 2>&1 | log "celery" &
CELERY_PID=$!
sleep 1

# Start Flask
echo "Starting Flask on http://localhost:5001"
echo "Starting Flask on http://localhost:5001" | log "main"
python app.py 2>&1 | log "flask" &
FLASK_PID=$!

echo ""
echo "All services running. Logs going to syslog. Press Ctrl+C to stop."
echo "  tail with: log stream --predicate 'senderImagePath contains \"logger\"' --info"

wait
