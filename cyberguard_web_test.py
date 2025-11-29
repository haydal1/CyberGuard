#!/usr/bin/env python3
"""
CyberGuard Web Test Interface
Full web version that mimics the Android app functionality
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import re

class USSDSecurityEngine:
    def __init__(self):
        # Load the same database used by Android app
        try:
            with open('CyberGuardAndroid/app/src/main/assets/ussd_database.json', 'r') as f:
                self.database = json.load(f)
            print("✅ Loaded USSD database successfully")
            print(f"   - Safe codes: {len(self.database['safe_ussd_codes'])}")
            print(f"   - Scam patterns: {len(self.database['scam_keywords'])}")
        except Exception as e:
            print(f"❌ Error loading database: {e}")
            # Fallback database
            self.database = {
                "safe_ussd_codes": ["*901#", "*902#", "*909#", "*123#", "*124#"],
                "scam_keywords": ["password", "bvn", "pin", "won", "prize"],
                "suspicious_patterns": ["*xxx*xxx*xxx*xxx#"],
                "rules": {"safe_prefixes": ["*123", "*901"]}
            }
    
    def check_ussd(self, code):
        """Main security check logic - same as Android app"""
        if not code or not code.strip():
            return self._create_result(False, 0, "❌ Please enter a USSD code", "gray")
        
        normalized = self._normalize_ussd(code)
        
        # 1. Check known safe codes
        if normalized in self.database["safe_ussd_codes"]:
            return self._create_result(True, 95, "✅ Known safe USSD code", "green")
        
        # 2. Check suspicious patterns
        if self._has_suspicious_pattern(normalized):
            return self._create_result(False, 80, "⚠️ Suspicious pattern detected", "orange")
        
        # 3. Check scam keywords
        if self._contains_scam_keywords(normalized):
            return self._create_result(False, 90, "🚨 Contains scam keywords!", "red")
        
        # 4. Check safe prefixes
        if self._has_safe_prefix(normalized):
            return self._create_result(True, 60, "✅ Starts with known safe prefix", "green")
        
        return self._create_result(False, 50, "❓ Unknown code - use caution", "orange")
    
    def _normalize_ussd(self, code):
        return code.strip().replace(" ", "").upper()
    
    def _has_suspicious_pattern(self, code):
        for pattern in self.database.get("suspicious_patterns", []):
            regex_pattern = pattern.replace("xxx", ".*")
            if re.match(regex_pattern, code):
                return True
        return False
    
    def _contains_scam_keywords(self, code):
        for keyword in self.database.get("scam_keywords", []):
            if keyword.lower() in code.lower():
                return True
        return False
    
    def _has_safe_prefix(self, code):
        for prefix in self.database.get("rules", {}).get("safe_prefixes", []):
            if code.startswith(prefix):
                return True
        return False
    
    def _create_result(self, is_safe, confidence, message, color):
        return {
            "safe": is_safe,
            "confidence": confidence,
            "message": message,
            "color": color
        }

# Initialize the security engine
security_engine = USSDSecurityEngine()

class CyberGuardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self._serve_main_page()
        elif self.path.startswith('/check?'):
            self._handle_api_check()
        elif self.path == '/stats':
            self._serve_stats()
        else:
            self._serve_404()
    
    def do_POST(self):
        if self.path == '/check':
            self._handle_form_check()
        else:
            self._serve_404()
    
    def _serve_main_page(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CyberGuard USSD Security</title>
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
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    padding: 40px;
                    max-width: 500px;
                    width: 100%;
                    text-align: center;
                }
                .logo {
                    font-size: 3em;
                    margin-bottom: 10px;
                }
                h1 {
                    color: #333;
                    margin-bottom: 10px;
                    font-size: 2.2em;
                }
                .subtitle {
                    color: #666;
                    margin-bottom: 30px;
                    font-size: 1.1em;
                }
                .input-group {
                    margin-bottom: 25px;
                    text-align: left;
                }
                label {
                    display: block;
                    margin-bottom: 8px;
                    color: #333;
                    font-weight: 600;
                }
                input {
                    width: 100%;
                    padding: 15px;
                    border: 2px solid #e1e5e9;
                    border-radius: 10px;
                    font-size: 16px;
                    transition: border-color 0.3s;
                }
                input:focus {
                    outline: none;
                    border-color: #667eea;
                }
                button {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 10px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s;
                    width: 100%;
                }
                button:hover {
                    transform: translateY(-2px);
                }
                .result {
                    margin-top: 25px;
                    padding: 20px;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 16px;
                    display: none;
                }
                .safe { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
                .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
                .danger { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
                .unknown { background: #e2e3e5; color: #383d41; border: 2px solid #d6d8db; }
                .examples {
                    margin-top: 30px;
                    text-align: left;
                }
                .examples h3 {
                    margin-bottom: 15px;
                    color: #333;
                }
                .example-list {
                    display: grid;
                    gap: 10px;
                }
                .example {
                    padding: 10px;
                    border-radius: 8px;
                    cursor: pointer;
                    transition: background 0.2s;
                }
                .example:hover {
                    background: #f8f9fa;
                }
                .example.safe { border-left: 4px solid #28a745; }
                .example.danger { border-left: 4px solid #dc3545; }
                .example.warning { border-left: 4px solid #ffc107; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🔒</div>
                <h1>CyberGuard</h1>
                <div class="subtitle">USSD Security Scanner</div>
                
                <form id="checkForm" method="POST" action="/check">
                    <div class="input-group">
                        <label for="ussd_code">Enter USSD Code:</label>
                        <input type="text" id="ussd_code" name="ussd_code" 
                               placeholder="e.g., *901# or *123*password*#" required>
                    </div>
                    <button type="submit">Check Security</button>
                </form>
                
                <div id="result" class="result"></div>
                
                <div class="examples">
                    <h3>Try these examples:</h3>
                    <div class="example-list">
                        <div class="example safe" onclick="setExample('*901#')">*901# - Safe banking code</div>
                        <div class="example safe" onclick="setExample('*123#')">*123# - Safe telecom code</div>
                        <div class="example danger" onclick="setExample('*123*password*#')">*123*password*# - Dangerous scam</div>
                        <div class="example warning" onclick="setExample('*999*123#')">*999*123# - Unknown code</div>
                        <div class="example danger" onclick="setExample('*123*bvn*456#')">*123*bvn*456# - BVN scam</div>
                    </div>
                </div>
            </div>
            
            <script>
                function setExample(code) {
                    document.getElementById('ussd_code').value = code;
                }
                
                // Handle form submission with AJAX
                document.getElementById('checkForm').addEventListener('submit', function(e) {
                    e.preventDefault();
                    const code = document.getElementById('ussd_code').value;
                    
                    fetch('/check?code=' + encodeURIComponent(code))
                        .then(response => response.json())
                        .then(data => {
                            const result = document.getElementById('result');
                            result.textContent = data.message;
                            result.className = 'result ' + data.color;
                            result.style.display = 'block';
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                });
            </script>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def _handle_api_check(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        code = params.get('code', [''])[0]
        
        result = security_engine.check_ussd(code)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())
    
    def _handle_form_check(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode()
        params = urllib.parse.parse_qs(post_data)
        code = params.get('ussd_code', [''])[0]
        
        result = security_engine.check_ussd(code)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        color_class = {
            'green': 'safe',
            'orange': 'warning', 
            'red': 'danger',
            'gray': 'unknown'
        }.get(result['color'], 'unknown')
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CyberGuard Result</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .result {{ padding: 20px; margin: 20px 0; border-radius: 10px; font-weight: bold; }}
                .safe {{ background: #d4edda; color: #155724; }}
                .warning {{ background: #fff3cd; color: #856404; }}
                .danger {{ background: #f8d7da; color: #721c24; }}
                a {{ display: inline-block; margin-top: 20px; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <h1>CyberGuard Result</h1>
            <p><strong>USSD Code:</strong> {code}</p>
            <div class="result {color_class}">{result['message']}</div>
            <p><strong>Confidence:</strong> {result['confidence']}%</p>
            <a href="/">← Check Another Code</a>
        </body>
        </html>
        """
        self.wfile.write(html.encode())
    
    def _serve_stats(self):
        stats = {
            "safe_codes": len(security_engine.database["safe_ussd_codes"]),
            "scam_patterns": len(security_engine.database["scam_keywords"]),
            "database_version": "1.0"
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(stats).encode())
    
    def _serve_404(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'<h1>404 - Not Found</h1><p>The page you requested was not found.</p>')

def main():
    port = 8001  # Use different port than your backend
    server = HTTPServer(('localhost', port), CyberGuardHandler)
    
    print("🚀 CyberGuard Web Test Interface Started!")
    print("📍 Open your browser and go to: http://localhost:8001")
    print("📱 This mimics the exact same logic as your Android app")
    print("🛑 Press Ctrl+C to stop the server")
    print("\n" + "="*50)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
