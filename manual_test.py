#!/usr/bin/env python3
import json
import re

class CyberGuardTester:
    def __init__(self):
        with open('CyberGuardAndroid/app/src/main/assets/ussd_database.json', 'r') as f:
            self.db = json.load(f)
    
    def test_ussd_interactive(self):
        print("\n" + "="*50)
        print("📟 USSD CODE TESTING INTERFACE")
        print("="*50)
        
        while True:
            code = input("\nEnter USSD code to test (or 'quit'): ").strip()
            if code.lower() == 'quit':
                break
            
            result = self.analyze_ussd(code)
            print(f"\n🔍 ANALYSIS RESULT: {result}")
    
    def test_sms_interactive(self):
        print("\n" + "="*50)
        print("💬 SMS MESSAGE TESTING INTERFACE")  
        print("="*50)
        
        while True:
            message = input("\nEnter SMS message to test (or 'quit'): ").strip()
            if message.lower() == 'quit':
                break
            
            result = self.analyze_sms(message)
            print(f"\n🔍 ANALYSIS RESULT: {result}")
    
    def analyze_ussd(self, code):
        normalized = code.lower().strip()
        
        # Check safe codes
        for safe_code in self.db["safe_codes"]:
            if safe_code["code"].lower() == normalized:
                return f"✅ SAFE - {safe_code['description']}"
        
        # Check scam patterns
        for pattern in self.db["scam_patterns"]:
            if re.search(pattern, normalized, re.IGNORECASE):
                return f"🚨 SCAM - Matches known scam pattern: '{pattern}'"
        
        # Check scam keywords
        found_keywords = []
        for keyword in self.db["scam_keywords"]:
            if keyword in normalized:
                found_keywords.append(keyword)
        
        if found_keywords:
            return f"⚠️ SUSPICIOUS - Contains scam keywords: {', '.join(found_keywords)}"
        
        return "❓ UNKNOWN - Code not in database. Use with caution."
    
    def analyze_sms(self, message):
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
                reasons.append(f"High-risk pattern: '{pattern}'")
        
        for pattern in medium_risk_patterns:
            if re.search(pattern, normalized):
                score += 4
                reasons.append(f"Medium-risk pattern: '{pattern}'")
        
        # Check for URLs
        if re.search(r'http://|https://|www\.|bit\.ly|tinyurl', normalized):
            score += 6
            reasons.append("Contains suspicious URL")
        
        # Check for phone requests
        if re.search(r'call.*\d|phone.*number|contact.*us|dial.*\d', normalized):
            score += 5
            reasons.append("Requests phone contact")
        
        # Determine result
        if score >= 15:
            return f"🚨 HIGH-RISK SCAM (Score: {score}/25)\nReasons: {', '.join(reasons)}"
        elif score >= 10:
            return f"⚠️ SUSPICIOUS SMS (Score: {score}/25)\nReasons: {', '.join(reasons)}"
        elif score >= 5:
            return f"⚠️ POTENTIALLY RISKY (Score: {score}/25)\nReasons: {', '.join(reasons)}"
        else:
            return f"✅ LIKELY LEGITIMATE (Score: {score}/25)"
    
    def run_demo_tests(self):
        print("\n" + "="*50)
        print("🎯 DEMONSTRATION TEST CASES")
        print("="*50)
        
        # USSD demo tests
        ussd_demos = [
            "*901#",
            "*500*1234*password#", 
            "*123*bvn*1234#",
            "*999*winner*5000#"
        ]
        
        print("\n📟 USSD DEMO TESTS:")
        for ussd in ussd_demos:
            result = self.analyze_ussd(ussd)
            print(f"  {ussd} -> {result}")
        
        # SMS demo tests
        sms_demos = [
            "Congratulations! You won $1,000,000 lottery! Call 09012345678 to claim",
            "Your bank account needs verification. Reply with your BVN immediately",
            "Hi, your package delivery is scheduled for tomorrow",
            "Free iPhone! Click http://bit.ly/free-iphone to claim now!"
        ]
        
        print("\n💬 SMS DEMO TESTS:")
        for sms in sms_demos:
            result = self.analyze_sms(sms)
            print(f"  {sms[:40]}... -> {result.split(chr(10))[0]}")

if __name__ == "__main__":
    tester = CyberGuardTester()
    
    print("🔒 CYBERGUARD SECURITY TESTING SUITE")
    print("====================================")
    
    tester.run_demo_tests()
    
    while True:
        print("\nChoose testing mode:")
        print("1. Test USSD codes")
        print("2. Test SMS messages") 
        print("3. Run demo tests")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            tester.test_ussd_interactive()
        elif choice == "2":
            tester.test_sms_interactive()
        elif choice == "3":
            tester.run_demo_tests()
        elif choice == "4":
            print("👋 Testing complete. Ready for deployment!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")
