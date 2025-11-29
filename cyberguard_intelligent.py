#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import re
import os

PORT = 8001

class IntelligentDetector:
    def __init__(self):
        self.trusted_patterns = [
            r'^\*9\d{2}#$', r'^\*737#', r'^\*894#', r'^\*919#', r'^\*822#',
            r'^\*966#', r'^\*770#', r'^\*131#', r'^\*310#', r'^\*123#', r'^\*232#'
        ]
        
    def is_legitimate_structure(self, code):
        """Check if code follows standard USSD patterns"""
        patterns = [
            r'^\*\d{3}#$', r'^\*\d{3}\*\d+#$', r'^\*\d{3}\*\d+\*\d+#$'
        ]
        return any(re.match(p, code) for p in patterns)
    
    def is_trusted_service(self, code):
        """Check if code matches known service patterns"""
        return any(re.match(p, code) for p in self.trusted_patterns)
    
    def contains_scam_indicators(self, code):
        scam_words = ['password', 'pin', 'bvn', 'winner', 'won', 'prize', 'lottery']
        return any(word in code.lower() for word in scam_words)

class CyberGuardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.database = self.load_database()
        self.intelligent_detector = IntelligentDetector()
        super().__init__(*args, **kwargs)
    
    def load_database(self):
        try:
            with open('CyberGuardAndroid/app/src/main/assets/ussd_database.json', 'r') as f:
                return json.load(f)
        except:
            return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
    
    def do_GET(self):
        if self.path == '/':
            self.serve_enhanced_html()
        elif self.path.startswith('/check'):
            self.handle_intelligent_check()
        elif self.path == '/stats':
            self.handle_stats()
        else:
            self.send_error(404, "Not found")
    
    def handle_intelligent_check(self):
        """Enhanced check with intelligent detection"""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        code = params.get('code', [''])[0]
        sms = params.get('sms', [''])[0]
        
        if code:
            result = self.check_ussd_code_intelligent(code)
        elif sms:
            result = self.check_sms_message(sms)
        else:
            result = {"message": "No code or SMS provided", "color": "gray"}
        
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response)
    
    def check_ussd_code_intelligent(self, code):
        """
        INTELLIGENT DETECTION - Prevents false positives
        """
        normalized = code.strip()
        
        # 1. First check safe database (existing known codes)
        for safe_code in self.database["safe_codes"]:
            if safe_code["code"] == normalized:
                return {
                    "message": f"✅ SAFE - {safe_code['description']}",
                    "color": "green",
                    "confidence": "high"
                }
        
        # 2. Check for obvious scams
        if self.intelligent_detector.contains_scam_indicators(normalized):
            return {
                "message": "🚨 SCAM - Contains suspicious keywords",
                "color": "red", 
                "confidence": "high"
            }
        
        # 3. INTELLIGENT CHECK: Is it likely a legitimate code?
        if self.intelligent_detector.is_legitimate_structure(normalized):
            if self.intelligent_detector.is_trusted_service(normalized):
                return {
                    "message": "✅ LIKELY SAFE - Matches legitimate service pattern",
                    "color": "green",
                    "confidence": "medium"
                }
            else:
                return {
                    "message": "⚠️ UNKNOWN - Legitimate structure but verify with provider",
                    "color": "orange", 
                    "confidence": "low"
                }
        
        # 4. Check scam patterns (existing logic)
        for pattern in self.database["scam_patterns"]:
            if re.search(pattern, normalized, re.IGNORECASE):
                return {
                    "message": "🚨 SCAM - Matches known scam pattern",
                    "color": "red",
                    "confidence": "high"
                }
        
        # 5. Final fallback
        return {
            "message": "❓ UNKNOWN - Use caution and verify with service provider",
            "color": "gray",
            "confidence": "very low"
        }
    
    def check_sms_message(self, message):
        """Existing SMS detection (unchanged)"""
        if not message.strip():
            return {"message": "❌ Empty message", "color": "gray"}
        
        normalized = message.lower()
        score = 0
        
        high_risk = ["won", "prize", "lottery", "congratulations", "claim", "free", "gift"]
        security_words = ["bvn", "password", "pin", "verification", "suspended", "reset"]
        
        for phrase in high_risk:
            if phrase in normalized: score += 6
        for keyword in security_words:
            if keyword in normalized: score += 5
        if "http://" in normalized or "https://" in normalized: score += 8
        
        if score >= 20:
            return {"message": "🚨 HIGH-RISK SCAM SMS DETECTED", "color": "red"}
        elif score >= 15:
            return {"message": "⚠️ SUSPICIOUS SMS DETECTED", "color": "orange"}
        elif score >= 10:
            return {"message": "⚠️ POTENTIALLY RISKY SMS", "color": "orange"}
        else:
            return {"message": "✅ Likely legitimate SMS", "color": "green"}
    
    def handle_stats(self):
        stats = {
            "safe_codes": len(self.database["safe_codes"]),
            "scam_patterns": len(self.database["scam_patterns"]),
            "status": "online",
            "detection": "intelligent"
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def serve_enhanced_html(self):
        html = """<html><body>
        <h1>🛡️ CyberGuard - Intelligent Detection</h1>
        <p>Now with smarter USSD code analysis to prevent false positives!</p>
        <p>Test endpoints: /check?code=*901# /stats</p>
        </body></html>"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())

print("🧠 Starting INTELLIGENT CyberGuard...")
print("✅ Prevents false positives for legitimate code changes")
with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
