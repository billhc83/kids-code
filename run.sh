#!/bin/bash
# Kill anything on port 5001
fuser -k 5001/tcp 2>/dev/null
# Start Flask
python app.py