#!/usr/bin/env python3
"""
CyberGuard Premium - Vercel Optimized Version
"""
import os
import re
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

app = Flask(__name__)

# Vercel requires this for serverless functions
@app.route('/.vercel/api')
def vercel_api():
    return jsonify({"status": "ok"})

@app.route('/api/user-stats', methods=['GET'])
def user_stats():
    user_id = request.args.get('user_id', 'default_user')
    return jsonify({
        'is_premium': False,
        'checks_today': 0,
        'total_checks': 0,
        'premium_until': None
    })

@app.route('/api/check-ussd', methods=['POST'])
def check_ussd():
    data = request.get_json()
    code = data.get('code', '').strip()
    
    # Nigerian scam detection logic
    safe_codes = ['*901#', '*894#', '*737#', '*919#', '*822#', '*533#', '*322#', '*326#']
    scam_indicators = ['password', 'pin', 'bvn', 'winner', 'won', 'prize', 'lottery']
    
    code_lower = code.lower()
    
    if code in safe_codes:
        return jsonify({
            'message': '✅ SAFE - Verified Nigerian bank USSD code',
            'type': 'safe',
            'premium_features': None
        })
    elif any(indicator in code_lower for indicator in scam_indicators):
        return jsonify({
            'message': '🚨 DANGER - This USSD code contains scam patterns!',
            'type': 'scam', 
            'premium_features': 'Upgrade to Premium for detailed scam analysis'
        })
    elif re.match(r'^\*\d{3}#$', code):
        return jsonify({
            'message': '✅ LIKELY SAFE - Standard USSD format',
            'type': 'safe',
            'premium_features': None
        })
    else:
        return jsonify({
            'message': '⚠️ UNKNOWN - Verify with service provider',
            'type': 'warning',
            'premium_features': None
        })

@app.route('/api/check-sms', methods=['POST'])
def check_sms():
    data = request.get_json()
    sms = data.get('sms', '').strip()
    
    sms_lower = sms.lower()
    score = 0
    reasons = []
    
    # Detection patterns
    patterns = {
        'won|prize|lottery|congratulations': 10,
        'bvn|password|pin|verification': 8,
        'urgent|immediately|now|today': 5,
        'call |text |whatsapp': 4,
        'http|://|www\.': 6,
        'account|bank|security': 4,
    }
    
    for pattern, points in patterns.items():
        if re.search(pattern, sms_lower, re.IGNORECASE):
            score += points
            reasons.append(pattern)
    
    if re.search(r'08[0-9]{8,}', sms):
        score += 5
        reasons.append('nigerian_phone')
    
    if score >= 15:
        message = '🚨 HIGH-RISK SCAM DETECTED!'
        result_type = 'scam'
    elif score >= 10:
        message = '⚠️ SUSPICIOUS MESSAGE - Be careful!'
        result_type = 'warning'
    else:
        message = '✅ Likely legitimate message'
        result_type = 'safe'
    
    return jsonify({
        'message': message,
        'type': result_type,
        'premium_features': f'Score: {score}/30 - Patterns: {", ".join(reasons[:2])}'
    })

@app.route('/api/upgrade-premium', methods=['POST'])
def upgrade_premium():
    data = request.get_json()
    return jsonify({
        'success': True,
        'message': 'Premium activated! Contact: 080-CYBER-GUARD',
        'premium_until': '2024-12-31'
    })

# Serve the HTML frontend
@app.route('/', methods=['GET'])
def serve_frontend():
    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberGuard NG Premium - Nigerian Fraud Protection</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #0056b3, #003d82);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .premium-badge {
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-left: 10px;
        }
        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        .tab.active {
            background: white;
            border-bottom: 3px solid #007bff;
            font-weight: bold;
        }
        .tab-content {
            display: none;
            padding: 30px;
        }
        .tab-content.active {
            display: block;
        }
        .input-group {
            margin-bottom: 20px;
        }
        input, textarea {
            width: 100%;
            padding: 15px;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus {
            outline: none;
            border-color: #007bff;
        }
        textarea {
            height: 120px;
            resize: vertical;
        }
        .btn {
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            width: 100%;
            transition: transform 0.2s;
            margin: 10px 0;
        }
        .btn:hover {
            transform: translateY(-2px);
        }
        .btn-premium {
            background: linear-gradient(135deg, #FFD700, #FFA500);
            color: #000;
            font-weight: bold;
        }
        .btn-danger {
            background: linear-gradient(135deg, #dc3545, #c82333);
        }
        .result {
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: center;
            font-weight: bold;
            display: none;
        }
        .safe { background: #d4edda; color: #155724; border: 2px solid #c3e6cb; }
        .scam { background: #f8d7da; color: #721c24; border: 2px solid #f5c6cb; }
        .warning { background: #fff3cd; color: #856404; border: 2px solid #ffeaa7; }
        
        @media (max-width: 768px) {
            .tabs { flex-direction: column; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🛡️ CyberGuard NG <span class="premium-badge">PREMIUM</span></h1>
            <p>Advanced Nigerian Fraud Protection with Premium Features</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="switchTab('scanner')">Security Scanner</button>
            <button class="tab" onclick="switchTab('premium')">Go Premium</button>
            <button class="tab" onclick="switchTab('account')">My Account</button>
        </div>
        
        <div id="scanner-content" class="tab-content active">
            <div class="user-stats" id="userStats">
                <strong>Account:</strong> Free | <strong>Checks Today:</strong> 0/5
            </div>
            
            <div class="section">
                <div class="section-title">Check USSD Code Safety</div>
                <div class="input-group">
                    <input type="text" id="ussdInput" placeholder="Enter USSD code e.g. *901# or *123*password*#" value="*901#">
                </div>
                <button class="btn" onclick="checkUSSD()">🔍 Check USSD Safety</button>
            </div>
            
            <div class="section">
                <div class="section-title">Scan SMS for Scams</div>
                <div class="input-group">
                    <textarea id="smsInput" placeholder="Paste suspicious SMS message here...">Congratulations! You have won 5,000,000 Naira! Call 08012345678 to claim your prize.</textarea>
                </div>
                <button class="btn btn-danger" onclick="checkSMS()">📱 Scan SMS for Fraud</button>
            </div>
            
            <div id="result" class="result">Ready to protect you from Nigerian fraud...</div>
        </div>
        
        <div id="premium-content" class="tab-content">
            <h2>Upgrade to CyberGuard Premium</h2>
            <p>Get advanced protection and unlimited scans</p>
            
            <div style="display: flex; gap: 20px; margin: 20px 0;">
                <div style="flex: 1; border: 2px solid #e1e5e9; padding: 20px; border-radius: 10px; text-align: center;">
                    <h3>Daily Premium</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #ffa000;">₦200</div>
                    <ul style="text-align: left; margin: 15px 0;">
                        <li>✓ Unlimited checks</li>
                        <li>✓ Advanced detection</li>
                        <li>✓ Detailed reports</li>
                    </ul>
                    <button class="btn btn-premium" onclick="showPayment('daily')">Get Daily Premium</button>
                </div>
                
                <div style="flex: 1; border: 2px solid #FFD700; padding: 20px; border-radius: 10px; text-align: center; background: #fffdf6;">
                    <h3>Weekly Premium</h3>
                    <div style="font-size: 2em; font-weight: bold; color: #ffa000;">₦1,000</div>
                    <ul style="text-align: left; margin: 15px 0;">
                        <li>✓ Everything in Daily</li>
                        <li>✓ 7 days access</li>
                        <li>✓ Save ₦400</li>
                    </ul>
                    <button class="btn btn-premium" onclick="showPayment('weekly')">Get Weekly Premium</button>
                </div>
            </div>
            
            <div id="paymentSection" style="display: none;">
                <h3>Complete Your Payment</h3>
                <p id="paymentInstructions"></p>
                <button class="btn btn-premium" onclick="completePayment()">I have paid - Activate Premium</button>
            </div>
        </div>
        
        <div id="account-content" class="tab-content">
            <h2>My Account</h2>
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <p><strong>Status:</strong> Free User</p>
                <p><strong>Checks Today:</strong> 0/5</p>
                <button class="btn btn-premium" onclick="switchTab('premium')">Upgrade to Premium</button>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            event.target.classList.add('active');
            document.getElementById(tabName + '-content').classList.add('active');
        }
        
        async function checkUSSD() {
            const code = document.getElementById('ussdInput').value;
            if (!code) return;
            
            try {
                const response = await fetch('/api/check-ussd', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code })
                });
                
                const result = await response.json();
                showResult(result);
            } catch (error) {
                showResult({
                    message: '❌ Network error. Please try again.',
                    type: 'warning'
                });
            }
        }
        
        async function checkSMS() {
            const sms = document.getElementById('smsInput').value;
            if (!sms) return;
            
            try {
                const response = await fetch('/api/check-sms', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sms: sms })
                });
                
                const result = await response.json();
                showResult(result);
            } catch (error) {
                showResult({
                    message: '❌ Network error. Please try again.',
                    type: 'warning'
                });
            }
        }
        
        function showResult(data) {
            const result = document.getElementById('result');
            result.textContent = data.message;
            result.className = 'result ' + data.type;
            result.style.display = 'block';
        }
        
        function showPayment(plan) {
            const plans = {
                'daily': 'Send ₦200 via bank transfer. WhatsApp proof to activate premium.',
                'weekly': 'Send ₦1,000 via bank transfer. WhatsApp proof to activate premium.'
            };
            
            document.getElementById('paymentInstructions').textContent = plans[plan];
            document.getElementById('paymentSection').style.display = 'block';
        }
        
        async function completePayment() {
            alert('🎉 Thank you! Contact us on WhatsApp with your payment proof to activate premium.');
        }
    </script>
</body>
</html>
    '''
    return html

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=False)
else:
    # For Vercel serverless
    application = app
