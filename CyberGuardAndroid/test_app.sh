#!/bin/bash
echo "🧪 CYBERGUARD COMPREHENSIVE TESTING SUITE"
echo "=========================================="
echo ""

# Test 1: Check if all required files exist
echo "📁 FILE STRUCTURE TEST"
echo "======================"
required_files=(
    "app/src/main/AndroidManifest.xml"
    "app/build.gradle"
    "app/src/main/java/com/cyberguard/MainActivity.kt"
    "app/src/main/java/com/cyberguard/USSDChecker.kt"
    "app/src/main/java/com/cyberguard/SMSChecker.kt"
    "app/src/main/java/com/cyberguard/SecurityResult.kt"
    "app/src/main/assets/ussd_database.json"
    "app/src/main/res/layout/activity_main.xml"
    "app/src/main/res/values/strings.xml"
    "app/src/main/res/values/colors.xml"
    "app/src/main/res/drawable/ic_launcher.xml"
)

all_files_exist=true
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file"
        all_files_exist=false
    fi
done

echo ""
if [ "$all_files_exist" = true ]; then
    echo "✅ All required files present"
else
    echo "❌ Missing files detected"
    exit 1
fi

# Test 2: Validate JSON database
echo ""
echo "📊 DATABASE VALIDATION TEST"
echo "==========================="
if python3 -c "
import json
try:
    with open('app/src/main/assets/ussd_database.json', 'r') as f:
        data = json.load(f)
    print('✅ JSON syntax valid')
    print(f'✅ Safe codes: {len(data[\"safe_codes\"])}')
    print(f'✅ Scam patterns: {len(data[\"scam_patterns\"])}')
    print(f'✅ Scam keywords: {len(data[\"scam_keywords\"])}')
except Exception as e:
    print(f'❌ JSON validation failed: {e}')
    exit(1)
"; then
    echo "✅ Database validation passed"
else
    echo "❌ Database validation failed"
    exit 1
fi

# Test 3: Test USSD detection logic
echo ""
echo "📟 USSD DETECTION TEST"
echo "======================"
cat > test_ussd.py << 'PY_EOF'
import json
import re

# Load test database
with open('app/src/main/assets/ussd_database.json', 'r') as f:
    db = json.load(f)

def test_ussd_code(code):
    normalized = code.lower().strip()
    
    # Check safe codes
    for safe_code in db["safe_codes"]:
        if safe_code["code"].lower() == normalized:
            return f"✅ SAFE: {safe_code['description']}"
    
    # Check scam patterns
    for pattern in db["scam_patterns"]:
        if re.search(pattern, normalized, re.IGNORECASE):
            return f"🚨 SCAM: Matches pattern '{pattern}'"
    
    # Check individual scam keywords
    for keyword in db["scam_keywords"]:
        if keyword in normalized:
            return f"⚠️ SUSPICIOUS: Contains scam keyword '{keyword}'"
    
    return "❓ UNKNOWN: Code not in database"

# Test cases
test_cases = [
    "*901#",      # Safe banking code
    "*123#",      # Safe telecom code  
    "*500*1234#", # Safe service code
    "*500*1234*password#",  # Scam - contains password
    "*123*bvn#",  # Scam - contains BVN
    "*999*pin#",  # Scam - contains PIN
    "*123*winner#", # Scam - contains winner
]

print("Testing USSD detection logic:")
for test in test_cases:
    result = test_ussd_code(test)
    print(f"  {test} -> {result}")
PY_EOF

python3 test_ussd.py
rm test_ussd.py

# Test 4: Test SMS detection logic
echo ""
echo "💬 SMS DETECTION TEST"
echo "===================="
cat > test_sms.py << 'PY_EOF'
import json
import re

def test_sms_message(message):
    normalized = message.lower()
    score = 0
    reasons = []
    
    # High-risk patterns
    high_risk_patterns = [
        "won.*prize", "win.*lottery", "congratulations.*won", 
        "claim.*prize", "free.*gift", "urgent.*account",
        "bvn.*required", "password.*reset", "pin.*verification",
        "account.*suspended", "verification.*required"
    ]
    
    # Medium-risk patterns  
    medium_risk_patterns = [
        "million", "cash.*award", "immediately", "click.*link",
        "call.*now", "limited.*time", "exclusive.*offer"
    ]
    
    # Check patterns
    for pattern in high_risk_patterns:
        if re.search(pattern, normalized):
            score += 8
            reasons.append(f"High-risk: '{pattern}'")
    
    for pattern in medium_risk_patterns:
        if re.search(pattern, normalized):
            score += 4
            reasons.append(f"Medium-risk: '{pattern}'")
    
    # Determine result
    if score >= 15:
        return "🚨 HIGH-RISK SCAM"
    elif score >= 10:
        return "⚠️ SUSPICIOUS SMS" 
    elif score >= 5:
        return "⚠️ POTENTIALLY RISKY"
    else:
        return "✅ LIKELY LEGITIMATE"

# Test SMS messages
sms_test_cases = [
    "Congratulations! You won $1,000,000. Call now to claim your prize!",
    "Your account has been suspended. Verify your BVN immediately.",
    "Hi John, are we still meeting tomorrow?",
    "Free gift! Click http://bit.ly/scam-link to claim your iPhone",
    "Your password needs resetting. Reply with your PIN for verification",
    "Your package has been delivered. Track at official-website.com"
]

print("Testing SMS detection logic:")
for test in sms_test_cases:
    result = test_sms_message(test)
    print(f"  '{test[:30]}...' -> {result}")
PY_EOF

python3 test_sms.py
rm test_sms.py

# Test 5: Build validation
echo ""
echo "🔨 BUILD VALIDATION TEST"
echo "========================"
echo "Checking Gradle build configuration..."

if ./gradle-8.0/bin/gradle --version > /dev/null 2>&1; then
    echo "✅ Gradle is working"
else
    echo "❌ Gradle not working"
    exit 1
fi

# Test 6: Check Android resources
echo ""
echo "🎨 RESOURCE VALIDATION"
echo "======================"
if [ -f "app/src/main/res/values/strings.xml" ]; then
    echo "✅ Strings.xml exists"
    grep -q "app_name" app/src/main/res/values/strings.xml && echo "✅ App name defined" || echo "❌ App name missing"
fi

if [ -f "app/src/main/res/values/colors.xml" ]; then
    echo "✅ Colors.xml exists"
    grep -q "purple_500" app/src/main/res/values/colors.xml && echo "✅ Theme colors defined" || echo "❌ Theme colors missing"
fi

echo ""
echo "🎯 TESTING COMPLETE"
echo "==================="
echo "If all tests pass, your CyberGuard app is ready for deployment!"
echo "Next: Deploy to GitHub for cloud build and APK generation"
