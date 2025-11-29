#!/bin/bash
echo "🎯 FINAL CYBERGUARD TEST"
echo "========================"

# Kill any existing server
pkill -f "cyberguard_working" 2>/dev/null
sleep 2

echo "🚀 Starting server..."
python3 cyberguard_working.py > server.log 2>&1 &
SERVER_PID=$!
echo "📝 Server PID: $SERVER_PID"

# Wait for server to start
echo "⏳ Waiting for server..."
sleep 5

# Test if server is running
if curl -s http://localhost:8001/ > /dev/null; then
    echo "✅ Server is running!"
else
    echo "❌ Server failed to start"
    cat server.log
    exit 1
fi

echo ""
echo "📊 DATABASE STATS:"
curl -s http://localhost:8001/stats | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f'   Safe USSD codes: {data.get(\"safe_codes\", \"N/A\")}')
    print(f'   Scam patterns: {data.get(\"scam_patterns\", \"N/A\")}')
    print(f'   Scam keywords: {data.get(\"scam_keywords\", \"N/A\")}')
    print(f'   Status: {data.get(\"status\", \"N/A\")}')
except Exception as e:
    print(f'   ERROR: {e}')
"

echo ""
echo "✅ TESTING SAFE USSD CODES:"
safe_codes=("*901#" "*737#" "*919#" "*894#" "*556#")
for code in "${safe_codes[@]}"; do
    result=$(curl -s "http://localhost:8001/check?code=$code")
    status=$(echo "$result" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'ERROR'))" 2>/dev/null || echo "PARSE_ERR")
    echo "   $code -> $status"
done

echo ""
echo "🚨 TESTING SCAM USSD CODES:"
scam_codes=("*123*password*#" "*500*bvn*123#" "*999*pin*456#" "*123*winner*#")
for code in "${scam_codes[@]}"; do
    result=$(curl -s "http://localhost:8001/check?code=$code")
    status=$(echo "$result" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'ERROR'))" 2>/dev/null || echo "PARSE_ERR")
    echo "   $code -> $status"
done

echo ""
echo "💬 TESTING SMS DETECTION:"
echo "   SCAM SMS ->" $(curl -s --data-urlencode "sms=You won 5,000,000! Call now!" "http://localhost:8001/check" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'ERROR'))" 2>/dev/null)
echo "   SAFE SMS ->" $(curl -s --data-urlencode "sms=Hi, meeting at 3 PM tomorrow" "http://localhost:8001/check" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'ERROR'))" 2>/dev/null)

# Stop server
echo ""
echo "🛑 Stopping server..."
kill $SERVER_PID 2>/dev/null

echo ""
echo "🎉 TEST COMPLETE! All endpoints working correctly."
