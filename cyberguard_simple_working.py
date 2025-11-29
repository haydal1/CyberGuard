#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import re
import os

PORT = 8001

class CyberGuardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.database = self.load_database()
        super().__init__(*args, **kwargs)
    
    def load_database(self):
        """Load the USSD database"""
        try:
            database_path = 'CyberGuardAndroid/app/src/main/assets/ussd_database.json'
            if os.path.exists(database_path):
                with open(database_path, 'r') as f:
                    database = json.load(f)
                print("✅ Loaded USSD database successfully")
                return database
            else:
                print(f"❌ Database file not found: {database_path}")
                return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
        except Exception as e:
            print(f"❌ Failed to load database: {e}")
            return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.serve_simple_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            super().do_GET()
    
    def serve_simple_html(self):
        """Serve a very simple HTML interface that definitely works"""
        html = '''<!DOCTYPE html>
<html>
<head>
    <title>CyberGuard - SIMPLE</title>
    <style>
        body { font-family: Arial; max-width: 600px; margin: 40px auto; padding: 20px; }
        .tab { padding: 10px; margin: 5px; cursor: pointer; border: 1px solid #ccc; }
        .active { background: blue; color: white; }
        .content { display: none; padding: 20px; border: 1px solid #ccc; margin: 10px 0; }
        .active-content { display: block; }
        button { padding: 10px; margin: 5px; }
        #result { padding: 20px; margin: 10px 0; background: #f0f0f0; }
    </style>
</head>
<body>
    <h1>CyberGuard Simple Test</h1>
    
    <div>
        <button class="tab active" onclick="showTab('ussd')">USSD</button>
        <button class="tab" onclick="showTab('sms')">SMS</button>
    </div>
    
    <div id="ussd-content" class="content active-content">
        <h3>USSD Check</h3>
        <input type="text" id="ussdInput" value="*901#">
        <button onclick="checkUSSD()">Check USSD</button>
    </div>
    
    <div id="sms-content" class="content">
        <h3>SMS Check</h3>
        <textarea id="smsInput" rows="3" cols="50">Congratulations you won!</textarea>
        <button onclick="checkSMS()">Check SMS</button>
    </div>
    
    <div id="result">Click a button to see results here</div>

    <script>
        // Simple tab switching
        function showTab(tabName) {
            console.log('Showing tab:', tabName);
            
            // Hide all content
            document.querySelectorAll('.content').forEach(el => {
                el.classList.remove('active-content');
            });
            document.querySelectorAll('.tab').forEach(el => {
                el.classList.remove('active');
            });
            
            // Show selected content
            document.getElementById(tabName + '-content').classList.add('active-content');
            event.target.classList.add('active');
        }
        
        // Simple USSD check
        function checkUSSD() {
            const code = document.getElementById('ussdInput').value;
            console.log('Checking USSD:', code);
            
            document.getElementById('result').innerHTML = 'Checking...';
            
            fetch('/check?code=' + encodeURIComponent(code))
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = data.message;
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = 'Error: ' + error;
                });
        }
        
        // Simple SMS check
        function checkSMS() {
            const sms = document.getElementById('smsInput').value;
            console.log('Checking SMS:', sms);
            
            document.getElementById('result').innerHTML = 'Checking...';
            
            fetch('/check?sms=' + encodeURIComponent(sms))
                .then(response => response.json())
                .then(data => {
                    document.getElementById('result').innerHTML = data.message;
                })
                .catch(error => {
                    document.getElementById('result').innerHTML = 'Error: ' + error;
                });
        }
        
        console.log('Simple CyberGuard loaded successfully!');
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
        print("✅ Served simple HTML")
    
    def handle_check(self):
        """Handle security check requests"""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        code = params.get('code', [''])[0]
        sms = params.get('sms', [''])[0]
        
        print(f"🔍 Check request - code: {code}, sms: {sms}")
        
        if code:
            result = self.check_ussd_code(code)
        elif sms:
            result = self.check_sms_message(sms)
        else:
            result = {"error": "No code or SMS provided"}
        
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response)
        print("✅ Sent response")
    
    def check_ussd_code(self, code):
        """Check USSD code security"""
        normalized = code.lower().strip()
        
        for safe_code in self.database["safe_codes"]:
            if safe_code["code"].lower() == normalized:
                return {
                    "safe": True,
                    "confidence": 95,
                    "message": f"✅ SAFE - {safe_code['description']}",
                    "color": "green"
                }
        
        for pattern in self.database["scam_patterns"]:
            if re.search(pattern, normalized, re.IGNORECASE):
                return {
                    "safe": False,
                    "confidence": 90,
                    "message": f"🚨 SCAM - Matches scam pattern: '{pattern}'",
                    "color": "red"
                }
        
        found_keywords = []
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                found_keywords.append(keyword)
        
        if found_keywords:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS - Contains scam keywords: {', '.join(found_keywords)}",
                "color": "orange"
            }
        
        return {
            "safe": False,
            "confidence": 50,
            "message": "❓ Unknown code - use caution",
            "color": "gray"
        }
    
    def check_sms_message(self, message):
        """Check SMS message security"""
        if not message.strip():
            return {
                "safe": False,
                "confidence": 0,
                "message": "❌ Empty message",
                "color": "gray"
            }
        
        normalized = message.lower()
        score = 0
        reasons = []
        
        high_risk_patterns = [
            "won.*prize", "win.*lottery", "congratulations.*won", 
            "claim.*prize", "free.*gift", "urgent.*account",
            "bvn.*required", "password.*reset", "pin.*verification"
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                score += 8
                reasons.append(f"High-risk: '{pattern}'")
        
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                score += 3
                reasons.append(f"Keyword: '{keyword}'")
        
        if score >= 10:
            return {
                "safe": False,
                "confidence": 90,
                "message": f"🚨 HIGH-RISK SCAM SMS (Score: {score})\nDetected: {', '.join(reasons[:2])}",
                "color": "red"
            }
        elif score >= 5:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS SMS (Score: {score})\nDetected: {reasons[0] if reasons else 'Unknown pattern'}",
                "color": "orange"
            }
        else:
            return {
                "safe": True,
                "confidence": 95,
                "message": "✅ Likely legitimate SMS",
                "color": "green"
            }

print(f"🚀 Starting ULTRA-SIMPLE CyberGuard Interface...")
print(f"📍 Open: http://localhost:{PORT}")
print(f"🎯 This version uses basic JavaScript that should definitely work")
print(f"🛑 Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
