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
            self.serve_enhanced_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            super().do_GET()
    
    def serve_enhanced_html(self):
        """Serve enhanced HTML with better instructions"""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard Security Scanner</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 100%;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .instructions {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            border-left: 4px solid #667eea;
        }
        .instructions h3 {
            color: #2d3748;
            margin-bottom: 10px;
        }
        .tabs {
            display: flex;
            background: #f7fafc;
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 25px;
        }
        .tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        .tab.active {
            background: white;
            color: #667eea;
            box-shadow: 0 2px 8px rgba(102,126,234,0.15);
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .input-group {
            margin-bottom: 20px;
        }
        .input-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }
        .input-group input, .input-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
        }
        .input-group textarea {
            height: 120px;
            resize: vertical;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-bottom: 20px;
        }
        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .safe { background: #d4edda; color: #155724; }
        .warning { background: #fff3cd; color: #856404; }
        .danger { background: #f8d7da; color: #721c24; }
        .unknown { background: #e2e3e5; color: #383d41; }
        .examples {
            background: #f7fafc;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
        }
        .example-item {
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 8px;
            cursor: pointer;
        }
        .example-item:hover {
            background: #667eea;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CyberGuard</h1>
            <p>Complete Security Scanner - USSD & SMS Fraud Detection</p>
        </div>

        <div class="instructions">
            <h3>📱 How to Use:</h3>
            <p><strong>USSD:</strong> Enter any USSD code to check safety</p>
            <p><strong>SMS:</strong> Copy suspicious SMS and paste here to scan</p>
            <p><em>Note: This is manual detection. Copy SMS from messages app.</em></p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('ussd')">📟 USSD Scanner</button>
            <button class="tab" onclick="switchTab('sms')">💬 SMS Scanner</button>
        </div>

        <div id="ussd-content" class="tab-content active">
            <div class="input-group">
                <label>Enter USSD Code</label>
                <input type="text" id="ussdInput" value="*901#" placeholder="e.g., *901#">
            </div>
            <button class="button" onclick="checkUSSD()">Check USSD Security</button>
            
            <div class="examples">
                <h3>Test Examples:</h3>
                <div class="example-item" onclick="setExample('ussd', '*901#')">*901# - Safe banking</div>
                <div class="example-item" onclick="setExample('ussd', '*123*password*#')">*123*password*# - Scam</div>
                <div class="example-item" onclick="setExample('ussd', '*123*bvn*456#')">*123*bvn*456# - BVN scam</div>
            </div>
        </div>

        <div id="sms-content" class="tab-content">
            <div class="input-group">
                <label>Paste SMS Message Here</label>
                <textarea id="smsInput" placeholder="Copy suspicious SMS from your messages and paste here...">Congratulations you won a prize!</textarea>
            </div>
            <button class="button" onclick="checkSMS()">Scan SMS for Scams</button>
            
            <div class="examples">
                <h3>Common Scam Examples:</h3>
                <div class="example-item" onclick="setExample('sms', 'Congratulations! You won $1,000,000 lottery! Call now to claim.')">Lottery scam</div>
                <div class="example-item" onclick="setExample('sms', 'Your account needs verification. Send your BVN immediately.')">BVN scam</div>
                <div class="example-item" onclick="setExample('sms', 'Free iPhone! Click http://bit.ly/free-iphone to claim now!')">Free gift scam</div>
            </div>
        </div>

        <div id="result" class="result unknown">
            Ready - Enter code or paste SMS to check security
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            document.getElementById(tabName + '-content').classList.add('active');
            
            const result = document.getElementById('result');
            result.className = 'result unknown';
            if (tabName === 'ussd') {
                result.innerHTML = 'Ready - Enter USSD code to check security';
            } else {
                result.innerHTML = 'Ready - Paste SMS message to scan for scams';
            }
        }

        function setExample(type, value) {
            if (type === 'ussd') {
                document.getElementById('ussdInput').value = value;
            } else {
                document.getElementById('smsInput').value = value;
            }
        }

        function checkUSSD() {
            const code = document.getElementById('ussdInput').value.trim();
            if (!code) return alert('Please enter a USSD code');
            
            const result = document.getElementById('result');
            result.innerHTML = 'Checking...';
            result.className = 'result unknown';
            
            fetch('/check?code=' + encodeURIComponent(code))
                .then(response => response.json())
                .then(data => {
                    result.innerHTML = data.message;
                    result.className = 'result ' + (data.color === 'green' ? 'safe' : data.color === 'orange' ? 'warning' : data.color === 'red' ? 'danger' : 'unknown');
                })
                .catch(error => {
                    result.innerHTML = 'Error checking code';
                    result.className = 'result danger';
                });
        }

        function checkSMS() {
            const sms = document.getElementById('smsInput').value.trim();
            if (!sms) return alert('Please paste an SMS message');
            
            const result = document.getElementById('result');
            result.innerHTML = 'Scanning for scams...';
            result.className = 'result unknown';
            
            fetch('/check?sms=' + encodeURIComponent(sms))
                .then(response => response.json())
                .then(data => {
                    result.innerHTML = data.message.replace(/\\n/g, '<br>');
                    result.className = 'result ' + (data.color === 'green' ? 'safe' : data.color === 'orange' ? 'warning' : data.color === 'red' ? 'danger' : 'unknown');
                })
                .catch(error => {
                    result.innerHTML = 'Error scanning SMS';
                    result.className = 'result danger';
                });
        }
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
        print("✅ Served enhanced HTML")
    
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
        """Enhanced USSD code security check"""
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
            try:
                if re.search(pattern, normalized, re.IGNORECASE):
                    return {
                        "safe": False,
                        "confidence": 90,
                        "message": f"🚨 SCAM - Matches suspicious pattern",
                        "color": "red"
                    }
            except re.error:
                continue
        
        # Check scam keywords
        found_keywords = []
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                found_keywords.append(keyword)
        
        if found_keywords:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS - Contains risky keywords: {', '.join(found_keywords)}",
                "color": "orange"
            }
        
        return {
            "safe": False,
            "confidence": 50,
            "message": "❓ Unknown code - use caution",
            "color": "gray"
        }
    
    def check_sms_message(self, message):
        """Enhanced SMS message security check"""
        if not message.strip():
            return {
                "safe": False,
                "confidence": 0,
                "message": "❌ Empty message - please paste an SMS",
                "color": "gray"
            }
        
        normalized = message.lower()
        score = 0
        reasons = []
        
        # High-risk indicators
        high_risk_phrases = [
            "won", "prize", "lottery", "congratulations", "claim",
            "free", "gift", "urgent", "immediately", "million"
        ]
        
        # Security-related keywords
        security_keywords = [
            "bvn", "password", "pin", "verification", "suspended",
            "reset", "authenticate", "validate", "confirm"
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
        if ("call" in normalized or "contact" in normalized) and any(char.isdigit() for char in normalized):
            score += 7
            reasons.append("phone_request")
        
        # Check for money mentions
        if "$" in normalized or "cash" in normalized or "money" in normalized:
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

print(f"🚀 Starting ENHANCED CyberGuard Interface...")
print(f"📍 Open: http://localhost:8001")
print(f"🎯 Better detection + Clear instructions")
print(f"🛑 Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
