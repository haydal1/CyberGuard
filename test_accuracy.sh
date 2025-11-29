#!/bin/bash
echo "🧪 TESTING USSD DETECTION ACCURACY:"
echo "==================================="

# Test safe codes
safe_codes=("*901#" "*902#" "*123#" "*310#" "*606#")
echo "✅ Testing SAFE codes:"
for code in "${safe_codes[@]}"; do
    result=$(curl -s "http://localhost:8001/check?code=$code")
    message=$(echo "$result" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['message'])")
    echo "  $code -> $message"
done

echo ""
echo "🚨 Testing SCAM codes:"
# Test scam codes
scam_codes=("*123*password*#" "*500*bvn*123#" "*999*pin*456#" "*123*winner*#" "*456*verification*#")
for code in "${scam_codes[@]}"; do
    result=$(curl -s "http://localhost:8001/check?code=$code")
    message=$(echo "$result" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['message'])")
    echo "  $code -> $message"
done

echo ""
echo "💬 TESTING SMS DETECTION ACCURACY:"
echo "=================================="

# Test scam SMS messages
echo "🚨 Testing SCAM SMS:"
scam_sms=(
    "Congratulations! You won $1,000,000 lottery! Call now to claim."
    "Your account has been suspended. Verify your BVN immediately."
    "Free iPhone! Click http://bit.ly/free-iphone to claim now!"
    "Your password needs resetting. Reply with your PIN for verification."
    "You won a cash prize! Send your account details to claim."
)

for sms in "${scam_sms[@]}"; do
    encoded_sms=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sms'))")
    result=$(curl -s "http://localhost:8001/check?sms=$encoded_sms")
    message=$(echo "$result" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['message'].split(chr(10))[0])")
    echo "  ${sms:0:40}... -> $message"
done

echo ""
echo "✅ Testing LEGITIMATE SMS:"
legit_sms=(
    "Hi John, are we still meeting tomorrow at 3 PM?"
    "Your package has been delivered. Tracking number: 123456"
    "Your Uber is arriving in 5 minutes. Driver: Mike"
    "Your bank statement for January is ready for download"
    "Reminder: Dentist appointment tomorrow at 10 AM"
)

for sms in "${legit_sms[@]}"; do
    encoded_sms=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$sms'))")
    result=$(curl -s "http://localhost:8001/check?sms=$encoded_sms")
    message=$(echo "$result" | python3 -c "import json, sys; data = json.load(sys.stdin); print(data['message'].split(chr(10))[0])")
    echo "  ${sms:0:40}... -> $message"
done
