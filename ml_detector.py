#!/usr/bin/env python3
"""
Machine Learning Pattern Detection
AI-powered legitimate pattern recognition
"""
import re
import json
import logging
from pathlib import Path
from collections import Counter
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib

logger = logging.getLogger("cyberguard")

class MLPatternDetector:
    def __init__(self):
        self.model_file = Path("data/ml_model.joblib")
        self.vectorizer_file = Path("data/vectorizer.joblib")
        self.training_data_file = Path("data/training_data.json")
        self.model = None
        self.vectorizer = None
        self.load_model()
    
    def load_model(self):
        """Load trained ML model"""
        try:
            if self.model_file.exists() and self.vectorizer_file.exists():
                self.model = joblib.load(self.model_file)
                self.vectorizer = joblib.load(self.vectorizer_file)
                logger.info("ML model loaded successfully")
            else:
                self.train_initial_model()
        except Exception as e:
            logger.warning(f"Failed to load ML model: {e}")
            self.train_initial_model()
    
    def extract_features(self, text):
        """Extract features from text for ML analysis"""
        features = {}
        
        # Structural features
        features['length'] = len(text)
        features['digit_count'] = len(re.findall(r'\d', text))
        features['star_count'] = text.count('*')
        features['hash_count'] = text.count('#')
        
        # Pattern features
        features['has_bank_pattern'] = bool(re.match(r'^\*9[0-9]{2}#$', text))
        features['has_telco_pattern'] = bool(re.match(r'^\*[0-9]{3}#$', text))
        features['has_service_pattern'] = bool(re.match(r'^\*#[0-9]{2}#$', text))
        
        # Keyword features
        risky_keywords = ['bvn', 'pin', 'password', 'verify', 'otp', 'account']
        safe_keywords = ['balance', 'transfer', 'airtime', 'data', 'minutes']
        
        text_lower = text.lower()
        features['risky_keyword_count'] = sum(1 for kw in risky_keywords if kw in text_lower)
        features['safe_keyword_count'] = sum(1 for kw in safe_keywords if kw in text_lower)
        
        return features
    
    def train_initial_model(self):
        """Train initial ML model with sample data"""
        logger.info("Training initial ML model...")
        
        # Sample training data (legitimate USSD patterns)
        training_data = [
            # Legitimate patterns
            ("*901#", 1), ("*902#", 1), ("*909#", 1), ("*123#", 1), ("*310#", 1),
            ("*311#", 1), ("*121#", 1), ("*131#", 1), ("*126#", 1), ("*232#", 1),
            
            # Suspicious patterns  
            ("*123*bvn*12345678901#", 0), ("*pin*1234*account#", 0),
            ("*635337467*2#", 0), ("*97645756*2#", 0),
        ]
        
        texts, labels = zip(*training_data)
        
        # Extract features
        features = [list(self.extract_features(text).values()) for text in texts]
        
        # Train model
        from sklearn.ensemble import RandomForestClassifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(features, labels)
        
        # Save model
        self.save_model()
        logger.info("Initial ML model trained and saved")
    
    def save_model(self):
        """Save trained model"""
        try:
            self.model_file.parent.mkdir(exist_ok=True)
            joblib.dump(self.model, self.model_file)
            logger.info("ML model saved successfully")
        except Exception as e:
            logger.error(f"Failed to save ML model: {e}")
    
    def predict_legitimate(self, ussd_code: str) -> dict:
        """
        Predict if USSD code is legitimate using ML
        Returns: {"legitimate": bool, "confidence": float, "features": dict}
        """
        try:
            if self.model is None:
                return {"legitimate": False, "confidence": 0.5, "features": {}}
            
            features = self.extract_features(ussd_code)
            feature_vector = [list(features.values())]
            
            prediction = self.model.predict(feature_vector)[0]
            probability = self.model.predict_proba(feature_vector)[0][1]  # Probability of legitimate
            
            return {
                "legitimate": bool(prediction),
                "confidence": float(probability),
                "features": features
            }
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return {"legitimate": False, "confidence": 0.5, "features": {}}
    
    def learn_from_feedback(self, ussd_code: str, is_legitimate: bool):
        """
        Learn from user feedback to improve model
        """
        try:
            # Load existing training data
            training_data = []
            if self.training_data_file.exists():
                with open(self.training_data_file, 'r') as f:
                    training_data = json.load(f)
            
            # Add new example
            training_data.append({
                "code": ussd_code,
                "legitimate": is_legitimate,
                "timestamp": datetime.now().isoformat()
            })
            
            # Keep only recent data (last 1000 examples)
            training_data = training_data[-1000:]
            
            # Save updated training data
            with open(self.training_data_file, 'w') as f:
                json.dump(training_data, f, indent=2)
            
            # Retrain model periodically
            if len(training_data) % 100 == 0:  # Retrain every 100 new examples
                self.retrain_model(training_data)
                
        except Exception as e:
            logger.error(f"Failed to learn from feedback: {e}")

# Global instance
ml_detector = MLPatternDetector()
