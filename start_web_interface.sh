#!/bin/bash
echo "🚀 Starting CyberGuard Web Interface..."
echo "======================================"

# Kill any existing processes
pkill -f "python.*8001" 2>/dev/null
sleep 2

# Check if port is available
if netstat -tulpn 2>/dev/null | grep -q ":8001 "; then
    echo "❌ Port 8001 is already in use"
    echo "   Please run: pkill -f 'python.*8001'"
    exit 1
fi

# Start the server
echo "📍 Starting server on http://localhost:8001"
echo "📱 Open this URL in your browser"
echo "🛑 Press Ctrl+C to stop the server"
echo ""

python3 cyberguard_web_fixed.py
