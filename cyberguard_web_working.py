#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import re
import os

PORT = 8001

class CyberGuardHandler(http.server.BaseHTTPRequestHandler):
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
                print(f"   - Safe codes: {len(database['safe_codes'])}")
                print(f"   - Scam patterns: {len(database['scam_patterns'])}")
                print(f"   - Scam keywords: {len(database['scam_keywords'])}")
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
            self.serve_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            self.send_error(404, "File not found")
    
    def serve_html(self):
        """Serve the main HTML interface"""
        html_content = self.generate_html_interface()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html_content)))
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def handle_check(self):
        """Handle security check requests"""
        # Parse query parameters
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        code = params.get('code', [''])[0]
        sms = params.get('sms', [''])[0]
        
        if code:
            result = self.check_ussd_code(code)
            print(f"🔍 Checking USSD code: {code}")
        elif sms:
            result = self.check_sms_message(sms)
            print(f"🔍 Checking SMS message: {sms[:50]}...")
        else:
            result = {"error": "No code or SMS provided"}
        
        print(f"✅ Result: {result['message']}")
        
        # Send JSON response
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
    
    def check_ussd_code(self, code):
        """Check USSD code security"""
        normalized = code.lower().strip()
        
        # Check safe codes
        for safe_code in self.database["safe_codes"]:
            if safe_code["code"].lower() == normalized:
                return {
                    "safe": True,
                    "confidence": 95,
                    "message": f"✅ SAFE - {safe_code['description']}",
                    "color": "green"
                }
        
        # Check scam patterns
        for pattern in self.database["scam_patterns"]:
            if re.search(pattern, normalized, re.IGNORECASE):
                return {
                    "safe": False,
                    "confidence": 90,
                    "message": f"🚨 SCAM - Matches scam pattern: '{pattern}'",
                    "color": "red"
                }
        
        # Check scam keywords
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
            if re.search(pattern, normalized, re.IGNORECASE):
                score += 8
                reasons.append(f"High-risk: '{pattern}'")
        
        for pattern in medium_risk_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                score += 4
                reasons.append(f"Medium-risk: '{pattern}'")
        
        # Check scam keywords
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                score += 3
                reasons.append(f"Keyword: '{keyword}'")
        
        # Check for suspicious URLs
        if re.search(r'http://|https://|www\.|bit\.ly|tinyurl|click.*here', normalized, re.IGNORECASE):
            score += 6
            reasons.append("Suspicious URL")
        
        # Check for phone number requests
        if re.search(r'call.*\d|phone.*number|contact.*us|dial.*\d|send.*number', normalized, re.IGNORECASE):
            score += 5
            reasons.append("Phone request")
        
        # Check for money mentions
        if re.search(r'\$\d|\d+\s*(dollar|naira|usd)|million|cash|money', normalized, re.IGNORECASE):
            score += 3
            reasons.append("Money mention")
        
        # Determine result
        if score >= 15:
            return {
                "safe": False,
                "confidence": 90,
                "message": f"🚨 HIGH-RISK SCAM SMS (Score: {score}/25)\nDetected: {', '.join(reasons[:3])}",
                "color": "red"
            }
        elif score >= 10:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS SMS (Score: {score}/25)\nDetected: {', '.join(reasons[:2])}",
                "color": "orange"
            }
        elif score >= 5:
            return {
                "safe": False,
                "confidence": 60,
                "message": f"⚠️ POTENTIALLY RISKY (Score: {score}/25)\nDetected: {reasons[0] if reasons else 'Unknown pattern'}",
                "color": "orange"
            }
        else:
            return {
                "safe": True,
                "confidence": 95,
                "message": "✅ Likely legitimate SMS",
                "color": "green"
            }
    
    def generate_html_interface(self):
        """Generate the enhanced HTML interface with tabs"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard Security Scanner</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        .container { background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { text-align: center; margin-bottom: 20px; }
        .header h1 { color: #333; margin-bottom: 10px; }
        .tabs { display: flex; margin-bottom: 20px; border-bottom: 2px solid #ddd; }
        .tab { padding: 10px 20px; background: #f8f9fa; border: none; margin-right: 5px; cursor: pointer; }
        .tab.active { background: #007bff; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        .input-group { margin-bottom: 15px; }
        .input-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .input-group input, .input-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .input-group textarea { height: 100px; resize: vertical; }
        .button { background: #007bff; color: white; border: none; padding: 12px 20px; border-radius: 5px; cursor: pointer; width: 100%; font-size: 16px; }
        .button:hover { background: #0056b3; }
        .result { margin-top: 20px; padding: 15px; border-radius: 5px; text-align: center; font-weight: bold; min-height: 60px; display: flex; align-items: center; justify-content: center; }
        .safe { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
        .danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .unknown { background: #e2e3e5; color: #383d41; border: 1px solid #d6d8db; }
        .examples { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-top: 15px; }
        .examples h3 { margin-top: 0; }
        .example-item { margin: 5px 0; padding: 5px; cursor: pointer; border-radius: 3px; }
        .example-item:hover { background: #e9ecef; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CyberGuard Security Scanner</h1>
            <p>Complete USSD & SMS Fraud Detection</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('ussd')">📟 USSD Scanner</button>
            <button class="tab" onclick="switchTab('sms')">💬 SMS Scanner</button>
        </div>

        <div id="ussd-tab" class="tab-content active">
            <div class="input-group">
                <label for="ussdInput">Enter USSD Code:</label>
                <input type="text" id="ussdInput" placeholder="e.g., *901# or *123*password*#">
            </div>
            <button class="button" onclick="checkUSSD()">Check USSD Security</button>
            
            <div class="examples">
                <h3>Try these examples:</h3>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*901#'">*901# - Safe banking</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*123*password*#'">*123*password*# - Scam</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*123*bvn*456#'">*123*bvn*456# - BVN scam</div>
            </div>
        </div>

        <div id="sms-tab" class="tab-content">
            <div class="input-group">
                <label for="smsInput">Enter SMS Message:</label>
                <textarea id="smsInput" placeholder="Paste SMS message to check for scams..."></textarea>
            </div>
            <button class="button" onclick="checkSMS()">Check SMS Security</button>
            
            <div class="examples">
                <h3>Try these examples:</h3>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Congratulations! You won $1,000,000 lottery!'">Lottery scam</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Your account needs verification. Send BVN.'">BVN scam</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Hi, are we meeting tomorrow?'">Legitimate</div>
            </div>
        </div>

        <div id="result" class="result unknown">
            System Ready - Select a tab and enter code/SMS to check security
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            document.getElementById('result').className = 'result unknown';
            if (tabName === 'ussd') {
                document.getElementById('result').innerHTML = 'System Ready - Enter a USSD code to check security';
            } else {
                document.getElementById('result').innerHTML = 'System Ready - Enter an SMS message to check for scams';
            }
        }

        function checkUSSD() {
            const code = document.getElementById('ussdInput').value.trim();
            if (!code) return alert('Please enter a USSD code');
            
            fetch('/check?code=' + encodeURIComponent(code))
                .then(r => r.json())
                .then(data => {
                    const result = document.getElementById('result');
                    result.innerHTML = data.message;
                    result.className = 'result ' + (data.color === 'green' ? 'safe' : data.color === 'orange' ? 'warning' : data.color === 'red' ? 'danger' : 'unknown');
                })
                .catch(err => {
                    document.getElementById('result').innerHTML = '❌ Error checking code';
                    document.getElementById('result').className = 'result danger';
                });
        }

        function checkSMS() {
            const sms = document.getElementById('smsInput').value.trim();
            if (!sms) return alert('Please enter an SMS message');
            
            fetch('/check?sms=' + encodeURIComponent(sms))
                .then(r => r.json())
                .then(data => {
                    const result = document.getElementById('result');
                    result.innerHTML = data.message.replace(/\\n/g, '<br>');
                    result.className = 'result ' + (data.color === 'green' ? 'safe' : data.color === 'orange' ? 'warning' : data.color === 'red' ? 'danger' : 'unknown');
                })
                .catch(err => {
                    document.getElementById('result').innerHTML = '❌ Error checking SMS';
                    document.getElementById('result').className = 'result danger';
                });
        }
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """Override to show custom log format"""
        print(f"🌐 {format % args}")

print(f"🚀 Starting CyberGuard Web Interface...")
print(f"📍 Open: http://localhost:{PORT}")
print(f"📱 Features: USSD Scanner + SMS Fraud Detection")
print(f"🛑 Press Ctrl+C to stop the server")
print("=" * 50)

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
