#!/usr/bin/env python3
import http.server
import socketserver
import json
import urllib.parse
import re
from http import HTTPStatus

class CyberGuardWebHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load_database()
    
    def load_database(self):
        """Load the USSD database"""
        try:
            with open('CyberGuardAndroid/app/src/main/assets/ussd_database.json', 'r') as f:
                self.database = json.load(f)
            print("✅ Loaded USSD database successfully")
            print(f"   - Safe codes: {len(self.database['safe_codes'])}")
            print(f"   - Scam patterns: {len(self.database['scam_patterns'])}")
            print(f"   - Scam keywords: {len(self.database['scam_keywords'])}")
        except Exception as e:
            print(f"❌ Failed to load database: {e}")
            self.database = {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
    
    def check_ussd_code(self, code):
        """Check USSD code security (same logic as Android app)"""
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
        """Check SMS message security (same logic as Android app)"""
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
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html_content = self.generate_html_interface()
            self.wfile.write(html_content.encode())
        
        elif self.path.startswith('/check'):
            # Parse query parameters
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            code = params.get('code', [''])[0]
            sms = params.get('sms', [''])[0]
            
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            if code:
                result = self.check_ussd_code(code)
                print(f"🔍 Checking USSD code: {code}")
            elif sms:
                result = self.check_sms_message(sms)
                print(f"🔍 Checking SMS message: {sms[:50]}...")
            else:
                result = {"error": "No code or SMS provided"}
            
            print(f"✅ Result: {result['message']}")
            self.wfile.write(json.dumps(result).encode())
        
        else:
            super().do_GET()
    
    def generate_html_interface(self):
        """Generate the enhanced HTML interface with tabs"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard Security Scanner</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #666;
            font-size: 1.2em;
        }}
        .tabs {{
            display: flex;
            margin-bottom: 20px;
            border-bottom: 2px solid #eee;
        }}
        .tab {{
            padding: 12px 24px;
            background: #f8f9fa;
            border: none;
            border-radius: 8px 8px 0 0;
            margin-right: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }}
        .tab.active {{
            background: #667eea;
            color: white;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .input-group {{
            margin-bottom: 20px;
        }}
        .input-group label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }}
        .input-group input, .input-group textarea {{
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        .input-group input:focus, .input-group textarea:focus {{
            border-color: #667eea;
            outline: none;
        }}
        .input-group textarea {{
            height: 100px;
            resize: vertical;
        }}
        .button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
        }}
        .button:hover {{
            transform: translateY(-2px);
        }}
        .result {{
            margin-top: 20px;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
            min-height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .safe {{ background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }}
        .warning {{ background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }}
        .danger {{ background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }}
        .unknown {{ background: #e2e3e5; color: #383d41; border: 2px solid #d6d8db; }}
        .examples {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .examples h3 {{
            margin-top: 0;
            color: #333;
        }}
        .example-item {{
            margin: 5px 0;
            padding: 5px;
            cursor: pointer;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .example-item:hover {{
            background: #e9ecef;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CyberGuard</h1>
            <p>Complete Security Scanner - USSD & SMS Fraud Detection</p>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('ussd')">📟 USSD Scanner</button>
            <button class="tab" onclick="switchTab('sms')">💬 SMS Scanner</button>
        </div>

        <!-- USSD Scanner Tab -->
        <div id="ussd-tab" class="tab-content active">
            <div class="input-group">
                <label for="ussdInput">Enter USSD Code:</label>
                <input type="text" id="ussdInput" placeholder="e.g., *901# or *123*password*#">
            </div>
            <button class="button" onclick="checkUSSD()">Check USSD Security</button>
            
            <div class="examples">
                <h3>Try these USSD examples:</h3>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*901#'">*901# - Safe banking code</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*123#'">*123# - Safe telecom code</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*123*password*#'">*123*password*# - Dangerous scam</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*999*123#'">*999*123# - Unknown code</div>
                <div class="example-item" onclick="document.getElementById('ussdInput').value = '*123*bvn*456#'">*123*bvn*456# - BVN scam</div>
            </div>
        </div>

        <!-- SMS Scanner Tab -->
        <div id="sms-tab" class="tab-content">
            <div class="input-group">
                <label for="smsInput">Enter SMS Message:</label>
                <textarea id="smsInput" placeholder="Paste SMS message here to check for scams..."></textarea>
            </div>
            <button class="button" onclick="checkSMS()">Check SMS Security</button>
            
            <div class="examples">
                <h3>Try these SMS examples:</h3>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Congratulations! You won $1,000,000 lottery! Call now to claim.'">Lottery scam message</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Your account needs verification. Send your BVN immediately.'">BVN verification scam</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Free iPhone! Click http://bit.ly/free-iphone to claim now!'">Free gift scam with URL</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Hi John, are we still meeting tomorrow at 3 PM?'">Legitimate message</div>
                <div class="example-item" onclick="document.getElementById('smsInput').value = 'Your password needs resetting. Reply with your PIN for verification.'">Password reset scam</div>
            </div>
        </div>

        <div id="result" class="result unknown">
            System Ready - Select a tab and enter code/SMS to check security
        </div>
    </div>

    <script>
        function switchTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.remove('active');
            }});
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.add('active');
            event.target.classList.add('active');
            
            // Update result message
            document.getElementById('result').className = 'result unknown';
            if (tabName === 'ussd') {{
                document.getElementById('result').innerHTML = 'System Ready - Enter a USSD code to check security';
            }} else {{
                document.getElementById('result').innerHTML = 'System Ready - Enter an SMS message to check for scams';
            }}
        }}

        function checkUSSD() {{
            const code = document.getElementById('ussdInput').value.trim();
            if (!code) {{
                alert('Please enter a USSD code');
                return;
            }}
            
            fetch('/check?code=' + encodeURIComponent(code))
                .then(response => response.json())
                .then(data => {{
                    const result = document.getElementById('result');
                    result.innerHTML = data.message;
                    result.className = 'result ' + getColorClass(data.color);
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    document.getElementById('result').innerHTML = '❌ Error checking code';
                    document.getElementById('result').className = 'result danger';
                }});
        }}

        function checkSMS() {{
            const sms = document.getElementById('smsInput').value.trim();
            if (!sms) {{
                alert('Please enter an SMS message');
                return;
            }}
            
            fetch('/check?sms=' + encodeURIComponent(sms))
                .then(response => response.json())
                .then(data => {{
                    const result = document.getElementById('result');
                    result.innerHTML = data.message.replace(/\\n/g, '<br>');
                    result.className = 'result ' + getColorClass(data.color);
                }})
                .catch(error => {{
                    console.error('Error:', error);
                    document.getElementById('result').innerHTML = '❌ Error checking SMS';
                    document.getElementById('result').className = 'result danger';
                }});
        }}

        function getColorClass(color) {{
            switch(color) {{
                case 'green': return 'safe';
                case 'orange': return 'warning';
                case 'red': return 'danger';
                default: return 'unknown';
            }}
        }}
    </script>
</body>
</html>
'''
