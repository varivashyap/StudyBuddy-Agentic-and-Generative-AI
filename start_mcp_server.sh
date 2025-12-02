#!/bin/bash
cd "$(dirname "$0")"
source aivenv/bin/activate
python -m mcp_server.server --host 0.0.0.0 --port 5000
