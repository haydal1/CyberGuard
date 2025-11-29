# mobile_data_generator.py
#!/usr/bin/env python3
"""
Mobile Data Generator - Creates lightweight, optimized data for Android app
"""
import json
from pathlib import Path
from datetime import datetime

class MobileDataGenerator:
    def __init__(self):
        self.data_dir = Path("data")
        self.mobile_dir = Path("mobile_data")
        self.mobile_dir.mkdir(exist_ok=True)
    
    def generate_mobile_database(self):
        """Create ultra-compact mobile database"""
        
        # Core safe USSD codes (verified, essential only)
        safe_ussd_codes = [
            # Banking
            "*901#", "*902#", "*909#", "*911#", "*826#", "*989#", "*945#", "*322#",
            # Telecom
            "*123#", "*124#", "*232#", "*121#", "*310#", "*311#", "*312#", "*323#",
            # Services
            "*199#", "*#06#", "*#21#", "*#61#", "*#62#", "*#67#",
            # Common patterns
            "*123*1#", "*123*2#", "*123*4#", "*310*1#", "*311*1#"
        ]
        
        # High-confidence scam patterns
        scam_keywords = [
            "won", "win", "prize", "lottery", "million", "cash", "award", "claim",
            "urgent", "immediately", "bvn", "password", "pin", "transfer", "free",
            "gift", "congratulations", "congrats", "account", "verification"
        ]
        
        # Suspicious USSD patterns
        suspicious_patterns = [
            "*xxx*xxx*xxx*xxx#",  # Too many segments
            "*xxx*password*",     # Contains sensitive words
            "*xxx*bvn*",          # BVN requests
            "*xxx*pin*",          # PIN requests
            "*xxx*verif*"         # Verification requests
        ]
        
        # Create mobile-optimized database
        mobile_db = {
            "metadata": {
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
                "data_size": "compact",
                "total_codes": len(safe_ussd_codes),
                "total_keywords": len(scam_keywords)
            },
            "safe_ussd_codes": safe_ussd_codes,
            "scam_keywords": scam_keywords,
            "suspicious_patterns": suspicious_patterns,
            "rules": {
                "max_segments": 4,
                "suspicious_keywords": ["bvn", "pin", "password", "verif"],
                "safe_prefixes": ["*123", "*310", "*311", "*901", "*909"]
            }
        }
        
        # Save as minified JSON for Android
        mobile_file = self.mobile_dir / "ussd_database.json"
        with open(mobile_file, 'w') as f:
            json.dump(mobile_db, f, separators=(',', ':'))
        
        print(f"✅ Mobile database created: {mobile_file}")
        print(f"📊 Stats: {len(safe_ussd_codes)} safe codes, {len(scam_keywords)} scam patterns")
        print(f"📱 File size: {mobile_file.stat().st_size} bytes (Perfect for mobile!)")
        
        return mobile_db

# Run the generator
if __name__ == "__main__":
    generator = MobileDataGenerator()
    generator.generate_mobile_database()
