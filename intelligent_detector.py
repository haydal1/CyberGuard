#!/usr/bin/env python3
"""
Intelligent USSD Detection - Prevents false positives for legitimate code changes
"""
import re
import json

class IntelligentDetector:
    def __init__(self):
        self.trusted_patterns = [
            # Bank patterns (most Nigerian banks follow these)
            r'^\*9\d{2}#$',      # *901#, *902#, etc. (Access Bank, etc.)
            r'^\*737#',          # GTBank patterns
            r'^\*894#',          # FirstBank patterns  
            r'^\*919#',          # UBA patterns
            r'^\*822#',          # Sterling Bank
            r'^\*966#',          # Zenith Bank
            r'^\*770#',          # Fidelity Bank
            
            # Telecom patterns
            r'^\*131#',          # Glo
            r'^\*310#',          # Airtel  
            r'^\*123#',          # MTN
            r'^\*232#',          # 9mobile
            
            # Standard service patterns
            r'^\*144#',          # Customer care
            r'^\*312#',          # Value added services
            r'^\*321#',          # Data services
        ]
        
        self.legitimate_structures = [
            # Simple service codes (most legitimate codes are simple)
            r'^\*\d{3}#$',                    # *123#
            r'^\*\d{3}\*\d+#$',               # *123*1#
            r'^\*\d{3}\*\d+\*\d+#$',          # *123*1*1#
        ]
    
    def is_trusted_structure(self, code):
        """Check if code follows legitimate USSD structure patterns"""
        for pattern in self.legitimate_structures:
            if re.match(pattern, code):
                return True
        return False
    
    def is_trusted_pattern(self, code):
        """Check if code matches known trusted service patterns"""
        for pattern in self.trusted_patterns:
            if re.match(pattern, code):
                return True
        return False
    
    def contains_scam_keywords(self, code):
        """Check for obvious scam indicators"""
        scam_indicators = [
            'password', 'pin', 'bvn', 'winner', 'won', 'prize', 
            'lottery', 'claim', 'free', 'gift', 'urgent', 'verification',
            'suspended', 'reset', 'confirm', 'update', 'security'
        ]
        
        code_lower = code.lower()
        return any(keyword in code_lower for keyword in scam_indicators)
    
    def analyze_ussd_code(self, code):
        """
        Intelligent analysis - not just black/white
        Returns: SAFE, LIKELY_SAFE, SUSPICIOUS, SCAM
        """
        if not code or not code.strip():
            return "UNKNOWN", "Empty code"
        
        normalized_code = code.strip()
        
        # 1. Check if it's in safe database (existing known codes)
        # This would be your current safe list check
        
        # 2. Check for obvious scams
        if self.contains_scam_keywords(normalized_code):
            return "SCAM", "Contains scam keywords"
        
        # 3. Check if it follows legitimate structure patterns
        if not self.is_trusted_structure(normalized_code):
            return "SUSPICIOUS", "Unusual USSD structure"
        
        # 4. Check if it matches known trusted service patterns
        if self.is_trusted_pattern(normalized_code):
            return "LIKELY_SAFE", "Matches legitimate service pattern"
        
        # 5. Length and complexity check (legitimate codes are usually short)
        if len(normalized_code) > 20:  # Very long codes are suspicious
            return "SUSPICIOUS", "Unusually long USSD code"
        
        # 6. Check for excessive special characters (besides * and #)
        special_chars = len([c for c in normalized_code if c not in '*#0123456789'])
        if special_chars > 2:
            return "SUSPICIOUS", "Contains unusual characters"
        
        # If all checks pass, it's likely safe but unknown
        return "LIKELY_SAFE", "Appears to be legitimate USSD code"

# Test the intelligent detector
def test_intelligent_detection():
    detector = IntelligentDetector()
    
    test_cases = [
        # Legitimate codes (should be safe/likely safe)
        ("*901#", "Access Bank - known safe"),
        ("*902#", "Access Bank new code - not in database"),
        ("*737#", "GTBank - known safe"),
        ("*737*1#", "GTBank transfer - known safe"),
        ("*123#", "MTN balance - known safe"),
        ("*144#", "Customer care - legitimate"),
        
        # New legitimate codes (banks might introduce these)
        ("*903#", "Hypothetical new bank code"),
        ("*738#", "Hypothetical GTBank new service"),
        ("*124#", "Hypothetical MTN new service"),
        
        # Scam codes (should be detected)
        ("*123*password*#", "Obvious scam"),
        ("*500*bvn*123#", "BVN scam"),
        ("*123*winner*#", "Lottery scam"),
        ("*456*verification*#", "Verification scam"),
        
        # Borderline cases
        ("*123*123*123*123#", "Unusually long but might be legitimate"),
        ("*999#", "Unknown but follows pattern"),
    ]
    
    print("🧠 INTELLIGENT USSD DETECTION TEST")
    print("===================================")
    
    for code, description in test_cases:
        status, reason = detector.analyze_ussd_code(code)
        print(f"{code:20} | {status:12} | {reason:45} | {description}")

if __name__ == "__main__":
    test_intelligent_detection()
