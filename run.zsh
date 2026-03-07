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

# Check for already-running services
ABORT=0
if lsof -i :6379 -sTCP:LISTEN -t &>/dev/null; then
    echo "ERROR: Redis is already running on port 6379."
    ABORT=1
fi
if lsof -i :5001 -sTCP:LISTEN -t &>/dev/null; then
    echo "ERROR: Something is already running on port 5001 (Flask)."
    ABORT=1
fi
if pgrep -f "celery worker" &>/dev/null; then
    echo "ERROR: A Celery worker is already running."
    ABORT=1
fi
if lsof -i :5555 -sTCP:LISTEN -t &>/dev/null; then
    echo "ERROR: Something is already running on port 5555 (Flower)."
    ABORT=1
fi
if [ $ABORT -eq 1 ]; then
    echo "Stopping. Please kill the above processes before starting."
    exit 1
fi

# logger helper — pipes stdin to syslog with a tag
log() { sed "s/^/[$1] /" | logger -t "link-scanner"; }

# Trap Ctrl+C and kill all background processes
cleanup() {
    echo ""
    echo "Shutting down..."
    echo "Shutting down all services." | log "main"
    kill $REDIS_PID $CELERY_PID $FLOWER_PID $FLASK_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

# Start Redis
echo "Starting Redis..."
echo "Starting Redis" | log "main"
redis-server --daemonize no &
REDIS_PID=$!
{ while kill -0 $REDIS_PID 2>/dev/null; do read line && echo "$line" | log "redis"; done; } &
sleep 1

# Start Celery worker
echo "Starting Celery worker..."
echo "Starting Celery worker" | log "main"
celery -A tasks worker --loglevel=info --concurrency=2 &
CELERY_PID=$!
{ while kill -0 $CELERY_PID 2>/dev/null; do read line && echo "$line" | log "celery"; done; } &
sleep 1

# Start Flower
echo "Starting Flower on http://localhost:5555"
echo "Starting Flower on http://localhost:5555" | log "main"
celery -A tasks flower --port=5555 &
FLOWER_PID=$!
{ while kill -0 $FLOWER_PID 2>/dev/null; do read line && echo "$line" | log "flower"; done; } &
sleep 1

# Start Flask
echo "Starting Flask on http://localhost:5001"
echo "Starting Flask on http://localhost:5001" | log "main"
python app.py &
FLASK_PID=$!
{ while kill -0 $FLASK_PID 2>/dev/null; do read line && echo "$line" | log "flask"; done; } &

echo ""
echo "All services running. Logs going to syslog. Press Ctrl+C to stop."
echo "  tail with: log stream --predicate 'senderImagePath contains \"logger\"' --info"

wait
