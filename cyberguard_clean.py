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
            self.serve_clean_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            super().do_GET()
    
    def serve_clean_html(self):
        """Serve clean HTML with working JavaScript"""
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

        <div class="tabs">
            <button class="tab active" onclick="switchTab('ussd')">📟 USSD</button>
            <button class="tab" onclick="switchTab('sms')">💬 SMS</button>
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
                <label>Enter SMS Message</label>
                <textarea id="smsInput" placeholder="Paste SMS message...">Congratulations you won a prize!</textarea>
            </div>
            <button class="button" onclick="checkSMS()">Check SMS Security</button>
            
            <div class="examples">
                <h3>Test Examples:</h3>
                <div class="example-item" onclick="setExample('sms', 'Congratulations! You won $1,000,000 lottery!')">Lottery scam</div>
                <div class="example-item" onclick="setExample('sms', 'Your account needs verification. Send BVN.')">BVN scam</div>
                <div class="example-item" onclick="setExample('sms', 'Hi, are we meeting tomorrow?')">Legitimate</div>
            </div>
        </div>

        <div id="result" class="result unknown">
            Ready - Enter code or message to check security
        </div>
    </div>

    <script>
        // Simple tab switching
        function switchTab(tabName) {
            console.log('Switching to:', tabName);
            
            // Update tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Update content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + '-content').classList.add('active');
            
            // Update result message
            const result = document.getElementById('result');
            result.className = 'result unknown';
            if (tabName === 'ussd') {
                result.innerHTML = 'Ready - Enter USSD code to check security';
            } else {
                result.innerHTML = 'Ready - Enter SMS message to check security';
            }
        }

        // Set example values
        function setExample(type, value) {
            if (type === 'ussd') {
                document.getElementById('ussdInput').value = value;
            } else {
                document.getElementById('smsInput').value = value;
            }
        }

        // Check USSD
        function checkUSSD() {
            const code = document.getElementById('ussdInput').value.trim();
            if (!code) {
                alert('Please enter a USSD code');
                return;
            }
            
            console.log('Checking USSD:', code);
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

        // Check SMS
        function checkSMS() {
            const sms = document.getElementById('smsInput').value.trim();
            if (!sms) {
                alert('Please enter an SMS message');
                return;
            }
            
            console.log('Checking SMS:', sms.substring(0, 50));
            const result = document.getElementById('result');
            result.innerHTML = 'Checking...';
            result.className = 'result unknown';
            
            fetch('/check?sms=' + encodeURIComponent(sms))
                .then(response => response.json())
                .then(data => {
                    result.innerHTML = data.message.replace(/\\n/g, '<br>');
                    result.className = 'result ' + (data.color === 'green' ? 'safe' : data.color === 'orange' ? 'warning' : data.color === 'red' ? 'danger' : 'unknown');
                })
                .catch(error => {
                    result.innerHTML = 'Error checking SMS';
                    result.className = 'result danger';
                });
        }

        console.log('CyberGuard loaded successfully');
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
        print("✅ Served clean HTML")
    
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
                        "message": f"🚨 SCAM - Matches pattern: {pattern}",
                        "color": "red"
                    }
            except re.error:
                continue  # Skip invalid regex patterns
        
        # Check scam keywords
        found_keywords = []
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                found_keywords.append(keyword)
        
        if found_keywords:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS - Contains: {', '.join(found_keywords)}",
                "color": "orange"
            }
        
        return {
            "safe": False,
            "confidence": 50,
            "message": "❓ Unknown code - use caution",
            "color": "gray"
        }
    
    def check_sms_message(self, message):
        """Check SMS message security - SIMPLIFIED"""
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
        
        # Simple keyword checking (no complex regex)
        scam_indicators = [
            "won", "prize", "lottery", "congratulations", "claim",
            "free", "gift", "urgent", "bvn", "password", "pin",
            "verification", "suspended", "reset", "million", "cash"
        ]
        
        for indicator in scam_indicators:
            if indicator in normalized:
                score += 5
                reasons.append(indicator)
        
        # Check for URLs
        if "http://" in normalized or "https://" in normalized or "www." in normalized:
            score += 10
            reasons.append("suspicious_url")
        
        # Check for phone requests
        if "call" in normalized and any(char.isdigit() for char in normalized):
            score += 8
            reasons.append("phone_request")
        
        # Determine result
        if score >= 15:
            return {
                "safe": False,
                "confidence": 90,
                "message": f"🚨 HIGH-RISK SCAM SMS\nDetected: {', '.join(reasons[:3])}",
                "color": "red"
            }
        elif score >= 10:
            return {
                "safe": False,
                "confidence": 75,
                "message": f"⚠️ SUSPICIOUS SMS\nDetected: {', '.join(reasons[:2])}",
                "color": "orange"
            }
        elif score >= 5:
            return {
                "safe": False,
                "confidence": 60,
                "message": f"⚠️ POTENTIALLY RISKY\nDetected: {reasons[0] if reasons else 'suspicious_content'}",
                "color": "orange"
            }
        else:
            return {
                "safe": True,
                "confidence": 95,
                "message": "✅ Likely legitimate SMS",
                "color": "green"
            }

print(f"🚀 Starting CLEAN CyberGuard Interface...")
print(f"📍 Open: http://localhost:{PORT}")
print(f"🔧 Fixed regex errors + working functionality")
print(f"🛑 Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
