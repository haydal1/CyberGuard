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
            self.serve_perfect_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            super().do_GET()
    
    def serve_perfect_html(self):
        """Serve the perfect HTML - beautiful + working"""
        html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard Security Scanner</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

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
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            max-width: 500px;
            width: 100%;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .header p {
            color: #718096;
            font-size: 1.1em;
            font-weight: 500;
        }

        .tabs {
            display: flex;
            background: #f7fafc;
            border-radius: 12px;
            padding: 4px;
            margin-bottom: 25px;
            border: 1px solid #e2e8f0;
        }

        .tab {
            flex: 1;
            padding: 12px 20px;
            background: transparent;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            font-size: 14px;
            color: #718096;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .tab.active {
            background: white;
            color: #667eea;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
        }

        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .input-group {
            margin-bottom: 20px;
        }

        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #4a5568;
            font-weight: 600;
            font-size: 14px;
        }

        .input-group input, .input-group textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            font-size: 16px;
            transition: all 0.3s ease;
            background: white;
            font-family: inherit;
        }

        .input-group input:focus, .input-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }

        .input-group textarea {
            height: 120px;
            resize: vertical;
            line-height: 1.5;
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
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }

        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        }

        .button:active {
            transform: translateY(0);
        }

        .result {
            margin-top: 25px;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-weight: 600;
            font-size: 16px;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            border: 2px solid transparent;
        }

        .safe {
            background: linear-gradient(135deg, #48bb78, #38a169);
            color: white;
            border-color: #48bb78;
        }

        .warning {
            background: linear-gradient(135deg, #ed8936, #dd6b20);
            color: white;
            border-color: #ed8936;
        }

        .danger {
            background: linear-gradient(135deg, #f56565, #e53e3e);
            color: white;
            border-color: #f56565;
        }

        .unknown {
            background: #f7fafc;
            color: #718096;
            border-color: #e2e8f0;
        }

        .examples {
            background: #f7fafc;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            border: 1px solid #e2e8f0;
        }

        .examples h3 {
            margin-bottom: 15px;
            color: #4a5568;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .example-item {
            padding: 10px 12px;
            margin: 6px 0;
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 14px;
            color: #4a5568;
        }

        .example-item:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
            transform: translateX(5px);
        }

        .status-bar {
            display: flex;
            justify-content: space-between;
            margin-top: 20px;
            padding: 15px;
            background: #f7fafc;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
        }

        .status-item {
            text-align: center;
            flex: 1;
        }

        .status-value {
            font-size: 1.2em;
            font-weight: 700;
            color: #667eea;
        }

        .status-label {
            font-size: 0.8em;
            color: #718096;
            margin-top: 4px;
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
            <button class="tab active" id="ussdTab">📟 USSD Scanner</button>
            <button class="tab" id="smsTab">💬 SMS Scanner</button>
        </div>

        <!-- USSD Scanner Tab -->
        <div id="ussd-content" class="tab-content active">
            <div class="input-group">
                <label>Enter USSD Code</label>
                <input type="text" id="ussdInput" placeholder="e.g., *901# or *123*password*#" value="*901#">
            </div>
            <button class="button" id="checkUSSD">🔍 Check USSD Security</button>
            
            <div class="examples">
                <h3>Quick Test Examples</h3>
                <div class="example-item" data-type="ussd" data-value="*901#">*901# - Safe banking code</div>
                <div class="example-item" data-type="ussd" data-value="*123#">*123# - Safe telecom code</div>
                <div class="example-item" data-type="ussd" data-value="*123*password*#">*123*password*# - Dangerous scam</div>
                <div class="example-item" data-type="ussd" data-value="*999*123#">*999*123# - Unknown code</div>
                <div class="example-item" data-type="ussd" data-value="*123*bvn*456#">*123*bvn*456# - BVN scam</div>
            </div>
        </div>

        <!-- SMS Scanner Tab -->
        <div id="sms-content" class="tab-content">
            <div class="input-group">
                <label>Enter SMS Message</label>
                <textarea id="smsInput" placeholder="Paste SMS message here to check for scams...">Congratulations you won a prize!</textarea>
            </div>
            <button class="button" id="checkSMS">🔍 Check SMS Security</button>
            
            <div class="examples">
                <h3>Common Scam Examples</h3>
                <div class="example-item" data-type="sms" data-value="Congratulations! You won $1,000,000 lottery! Call now to claim.">Lottery scam message</div>
                <div class="example-item" data-type="sms" data-value="Your account needs verification. Send your BVN immediately.">BVN verification scam</div>
                <div class="example-item" data-type="sms" data-value="Free iPhone! Click http://bit.ly/free-iphone to claim now!">Free gift scam with URL</div>
                <div class="example-item" data-type="sms" data-value="Hi John, are we still meeting tomorrow at 3 PM?">Legitimate message</div>
                <div class="example-item" data-type="sms" data-value="Your password needs resetting. Reply with your PIN for verification.">Password reset scam</div>
            </div>
        </div>

        <div id="result" class="result unknown">
            System Ready - Select a tab and enter code/SMS to check security
        </div>

        <div class="status-bar">
            <div class="status-item">
                <div class="status-value">25</div>
                <div class="status-label">Safe Codes</div>
            </div>
            <div class="status-item">
                <div class="status-value">20</div>
                <div class="status-label">Scam Patterns</div>
            </div>
            <div class="status-item">
                <div class="status-value">32</div>
                <div class="status-label">Keywords</div>
            </div>
        </div>
    </div>

    <script>
        // Simple and reliable JavaScript
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 CyberGuard Perfect Version Loaded');
            
            // Tab switching - SIMPLE AND RELIABLE
            const ussdTab = document.getElementById('ussdTab');
            const smsTab = document.getElementById('smsTab');
            const ussdContent = document.getElementById('ussd-content');
            const smsContent = document.getElementById('sms-content');
            
            ussdTab.addEventListener('click', function() {
                console.log('📟 Switching to USSD tab');
                ussdTab.classList.add('active');
                smsTab.classList.remove('active');
                ussdContent.classList.add('active');
                smsContent.classList.remove('active');
                updateResultMessage('ussd');
            });
            
            smsTab.addEventListener('click', function() {
                console.log('💬 Switching to SMS tab');
                smsTab.classList.add('active');
                ussdTab.classList.remove('active');
                smsContent.classList.add('active');
                ussdContent.classList.remove('active');
                updateResultMessage('sms');
            });
            
            // USSD Check - SIMPLE AND RELIABLE
            document.getElementById('checkUSSD').addEventListener('click', function() {
                const code = document.getElementById('ussdInput').value.trim();
                if (!code) {
                    alert('Please enter a USSD code');
                    return;
                }
                
                console.log('🔍 Checking USSD:', code);
                checkSecurity('code', code);
            });
            
            // SMS Check - SIMPLE AND RELIABLE
            document.getElementById('checkSMS').addEventListener('click', function() {
                const sms = document.getElementById('smsInput').value.trim();
                if (!sms) {
                    alert('Please enter an SMS message');
                    return;
                }
                
                console.log('🔍 Checking SMS:', sms.substring(0, 50) + '...');
                checkSecurity('sms', sms);
            });
            
            // Example items - SIMPLE AND RELIABLE
            document.querySelectorAll('.example-item').forEach(item => {
                item.addEventListener('click', function() {
                    const type = this.getAttribute('data-type');
                    const value = this.getAttribute('data-value');
                    
                    if (type === 'ussd') {
                        document.getElementById('ussdInput').value = value;
                    } else {
                        document.getElementById('smsInput').value = value;
                    }
                    
                    // Visual feedback
                    this.style.background = '#667eea';
                    this.style.color = 'white';
                    setTimeout(() => {
                        this.style.background = '';
                        this.style.color = '';
                    }, 300);
                });
            });
            
            // Enter key support
            document.getElementById('ussdInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    document.getElementById('checkUSSD').click();
                }
            });
            
            console.log('✅ All event listeners attached successfully');
        });
        
        function updateResultMessage(tab) {
            const result = document.getElementById('result');
            result.className = 'result unknown';
            if (tab === 'ussd') {
                result.innerHTML = 'System Ready - Enter a USSD code to check security';
            } else {
                result.innerHTML = 'System Ready - Enter an SMS message to check for scams';
            }
        }
        
        function checkSecurity(type, value) {
            const result = document.getElementById('result');
            result.innerHTML = '🔄 Checking...';
            result.className = 'result unknown';
            
            const url = `/check?${type}=${encodeURIComponent(value)}`;
            
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network error');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('✅ Result:', data);
                    result.innerHTML = data.message.replace(/\n/g, '<br>');
                    result.className = 'result ' + getColorClass(data.color);
                })
                .catch(error => {
                    console.error('❌ Error:', error);
                    result.innerHTML = '❌ Error checking - please try again';
                    result.className = 'result danger';
                });
        }
        
        function getColorClass(color) {
            switch(color) {
                case 'green': return 'safe';
                case 'orange': return 'warning';
                case 'red': return 'danger';
                default: return 'unknown';
            }
        }
    </script>
</body>
</html>'''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
        print("✅ Served perfect HTML")
    
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
            "bvn.*required", "password.*reset", "pin.*verification",
            "account.*suspended", "verification.*required"
        ]
        
        medium_risk_patterns = [
            "million", "cash.*award", "immediately", "click.*link",
            "call.*now", "limited.*time", "exclusive.*offer"
        ]
        
        for pattern in high_risk_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                score += 8
                reasons.append(f"High-risk: '{pattern}'")
        
        for pattern in medium_risk_patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                score += 4
                reasons.append(f"Medium-risk: '{pattern}'")
        
        for keyword in self.database["scam_keywords"]:
            if keyword in normalized:
                score += 3
                reasons.append(f"Keyword: '{keyword}'")
        
        if re.search(r'http://|https://|www\.|bit\.ly|tinyurl|click.*here', normalized, re.IGNORECASE):
            score += 6
            reasons.append("Suspicious URL")
        
        if re.search(r'call.*\d|phone.*number|contact.*us|dial.*\d|send.*number', normalized, re.IGNORECASE):
            score += 5
            reasons.append("Phone request")
        
        if re.search(r'\$\d|\d+\s*(dollar|naira|usd)|million|cash|money', normalized, re.IGNORECASE):
            score += 3
            reasons.append("Money mention")
        
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

print(f"🚀 Starting CYBERGUARD PERFECT VERSION...")
print(f"📍 Open: http://localhost:{PORT}")
print(f"🎨 Beautiful design + ✅ Working functionality")
print(f"📱 Both USSD & SMS detection")
print(f"🛑 Press Ctrl+C to stop the server")

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
