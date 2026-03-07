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

# Debug run script — starts Redis and Celery only.
# Launch app.py separately via the VSCode debugger.

source .venv/bin/activate

# Check for already-running services
ABORT=0
if lsof -i :6379 -sTCP:LISTEN -t &>/dev/null; then
    echo "ERROR: Redis is already running on port 6379."
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

cleanup() {
    echo ""
    echo "Shutting down Redis and Celery..."
    kill $REDIS_PID $CELERY_PID $FLOWER_PID 2>/dev/null
    exit 0
}
trap cleanup INT TERM

echo "Starting Redis..."
redis-server --daemonize no &
REDIS_PID=$!
sleep 1

echo "Starting Celery worker..."
celery -A tasks worker --loglevel=info --concurrency=2 &
CELERY_PID=$!

echo "Starting Flower on http://localhost:5555"
celery -A tasks flower --port=5555 &
FLOWER_PID=$!

echo ""
echo "Redis, Celery, and Flower running. Start app.py in the VSCode debugger."
echo "  Flower admin: http://localhost:5555"
echo "Press Ctrl+C to stop."
wait
