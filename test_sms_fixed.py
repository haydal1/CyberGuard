#!/usr/bin/env python3
import re

def test_sms_improved(message):
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
    
    # Check patterns with proper regex
    for pattern in high_risk_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            score += 8
            reasons.append(f"High-risk: '{pattern}'")
    
    for pattern in medium_risk_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            score += 4
            reasons.append(f"Medium-risk: '{pattern}'")
    
    # Check individual keywords
    scam_keywords = ["bvn", "pin", "password", "winner", "won", "prize", "urgent", "verification"]
    for keyword in scam_keywords:
        if keyword in normalized:
            score += 3
            reasons.append(f"Keyword: '{keyword}'")
    
    # Check URLs
    if re.search(r'http://|https://|www\.|bit\.ly|tinyurl|click.*here', normalized, re.IGNORECASE):
        score += 6
        reasons.append("Suspicious URL")
    
    # Check phone requests
    if re.search(r'call.*\d|phone.*number|contact.*us|dial.*\d|send.*number', normalized, re.IGNORECASE):
        score += 5
        reasons.append("Phone request")
    
    # Check money mentions
    if re.search(r'\$\d|\d+\s*(dollar|naira|usd)|million|cash|money', normalized, re.IGNORECASE):
        score += 3
        reasons.append("Money mention")
    
    # Determine result
    if score >= 15:
        return f"🚨 HIGH-RISK SCAM (Score: {score}) - {', '.join(reasons)}"
    elif score >= 10:
        return f"⚠️ SUSPICIOUS (Score: {score}) - {', '.join(reasons)}"
    elif score >= 5:
        return f"⚠️ POTENTIALLY RISKY (Score: {score}) - {', '.join(reasons)}"
    else:
        return f"✅ LIKELY LEGITIMATE (Score: {score})"

# Test the problematic messages
test_messages = [
    "congratulation you won a prize!",
    "congratulations",
    "click to submit your bvn",
    "send me your account pin number",
    "Congratulations! You won $1,000,000 lottery!",
    "Your account needs verification. Send your BVN",
    "Click here to claim your free gift: http://bit.ly/scam"
]

print("🧪 TESTING IMPROVED SMS DETECTION:")
print("=" * 50)
for msg in test_messages:
    result = test_sms_improved(msg)
    print(f"'{msg}'")
    print(f"  -> {result}")
    print()
