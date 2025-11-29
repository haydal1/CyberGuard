#!/usr/bin/env python3
"""
Cron job script for automated maintenance
Run this daily via system cron
"""
import logging
from auto_updater import auto_updater
from ml_detector import ml_detector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cyberguard-cron")

def daily_maintenance():
    """Daily maintenance tasks"""
    logger.info("Starting daily maintenance")
    
    # 1. Update safe codes
    update_stats = auto_updater.update_safe_codes()
    
    # 2. Retrain ML model if enough new data
    ml_detector.retrain_if_needed()
    
    # 3. Cleanup old cache entries
    # Add cleanup logic here
    
    logger.info("Daily maintenance completed")
    return update_stats

if __name__ == "__main__":
    daily_maintenance()
