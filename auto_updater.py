#!/usr/bin/env python3
"""
Automated Safe List Updater v2.0
Enhanced with curated codes integration and multiple source support
"""
import requests
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
import re

logger = logging.getLogger("cyberguard")

class AutoUpdater:
    def __init__(self):
        self.data_dir = Path("data")
        self.safe_codes_file = self.data_dir / "safe_ussd_codes.txt"
        self.curated_codes_file = self.data_dir / "curated_codes.json"
        self.manual_sources_file = self.data_dir / "manual_sources.txt"
        self.stats_file = self.data_dir / "update_stats.json"
        self.last_update_file = self.data_dir / "last_update.txt"
        
        # Initialize files if they don't exist
        self.initialize_files()
    
    def initialize_files(self):
        """Initialize required files"""
        if not self.manual_sources_file.exists():
            self.manual_sources_file.write_text("# Add trusted USSD code sources here\n# One URL per line\n")
        
        if not self.stats_file.exists():
            self.stats_file.write_text("{}")
    
    def normalize_ussd(self, code: str):
        """Normalize USSD code format"""
        return code.strip().replace(" ", "").upper() if code else ""
    
    def get_trusted_sources(self):
        """Get trusted sources including curated database and external sources"""
        sources = []
        
        # 1. Primary source: Your curated database
        if self.curated_codes_file.exists():
            sources.append(f"file://{self.curated_codes_file.absolute()}")
        
        # 2. Manual sources from file
        if self.manual_sources_file.exists():
            with open(self.manual_sources_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip comments
                        sources.append(line)
        
        # 3. Fallback: Default safe codes file
        if self.safe_codes_file.exists():
            sources.append(f"file://{self.safe_codes_file.absolute()}")
        
        logger.info(f"Loaded {len(sources)} trusted sources")
        return sources
    
    def fetch_from_source(self, url: str) -> list:
        """Fetch USSD codes from a trusted source"""
        try:
            if url.startswith("file://"):
                # Local file processing
                file_path = Path(url[7:])
                if not file_path.exists():
                    logger.warning(f"File not found: {file_path}")
                    return []
                
                if file_path.suffix == '.json':
                    # JSON file (curated codes format)
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        # Extract codes from curated format
                        codes = []
                        for item in data:
                            if isinstance(item, dict) and 'code' in item:
                                codes.append(item['code'])
                            elif isinstance(item, str):
                                codes.append(item)
                        return codes
                    return []
                else:
                    # Text file (one code per line)
                    with open(file_path, 'r') as f:
                        return [line.strip() for line in f if line.strip()]
            
            else:
                # Remote URL
                logger.info(f"Fetching from remote source: {url}")
                response = requests.get(url, timeout=15, headers={
                    'User-Agent': 'CyberGuard-AutoUpdater/2.0'
                })
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    if 'application/json' in content_type:
                        # JSON response
                        data = response.json()
                        if isinstance(data, list):
                            return [item.get('code', item) if isinstance(item, dict) else str(item) 
                                   for item in data if item]
                    
                    # Text response (one code per line)
                    return [line.strip() for line in response.text.splitlines() if line.strip()]
                
                else:
                    logger.warning(f"HTTP {response.status_code} from {url}")
                    
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching from {url}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error fetching from {url}: {e}")
        except Exception as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
        
        return []
    
    def validate_ussd_code(self, code: str) -> bool:
        """Validate if a string is a properly formatted USSD code"""
        if not code or len(code) > 50:
            return False
        
        # Basic USSD pattern: * followed by digits/letters/symbols ending with #
        normalized = self.normalize_ussd(code)
        return bool(re.match(r"^\*[\d\*\#A-Za-z]+#?$", normalized))
    
    def should_update(self) -> bool:
        """Check if it's time to update (every 24 hours)"""
        try:
            if not self.last_update_file.exists():
                return True
            
            with open(self.last_update_file, 'r') as f:
                last_update = datetime.fromisoformat(f.read().strip())
            
            time_since_update = datetime.now() - last_update
            return time_since_update > timedelta(hours=24)
            
        except Exception as e:
            logger.warning(f"Error checking update timing: {e}")
            return True
    
    def load_existing_codes(self) -> set:
        """Load existing safe codes"""
        existing_codes = set()
        if self.safe_codes_file.exists():
            with open(self.safe_codes_file, 'r') as f:
                existing_codes = {self.normalize_ussd(line.strip()) for line in f if line.strip()}
        return existing_codes
    
    def update_safe_codes(self):
        """Main update function - enhanced with curated codes integration"""
        if not self.should_update():
            logger.info("Skipping update - recently updated")
            return {"skipped": True, "reason": "recently_updated"}
        
        logger.info("Starting automatic safe codes update")
        
        all_codes = set()
        stats = {
            "sources_checked": 0,
            "sources_successful": 0,
            "new_codes": 0,
            "total_codes": 0,
            "invalid_codes_filtered": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Load existing codes
        existing_codes = self.load_existing_codes()
        stats["existing_codes"] = len(existing_codes)
        
        # Fetch from all sources
        sources = self.get_trusted_sources()
        
        for source in sources:
            stats["sources_checked"] += 1
            try:
                new_codes = self.fetch_from_source(source)
                
                # Filter and validate codes
                valid_codes = set()
                for code in new_codes:
                    if self.validate_ussd_code(code):
                        valid_codes.add(self.normalize_ussd(code))
                    else:
                        stats["invalid_codes_filtered"] += 1
                
                if valid_codes:
                    stats["sources_successful"] += 1
                    all_codes.update(valid_codes)
                    logger.info(f"Fetched {len(valid_codes)} valid codes from {source}")
                else:
                    logger.warning(f"No valid codes from {source}")
                    
            except Exception as e:
                logger.error(f"Error processing source {source}: {e}")
        
        # Merge with existing codes
        merged_codes = existing_codes.union(all_codes)
        stats["new_codes"] = len(merged_codes) - len(existing_codes)
        stats["total_codes"] = len(merged_codes)
        
        # Save updated list
        with open(self.safe_codes_file, 'w') as f:
            f.write("\n".join(sorted(merged_codes)) + "\n")
        
        # Update timestamp
        with open(self.last_update_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        # Save detailed stats
        with open(self.stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"Update completed: {stats['new_codes']} new codes, total: {stats['total_codes']}")
        
        return stats
    
    def update_from_curated_database(self):
        """
        Special update function that ONLY uses curated database
        Use this when you want to force refresh from your curated data
        """
        logger.info("Updating safe codes exclusively from curated database")
        
        if not self.curated_codes_file.exists():
            logger.error("Curated database not found")
            return {"error": "curated_database_not_found"}
        
        try:
            with open(self.curated_codes_file, 'r') as f:
                curated_data = json.load(f)
            
            # Extract and validate codes
            safe_codes = set()
            invalid_count = 0
            
            for item in curated_data:
                if isinstance(item, dict) and 'code' in item:
                    code = item['code']
                elif isinstance(item, str):
                    code = item
                else:
                    continue
                
                if self.validate_ussd_code(code):
                    safe_codes.add(self.normalize_ussd(code))
                else:
                    invalid_count += 1
            
            # Save to safe USSD codes file
            with open(self.safe_codes_file, 'w') as f:
                f.write("\n".join(sorted(safe_codes)) + "\n")
            
            # Update timestamp
            with open(self.last_update_file, 'w') as f:
                f.write(datetime.now().isoformat())
            
            stats = {
                "source": "curated_database",
                "curated_codes_processed": len(curated_data),
                "valid_codes_extracted": len(safe_codes),
                "invalid_codes_filtered": invalid_count,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save stats
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"Curated update: {len(safe_codes)} codes from {len(curated_data)} curated entries")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to update from curated database: {e}")
            return {"error": str(e)}
    
    def get_update_stats(self):
        """Get the latest update statistics"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load update stats: {e}")
        
        return {"error": "no_stats_available"}
    
    def add_manual_source(self, url: str):
        """Add a new manual source to the sources file"""
        try:
            with open(self.manual_sources_file, 'a') as f:
                f.write(f"{url}\n")
            logger.info(f"Added manual source: {url}")
            return True
        except Exception as e:
            logger.error(f"Failed to add manual source: {e}")
            return False
    
    def list_manual_sources(self):
        """List all manual sources"""
        sources = []
        if self.manual_sources_file.exists():
            with open(self.manual_sources_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        sources.append(line)
        return sources
    
    def force_update(self):
        """Force an update regardless of timing"""
        # Temporarily remove last update file to force update
        if self.last_update_file.exists():
            self.last_update_file.unlink()
        
        return self.update_safe_codes()

# Global instance
auto_updater = AutoUpdater()

# Command line interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="CyberGuard Auto Updater")
    parser.add_argument('--update', action='store_true', help='Run standard update')
    parser.add_argument('--curated-only', action='store_true', help='Update only from curated database')
    parser.add_argument('--force', action='store_true', help='Force update regardless of timing')
    parser.add_argument('--stats', action='store_true', help='Show update statistics')
    parser.add_argument('--add-source', type=str, help='Add a new source URL')
    parser.add_argument('--list-sources', action='store_true', help='List all sources')
    
    args = parser.parse_args()
    
    if args.add_source:
        if auto_updater.add_manual_source(args.add_source):
            print(f"✓ Added source: {args.add_source}")
        else:
            print(f"✗ Failed to add source: {args.add_source}")
    
    elif args.list_sources:
        sources = auto_updater.list_manual_sources()
        print("Manual Sources:")
        for source in sources:
            print(f"  - {source}")
    
    elif args.stats:
        stats = auto_updater.get_update_stats()
        print("Update Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    elif args.curated_only:
        result = auto_updater.update_from_curated_database()
        print("Curated Database Update Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    elif args.force:
        result = auto_updater.force_update()
        print("Forced Update Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    elif args.update:
        result = auto_updater.update_safe_codes()
        print("Update Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    
    else:
        parser.print_help()
