#!/usr/bin/env python3
"""
Test Automatic SMS Detection Simulation
This simulates how the Android app would detect scams automatically
"""
import json
import re
import os

class AutoSMSDetector:
    def __init__(self):
        self.database = self.load_database()
        self.scam_messages_detected = 0
        self.legitimate_messages_passed = 0
    
    def load_database(self):
        """Load the USSD database"""
        try:
            database_path = 'CyberGuardAndroid/app/src/main/assets/ussd_database.json'
            if os.path.exists(database_path):
                with open(database_path, 'r') as f:
                    return json.load(f)
            return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
        except Exception as e:
            print(f"❌ Failed to load database: {e}")
            return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
    
    def simulate_incoming_sms(self, message, sender="Unknown"):
        """Simulate automatic SMS detection like the Android app"""
        print(f"📱 INCOMING SMS from {sender}:")
        print(f"   '{message}'")
        
        result = self.check_sms_message(message)
        
        # Simulate automatic alert for high-risk scams
        if not result['safe'] and result['confidence'] >= 75:
            print(f"🚨 AUTOMATIC ALERT: {result['message'].split(chr(10))[0]}")
            print("   ⚠️ User would receive notification immediately!")
            self.scam_messages_detected += 1
        elif result['safe']:
            print(f"✅ Legitimate SMS - No alert needed")
            self.legitimate_messages_passed += 1
        else:
            print(f"⚠️ Suspicious but no automatic alert (confidence: {result['confidence']}%)")
        
        print("")
        return result
    
    def check_sms_message(self, message):
        """Enhanced SMS message security check"""
        if not message.strip():
            return {"safe": True, "confidence": 0, "message": "Empty message"}
        
        normalized = message.lower()
        score = 0
        reasons = []
        
        # High-risk indicators
        high_risk_phrases = [
            "won", "prize", "lottery", "congratulations", "claim",
            "free", "gift", "urgent", "immediately", "million", "cash award"
        ]
        
        # Security-related keywords
        security_keywords = [
            "bvn", "password", "pin", "verification", "suspended",
            "reset", "authenticate", "validate", "confirm", "account"
        ]
        
        # Check high-risk phrases
        for phrase in high_risk_phrases:
            if phrase in normalized:
                score += 6
                reasons.append(phrase)
        
        # Check security keywords
        for keyword in security_keywords:
            if keyword in normalized:
                score += 5
                reasons.append(keyword)
        
        # Check for URLs
        if "http://" in normalized or "https://" in normalized or "www." in normalized:
            score += 8
            reasons.append("suspicious_url")
        
        # Check for phone number requests
        if ("call" in normalized or "contact" in normalized or "reply" in normalized) and any(char.isdigit() for char in normalized):
            score += 7
            reasons.append("phone_request")
        
        # Check for money mentions
        if "$" in normalized or "cash" in normalized or "money" in normalized or "naira" in normalized:
            score += 4
            reasons.append("money_mention")
        
        # Determine result
        if score >= 20:
            return {
                "safe": False,
                "confidence": 95,
                "message": f"🚨 HIGH-RISK SCAM SMS DETECTED\n⚠️ Contains: {', '.join(set(reasons[:4]))}\n🔒 Do not respond or click links",
                "color": "red"
            }
        elif score >= 15:
            return {
                "safe": False,
                "confidence": 80,
                "message": f"⚠️ SUSPICIOUS SMS DETECTED\nContains: {', '.join(set(reasons[:3]))}\nBe very cautious",
                "color": "orange"
            }
        elif score >= 10:
            return {
                "safe": False,
                "confidence": 65,
                "message": f"⚠️ POTENTIALLY RISKY SMS\nDetected: {', '.join(set(reasons[:2]))}\nVerify before acting",
                "color": "orange"
            }
        else:
            return {
                "safe": True,
                "confidence": 90,
                "message": "✅ Likely legitimate SMS\nNo obvious scam patterns detected",
                "color": "green"
            }
    
    def print_stats(self):
        print("=" * 50)
        print("📊 AUTOMATIC DETECTION STATISTICS:")
        print(f"   Scam messages detected: {self.scam_messages_detected}")
        print(f"   Legitimate messages passed: {self.legitimate_messages_passed}")
        print(f"   Total messages processed: {self.scam_messages_detected + self.legitimate_messages_passed}")
        print("=" * 50)

# Test the automatic detection
def main():
    detector = AutoSMSDetector()
    
    print("🚀 TESTING AUTOMATIC SMS DETECTION")
    print("===================================")
    print("Simulating real-time SMS monitoring...")
    print("")
    
    # Test scam messages (should trigger automatic alerts)
    scam_messages = [
        ("Congratulations! You won $1,000,000 lottery! Call 09012345678 to claim.", "Lottery Scam"),
        ("Your GTBank account has been suspended. Verify your BVN immediately at http://gtbank-verify.com", "Phishing Scam"),
        ("Free iPhone 14! Click http://bit.ly/free-iphone-now to claim your gift!", "Free Gift Scam"),
        ("URGENT: Your password needs resetting. Reply with your PIN for verification.", "Password Scam"),
        ("You have won 5,000,000 Naira! Send your account details to claim your cash prize.", "Money Scam"),
        ("Your account will be closed today. Call 08031234567 immediately to verify.", "Urgency Scam"),
    ]
    
    print("🔴 TESTING SCAM MESSAGES (Should trigger alerts):")
    print("")
    for message, scam_type in scam_messages:
        detector.simulate_incoming_sms(message, f"Scam-{scam_type}")
    
    # Test legitimate messages (should not trigger alerts)
    legit_messages = [
        ("Hi John, are we still meeting tomorrow at 3 PM?", "Friend"),
        ("Your package has been delivered. Tracking number: ABC123XYZ", "DHL"),
        ("Your Uber is arriving in 5 minutes. Driver: Mike - Toyota Corolla", "Uber"),
        ("Your bank statement for January is ready for download", "GTBank"),
        ("Reminder: Dentist appointment tomorrow at 10 AM", "Clinic"),
        ("Your monthly subscription renewal was successful. Amount: ₦2,500", "Service"),
    ]
    
    print("🟢 TESTING LEGITIMATE MESSAGES (No alerts expected):")
    print("")
    for message, sender in legit_messages:
        detector.simulate_incoming_sms(message, sender)
    
    # Print final statistics
    detector.print_stats()
    
    print("")
    print("🎯 AUTOMATIC DETECTION FEATURES:")
    print("✅ Real-time SMS monitoring")
    print("✅ Instant scam alerts")
    print("✅ Background operation")
    print("✅ No user interaction needed")
    print("✅ Works with existing SMS app")
    print("")
    print("📱 On Android: User receives notification immediately for high-risk scams!")

if __name__ == "__main__":
    main()
