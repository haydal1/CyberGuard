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
                return database
            else:
                print(f"❌ Database file not found: {database_path}")
                return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
        except Exception as e:
            print(f"❌ Failed to load database: {e}")
            return {"safe_codes": [], "scam_patterns": [], "scam_keywords": []}
    
    def do_GET(self):
        """Handle GET requests"""
        print(f"🔍 Received request: {self.path}")
        
        if self.path == '/':
            self.serve_html()
        elif self.path.startswith('/check'):
            self.handle_check()
        else:
            self.send_error(404, "File not found")
    
    def serve_html(self):
        """Serve the HTML interface with extensive debugging"""
        html_content = self.generate_debug_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Content-Length', str(len(html_content)))
        self.end_headers()
        self.wfile.write(html_content.encode())
        print("✅ Served HTML page")
    
    def handle_check(self):
        """Handle security check requests"""
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        code = params.get('code', [''])[0]
        sms = params.get('sms', [''])[0]
        
        print(f"🔍 Check request - code: {code}, sms: {sms}")
        
        if code:
            result = self.check_ussd_code(code)
            print(f"✅ USSD Check Result: {result['message']}")
        elif sms:
            result = self.check_sms_message(sms)
            print(f"✅ SMS Check Result: {result['message']}")
        else:
            result = {"error": "No code or SMS provided"}
        
        response = json.dumps(result).encode()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)
        print("✅ Sent JSON response")
    
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
    
    def generate_debug_html(self):
        """Generate HTML with extensive debugging"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard Debug</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; }
        .container { border: 2px solid #333; padding: 20px; border-radius: 10px; }
        .header { text-align: center; margin-bottom: 20px; }
        .tabs { display: flex; margin-bottom: 20px; }
        .tab { flex: 1; padding: 10px; border: 1px solid #ccc; background: #f0f0f0; cursor: pointer; }
        .tab.active { background: #007bff; color: white; }
        .tab-content { display: none; padding: 20px; border: 1px solid #ccc; }
        .tab-content.active { display: block; }
        .button { padding: 10px 20px; background: #28a745; color: white; border: none; cursor: pointer; margin: 10px 0; }
        .debug { background: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; margin-top: 20px; }
        .log { background: #000; color: #0f0; padding: 10px; font-family: monospace; height: 200px; overflow-y: scroll; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🐛 CyberGuard Debug</h1>
            <p>Testing Interface - Check browser console for errors</p>
        </div>

        <div class="tabs">
            <button class="tab active" id="ussdTab">USSD Scanner</button>
            <button class="tab" id="smsTab">SMS Scanner</button>
        </div>

        <div id="ussd-content" class="tab-content active">
            <h3>USSD Security Check</h3>
            <input type="text" id="ussdInput" placeholder="Enter USSD code" value="*901#">
            <button class="button" id="checkUSSD">Check USSD</button>
            <button class="button" id="testUSSD">Test USSD Example</button>
        </div>

        <div id="sms-content" class="tab-content">
            <h3>SMS Security Check</h3>
            <textarea id="smsInput" placeholder="Enter SMS message">Congratulations you won a prize!</textarea>
            <button class="button" id="checkSMS">Check SMS</button>
            <button class="button" id="testSMS">Test SMS Example</button>
        </div>

        <div id="result" style="padding: 20px; background: #e9ecef; margin: 20px 0;">
            Result will appear here...
        </div>

        <div class="debug">
            <h3>Debug Log</h3>
            <div class="log" id="debugLog">
                Debug messages will appear here...
            </div>
            <button class="button" id="clearLog">Clear Log</button>
        </div>
    </div>

    <script>
        // Debug logging function
        function debugLog(message) {
            const log = document.getElementById('debugLog');
            log.innerHTML += '> ' + message + '\\n';
            log.scrollTop = log.scrollHeight;
            console.log('DEBUG:', message);
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', function() {
            debugLog('🚀 Page loaded - initializing event listeners');
            
            // Tab switching
            const ussdTab = document.getElementById('ussdTab');
            const smsTab = document.getElementById('smsTab');
            const ussdContent = document.getElementById('ussd-content');
            const smsContent = document.getElementById('sms-content');

            ussdTab.addEventListener('click', function() {
                debugLog('📟 USSD tab clicked');
                ussdTab.classList.add('active');
                smsTab.classList.remove('active');
                ussdContent.classList.add('active');
                smsContent.classList.remove('active');
            });

            smsTab.addEventListener('click', function() {
                debugLog('💬 SMS tab clicked');
                smsTab.classList.add('active');
                ussdTab.classList.remove('active');
                smsContent.classList.add('active');
                ussdContent.classList.remove('active');
            });

            // USSD Check
            document.getElementById('checkUSSD').addEventListener('click', function() {
                const code = document.getElementById('ussdInput').value;
                debugLog(`🔍 Checking USSD: ${code}`);
                
                document.getElementById('result').innerHTML = '🔄 Checking...';
                
                fetch('/check?code=' + encodeURIComponent(code))
                    .then(response => {
                        debugLog(`📡 Response status: ${response.status}`);
                        return response.json();
                    })
                    .then(data => {
                        debugLog(`✅ USSD Result: ${data.message}`);
                        document.getElementById('result').innerHTML = data.message;
                    })
                    .catch(error => {
                        debugLog(`❌ USSD Error: ${error}`);
                        document.getElementById('result').innerHTML = 'Error: ' + error;
                    });
            });

            // SMS Check
            document.getElementById('checkSMS').addEventListener('click', function() {
                const sms = document.getElementById('smsInput').value;
                debugLog(`🔍 Checking SMS: ${sms.substring(0, 50)}...`);
                
                document.getElementById('result').innerHTML = '🔄 Checking...';
                
                fetch('/check?sms=' + encodeURIComponent(sms))
                    .then(response => {
                        debugLog(`📡 Response status: ${response.status}`);
                        return response.json();
                    })
                    .then(data => {
                        debugLog(`✅ SMS Result: ${data.message}`);
                        document.getElementById('result').innerHTML = data.message;
                    })
                    .catch(error => {
                        debugLog(`❌ SMS Error: ${error}`);
                        document.getElementById('result').innerHTML = 'Error: ' + error;
                    });
            });

            // Test buttons
            document.getElementById('testUSSD').addEventListener('click', function() {
                document.getElementById('ussdInput').value = '*123*password*#';
                debugLog('🧪 Set USSD test example');
            });

            document.getElementById('testSMS').addEventListener('click', function() {
                document.getElementById('smsInput').value = 'You won $1,000,000! Click here to claim.';
                debugLog('🧪 Set SMS test example');
            });

            // Clear log
            document.getElementById('clearLog').addEventListener('click', function() {
                document.getElementById('debugLog').innerHTML = '';
                debugLog('🗑️ Log cleared');
            });

            debugLog('✅ All event listeners attached successfully');
            debugLog('👉 Try clicking tabs and buttons to test functionality');
        });

        // Global error handler
        window.addEventListener('error', function(e) {
            debugLog(`💥 Global error: ${e.message}`);
        });
    </script>
</body>
</html>'''
    
    def log_message(self, format, *args):
        """Override to show custom log format"""
        print(f"🌐 {format % args}")

print(f"🚀 Starting CyberGuard Debug Interface...")
print(f"📍 Open: http://localhost:{PORT}")
print(f"🐛 This version has extensive debugging to identify the issue")
print(f"🛑 Press Ctrl+C to stop the server")
print("=" * 50)

with socketserver.TCPServer(("", PORT), CyberGuardHandler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
