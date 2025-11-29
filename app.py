#!/usr/bin/env python3
"""
CyberMiniService - PRODUCTION READY v2.3
Enhanced with Manual Curation System, Bank API verification, Auto-updater, and ML detection
"""
import json
import datetime as dt
from pathlib import Path
import re, string, json, datetime, requests, hashlib, os, psutil, socket, logging, csv
from pathlib import Path
from typing import List, Dict
from fastapi import FastAPI, HTTPException, Query, Request, UploadFile, File
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from datetime import datetime

# --------------------------
# Enhanced Imports
# --------------------------
try:
    from bank_verification import bank_verifier
    from auto_updater import auto_updater
    from ml_detector import ml_detector
    ENHANCED_FEATURES = True
except ImportError as e:
    logging.warning(f"Enhanced features disabled: {e}")
    ENHANCED_FEATURES = False

# --------------------------
# Configuration
# --------------------------
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
DATA_DIR.mkdir(exist_ok=True)

# File paths
OFFLINE_SCAM_SMS = DATA_DIR / "scam_sms_keywords.txt"
OFFLINE_USSD_CODES = DATA_DIR / "safe_ussd_codes.txt"
COMMUNITY_REPORTS_DB = DATA_DIR / "community_reports.json"
BLACKLIST_USSD = DATA_DIR / "blacklist_ussd.txt"
USSD_CACHE = DATA_DIR / "ussd_cache.json"
LOG_FILE = BASE / "cyberguard.log"
CURATED_CODES_FILE = DATA_DIR / "curated_codes.json"

# Initialize files
for f in [OFFLINE_SCAM_SMS, OFFLINE_USSD_CODES, COMMUNITY_REPORTS_DB, BLACKLIST_USSD, USSD_CACHE, CURATED_CODES_FILE]:
    if not f.exists():
        if f == COMMUNITY_REPORTS_DB:
            f.write_text("[]")
        elif f == USSD_CACHE:
            f.write_text("{}")
        elif f == CURATED_CODES_FILE:
            f.write_text("[]")
        else:
            f.touch()

# Production settings
TRUSTED_USSD_SOURCE_URLS = []

# Comprehensive safe patterns for Nigerian context
SAFE_PREFIX_PATTERNS = [
    "*123", "*123*", "*310", "*311", "*312", "*323", "*321", "*131", "*404", "*606", "*244", "*244*", "*556",
    "*121", "*140", "*123", "*124", "*126", "*137", "*124", "*127", "*129", "*130", "*131", "*132", "*133",
    "*228", "*232", "*233", "*229", "*901", "*902", "*909", "*911", "*826", "*989", "*737", "*737*", "*779", "*779*",
    "*135", "*136", "*137", "*138", "*139", "*144", "*#21", "*#61", "*#62", "*#67", "*#06",
    "*199", "*770", "*894", "*329", "*565", "*326", "*24542", "*244*1", "*123*1", "*123*2", "*123*4"
]

NIGERIAN_LOCATIONS = {
    "Abuja": {"lat": 9.05785, "lon": 7.49508}, "Lagos": {"lat": 6.5244, "lon": 3.3792},
    "Port Harcourt": {"lat": 4.8156, "lon": 7.0498}, "Kano": {"lat": 12.0022, "lon": 8.5919},
    "Ibadan": {"lat": 7.3775, "lon": 3.9470}, "Jos": {"lat": 9.8965, "lon": 8.8583},
    "Enugu": {"lat": 6.4400, "lon": 7.4946}, "Abia": {"lat": 5.4541, "lon": 7.5153},
    "Nasarawa": {"lat": 8.5083, "lon": 8.5215}, "Kaduna": {"lat": 10.5105, "lon": 7.4165},
    "Makurdi": {"lat": 7.7325, "lon": 8.5391}
}

app = FastAPI(
    title="CyberGuard Production v2.3",
    description="Enhanced USSD/SMS Fraud Detection with Manual Curation & ML",
    version="2.3",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Production logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cyberguard")

# --------------------------
# Models
# --------------------------
class ReportRequest(BaseModel):
    report_type: str
    content: str
    location: str = None
    username: str = None

class UpdateReportStatus(BaseModel):
    index: int
    status: str
    action: str = None

class SyncRequest(BaseModel):
    urls: list[str] = None

class FeedbackRequest(BaseModel):
    ussd_code: str
    legitimate: bool

# Manual Curation Models
class CurationRequest(BaseModel):
    code: str
    type: str
    provider: str
    description: str = ""
    reference: str = ""

class BulkCurationRequest(BaseModel):
    codes: List[Dict]

class CodeActionRequest(BaseModel):
    index: int

class DeleteCodeRequest(BaseModel):
    code: str

# --------------------------
# Core Functions
# --------------------------
def is_online(timeout=2.0):
    try:
        requests.head("https://www.google.com", timeout=timeout)
        return True
    except:
        return False

def normalize_ussd(code: str):
    return code.strip().replace(" ", "") if code else ""

def load_lines(path: Path):
    try:
        with open(path, "r") as f:
            return [l.strip() for l in f if l.strip()]
    except:
        return []

def read_reports():
    try:
        return json.loads(COMMUNITY_REPORTS_DB.read_text())
    except:
        return []

def write_reports(reports):
    COMMUNITY_REPORTS_DB.write_text(json.dumps(reports, indent=2))

def load_safe_ussd():
    return {normalize_ussd(x) for x in load_lines(OFFLINE_USSD_CODES)}

def load_blacklist_ussd():
    return {normalize_ussd(x) for x in load_lines(BLACKLIST_USSD)}

def read_ussd_cache():
    try:
        return json.loads(USSD_CACHE.read_text())
    except:
        return {}

def write_ussd_cache(d):
    USSD_CACHE.write_text(json.dumps(d, indent=2))

def geocode_location(location: str):
    if not location: return None, None
    try:
        resp = requests.get("https://nominatim.openstreetmap.org/search",
                           params={"q": f"{location}, Nigeria", "format":"json", "limit":1},
                           headers={"User-Agent":"CyberGuard/2.3"}, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data: return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        pass
    loc = NIGERIAN_LOCATIONS.get(location.title())
    return (loc["lat"], loc["lon"]) if loc else (None, None)

# Manual Curation Functions
def load_curated_codes():
    """Load curated USSD codes"""
    try:
        return json.loads(CURATED_CODES_FILE.read_text())
    except:
        return []

def save_curated_codes(codes):
    """Save curated USSD codes"""
    CURATED_CODES_FILE.write_text(json.dumps(codes, indent=2))

def normalize_code(code: str):
    """Normalize USSD code for consistency"""
    return code.strip().replace(" ", "").upper()

def pattern_score_ussd(code: str):
    reasons, score = [], 0
    c = normalize_ussd(code)
    if not c: return 100, ["Empty code"]
    
    KNOWN_SAFE_CODES = {
        "*123#", "*123*1#", "*123*1*1#", "*123*2#", "*123*4#", "*310#", "*311#", "*312#", 
        "*321#", "*131#", "*121#", "*124#", "*228#", "*901#", "*902#", "*909#", "*911#", 
        "*826#", "*989#", "*737#", "*199#", "*#21#", "*#61#", "*#62#", "*#67#", "*#06#", 
        "*244*1#", "*24542#", "*232#", "*233#", "*322#", "*326#", "*329#", "*565#", "*126#"
    }
    
    if c in KNOWN_SAFE_CODES:
        return 0, ["Known safe telco/bank code"]

    if not re.match(r"^\*[\d\*\#A-Za-z]+#?$", c):
        reasons.append("Invalid USSD format"); score += 4

    is_known_safe = any(c.startswith(p) for p in SAFE_PREFIX_PATTERNS)
    if is_known_safe:
        score = max(0, score - 2)
        reasons.append("Known safe prefix")

    digits = re.sub(r"\D", "", c)
    if len(digits) >= 9:
        score += 6
        reasons.append(f"Long numeric sequence ({len(digits)} digits)")
    elif len(digits) >= 6:
        score += 2
        reasons.append("Moderate numeric sequence")

    high_risk_kw = ["bvn", "pin", "password", "passcode", "verif", "auth"]
    medium_risk_kw = ["account", "confirm", "secure", "update", "validate"]
    
    low = c.lower()
    for k in high_risk_kw:
        if k in low: score += 8; reasons.append(f"High-risk keyword: '{k}'")
    for k in medium_risk_kw:
        if k in low: score += 4; reasons.append(f"Medium-risk keyword: '{k}'")

    segments = re.sub(r"^\*|\#$", "", c).split("*")
    if len(segments) > 3:
        score += 3; reasons.append(f"Many segments ({len(segments)})")
    if len(set(segments)) <= 1 and len(segments) > 1:
        score += 4; reasons.append("Repeating segments")

    if re.search(r"[A-Za-z]", c) and not is_known_safe:
        score += 2; reasons.append("Contains letters")

    if not is_known_safe:
        score += 1; reasons.append("Unknown prefix")

    # CAP SCORE AT 10 - FIXED
    score = min(max(0, score), 10)
    
    return score, reasons

def improved_check_sms_scam(content: str):
    if not content: return {"scam": False, "confidence": 0, "reasons": []}
    
    if re.match(r"^\*[\d\*\#A-Za-z]+#?$", content.strip()):
        return {"scam": False, "confidence": 0, "reasons": ["USSD code detected"]}
    
    normalized = content.lower().translate(str.maketrans('', '', string.punctuation))
    words = normalized.split()
    
    # LEGITIMATE PATTERNS WHITELIST - FIXED
    legitimate_patterns = [
        r"your otp is \d{4,6}",  # OTP patterns
        r"verification code:?\s*\d+",  # Verification codes
        r"meeting at \d",  # Meeting reminders
        r"delivery (arriving|scheduled)",  # Delivery notifications
        r"hello,? how are you",  # Common greetings
    ]
    
    for pattern in legitimate_patterns:
        if re.search(pattern, normalized):
            return {"scam": False, "confidence": 0, "reasons": ["Legitimate communication pattern"]}
    
    scam_indicators = {
        # High confidence scam indicators
        "won": 4, "win": 4, "prize": 4, "lottery": 5, "million": 4, "cash": 3,
        "award": 3, "claim": 3, "urgent": 3, "immediately": 3, "verification": 2,  # Reduced OTP penalty
        "bvn": 6, "password": 5, "pin": 5, "transfer": 3, "free": 3,
        "gift": 3, "congratulations": 2, "congrats": 2, "account": 3, "bank": 2
    }
    
    # REDUCED OTP PENALTY - FIXED
    if "otp" in normalized and any(word in normalized for word in ["your", "code", "is", "verification"]):
        scam_indicators["otp"] = 1  # Much lower penalty in legitimate context
    else:
        scam_indicators["otp"] = 3  # Normal penalty in suspicious context
    
    score, reasons, triggered = 0, [], []
    for word in words:
        if word in scam_indicators:
            score += scam_indicators[word]
            triggered.append(word)
    
    if triggered: 
        reasons.append(f"Suspicious words: {', '.join(triggered)}")
    
    patterns = [
        (r"you.*won.*\d+", 6, "Winning announcement"),
        (r"call.*\d{8,}", 5, "Unknown number request"),
        (r"click.*http", 5, "Suspicious link"),
        (r"account.*verif", 4, "Account verification"),  # Reduced penalty
        (r"free.*gift", 4, "Free gift offer"),
        (r"your.*bvn", 6, "BVN request")
    ]
    
    for pattern, points, reason in patterns:
        if re.search(pattern, normalized):
            score += points
            reasons.append(reason)
    
    # Single word "congratulations" shouldn't be enough
    if len(words) == 1 and words[0] in ["congratulations", "congrats"]:
        score = max(score - 3, 0)
        reasons = ["Single word - needs context"]
    
    # CAP CONFIDENCE AT 10 - FIXED
    confidence = min(score, 10)
    scam = score >= 6
    
    return {
        "content": content, "scam": scam, 
        "confidence": confidence, "score": score, "reasons": reasons
    }

def online_verify_ussd(code: str, urls: list=None):
    urls = urls or TRUSTED_USSD_SOURCE_URLS
    if not urls: return False, None
    norm = normalize_ussd(code).lower()
    for u in urls:
        try:
            r = requests.get(u, timeout=8)
            if r.status_code == 200 and norm in r.text.lower():
                return True, u
        except: continue
    return False, None

# --------------------------
# Enhanced Functions
# --------------------------
def calculate_enhanced_score(basic, bank, ml):
    """Calculate enhanced confidence score"""
    base_score = basic.get("score", 0)
    
    # Bank verification boosts confidence
    if bank["verified"]:
        base_score = max(0, base_score - 3)
    
    # ML confidence adjustment
    if ml["legitimate"] and ml["confidence"] > 0.7:
        base_score = max(0, base_score - 2)
    elif not ml["legitimate"] and ml["confidence"] > 0.7:
        base_score = min(10, base_score + 2)
    
    return min(10, base_score)

# --------------------------
# API Endpoints
# --------------------------

@app.post("/admin/add-source")
def add_source(url: str):
    """Add a new trusted source"""
    success = auto_updater.add_manual_source(url)
    return {"message": "Source added" if success else "Failed to add source"}

@app.get("/admin/list-sources")
def list_sources():
    """List all trusted sources"""
    return {"sources": auto_updater.list_manual_sources()}

@app.post("/admin/update-safe-codes")
def update_safe_codes(mode: str = "standard"):
    """Enhanced safe codes update with different modes"""
    if mode == "curated-only":
        stats = auto_updater.update_from_curated_database()
    elif mode == "force":
        stats = auto_updater.force_update()
    else:
        stats = auto_updater.update_safe_codes()
    
    return {"message": "Update completed", "mode": mode, "stats": stats}

@app.get("/admin/update-stats")
def get_update_stats():
    """Get update statistics"""
    return auto_updater.get_update_stats()

@app.get("/")
async def root():
    enhanced_status = "enabled" if ENHANCED_FEATURES else "disabled"
    return {
        "message": "CyberGuard API v2.3", 
        "version": "2.3", 
        "status": "active",
        "enhanced_features": enhanced_status
    }

@app.get("/check-ussd")
def check_ussd(code: str = Query(...), full_mode: bool = Query(False)):
    """
    Standard USSD check endpoint
    """
    if not code: raise HTTPException(400, "USSD code required")
    
    norm = normalize_ussd(code)
    safe_set, blacklist, cache = load_safe_ussd(), load_blacklist_ussd(), read_ussd_cache()
    
    if norm in blacklist:
        return {"code": norm, "safe": False, "score": 10, "reasons": ["Blacklisted"], "verified_online": False, "cached": False}
    
    if norm in cache:
        entry = cache[norm]
        return {"code": norm, "safe": entry.get("safe", False), "score": entry.get("score", 0),
                "reasons": entry.get("reasons", []), "verified_online": entry.get("verified_online", False),
                "source": entry.get("source"), "cached": True}

    if norm in safe_set:
        score, reasons = pattern_score_ussd(norm)
        result = {"code": norm, "safe": True, "score": score, "reasons": reasons + ["In safe list"], "verified_online": False, "cached": False}
        if full_mode and is_online():
            v, src = online_verify_ussd(norm)
            if v: 
                result.update({"verified_online": True, "source": src})
                cache[norm] = {"safe": True, "score": score, "reasons": reasons, "verified_online": True, "source": src}
                write_ussd_cache(cache)
        return result

    score, reasons = pattern_score_ussd(norm)
    safe = score < 5
    verified_online, source = False, None
    
    if full_mode and is_online():
        v, src = online_verify_ussd(norm)
        verified_online, source = v, src
        if v:
            safe = True
            reasons.append(f"Verified by {src}")
            cache[norm] = {"safe": True, "score": score, "reasons": reasons, "verified_online": True, "source": src}
            write_ussd_cache(cache)
            return {"code": norm, "safe": True, "score": score, "reasons": reasons, "verified_online": True, "source": src, "cached": True}

    return {"code": norm, "safe": safe, "score": score, "reasons": reasons, "verified_online": verified_online, "source": source, "cached": False}

@app.get("/check-ussd-enhanced")
def check_ussd_enhanced(code: str = Query(...), full_mode: bool = Query(False)):
    """
    Enhanced USSD check with bank verification and ML
    """
    if not code:
        raise HTTPException(400, "USSD code required")
    
    if not ENHANCED_FEATURES:
        raise HTTPException(503, "Enhanced features not available. Please install ML dependencies.")
    
    norm = normalize_ussd(code)
    
    # 1. Traditional checks
    basic_result = check_ussd(code, full_mode)
    
    # 2. Bank API verification
    bank_verification = bank_verifier.verify_ussd_code(norm)
    
    # 3. ML pattern analysis
    ml_analysis = ml_detector.predict_legitimate(norm)
    
    # Combine results
    enhanced_result = {
        **basic_result,
        "bank_verified": bank_verification["verified"],
        "bank_source": bank_verification["source"],
        "bank_name": bank_verification["bank"],
        "ml_legitimate": ml_analysis["legitimate"],
        "ml_confidence": ml_analysis["confidence"],
        "enhanced_score": calculate_enhanced_score(basic_result, bank_verification, ml_analysis),
        "enhanced_features": True
    }
    
    return enhanced_result

@app.get("/check-sms-scam")
def check_sms_scam(content: str = Query(...)):
    """Improved SMS scam detection endpoint"""
    return improved_check_sms_scam(content)

@app.post("/community/report")
def submit_report(report: ReportRequest):
    reports = read_reports()
    lat, lon = geocode_location(report.location)
    entry = {
        "report_type": report.report_type, "content": report.content,
        "location": report.location or "Unknown", "username": report.username or "Anonymous",
        "timestamp": datetime.datetime.now().isoformat(), "status": "Pending", "lat": lat, "lon": lon
    }
    reports.append(entry)
    write_reports(reports)
    logger.info(f"New report: {report.report_type} from {report.location}")
    return {"message": "Report submitted", "report": entry}

@app.get("/community/reports")
def get_reports(status: str = None):
    reports = read_reports()
    if status: reports = [r for r in reports if r.get("status","").lower() == status.lower()]
    return {"reports": reports}

@app.post("/community/update-report")
def update_report_status(data: UpdateReportStatus):
    reports = read_reports()
    if data.index < 0 or data.index >= len(reports):
        raise HTTPException(400, "Invalid report index")
    reports[data.index]["status"] = data.status
    if data.action == "add_safe":
        code = normalize_ussd(reports[data.index]["content"])
        safe = load_safe_ussd()
        if code not in safe:
            with open(OFFLINE_USSD_CODES, "a") as fh:
                fh.write(code + "\n")
    if data.action == "add_blacklist":
        code = normalize_ussd(reports[data.index]["content"])
        bl = load_blacklist_ussd()
        if code not in bl:
            with open(BLACKLIST_USSD, "a") as fh:
                fh.write(code + "\n")
    write_reports(reports)
    return {"message": "Report updated", "report": reports[data.index]}

@app.post("/admin/sync-ussd")
def sync_ussd(req: SyncRequest):
    urls = req.urls or TRUSTED_USSD_SOURCE_URLS
    if not urls: raise HTTPException(400, "No URLs configured")
    fetched = set()
    for u in urls:
        try:
            r = requests.get(u, timeout=10)
            if r.status_code == 200:
                for ln in r.text.splitlines():
                    cand = ln.strip()
                    if cand and re.search(r"^\*\d[\d\*#A-Za-z]+\#?$", normalize_ussd(cand)):
                        fetched.add(normalize_ussd(cand))
        except: continue
    if not fetched: return {"message": "No codes fetched", "fetched": []}
    safe = load_safe_ussd()
    merged = sorted(set(list(safe) + list(fetched)))
    with open(OFFLINE_USSD_CODES, "w") as fh:
        fh.write("\n".join(merged) + "\n")
    logger.info(f"Synced {len(merged)} USSD codes")
    return {"message": "Synced USSD list", "added": len(merged) - len(safe), "total": len(merged)}

@app.post("/admin/trigger-update")
def trigger_update():
    """Manually trigger safe list update"""
    if not ENHANCED_FEATURES:
        raise HTTPException(503, "Enhanced features not available")
    
    stats = auto_updater.update_safe_codes()
    return {"message": "Update completed", "stats": stats}

@app.post("/feedback/ussd")
def submit_ussd_feedback(feedback: FeedbackRequest):
    """Submit feedback to improve ML model"""
    if not ENHANCED_FEATURES:
        raise HTTPException(503, "Enhanced features not available")
    
    ml_detector.learn_from_feedback(feedback.ussd_code, feedback.legitimate)
    return {"message": "Feedback recorded for ML model improvement"}

# --------------------------
# Manual Curation Endpoints
# --------------------------
@app.get("/curation/stats")
def get_curation_stats():
    """Get curation statistics"""
    curated_codes = load_curated_codes()
    reports = read_reports()
    
    bank_codes = [c for c in curated_codes if c.get("type") == "bank"]
    pending_reports = [r for r in reports if r.get("status") == "Pending" and r.get("report_type") == "ussd"]
    
    return {
        "total_codes": len(curated_codes),
        "verified_codes": len(curated_codes),
        "bank_codes": len(bank_codes),
        "pending_reports": len(pending_reports)
    }

@app.get("/curation/codes")
def get_curated_codes():
    """Get all curated codes"""
    return load_curated_codes()

@app.get("/curation/pending")
def get_pending_reports():
    """Get pending USSD reports for curation"""
    reports = read_reports()
    pending = [
        {**report, "index": i} 
        for i, report in enumerate(reports) 
        if report.get("status") == "Pending" and report.get("report_type") == "ussd"
    ]
    return pending

@app.post("/curation/add")
def add_curated_code(request: CurationRequest):
    """Add a single curated code"""
    curated_codes = load_curated_codes()
    
    # Check if code already exists
    normalized_code = normalize_code(request.code)
    existing = any(normalize_code(c["code"]) == normalized_code for c in curated_codes)
    
    if existing:
        raise HTTPException(400, "Code already exists in database")
    
    # Add new code
    new_code = {
        "code": request.code,
        "type": request.type,
        "provider": request.provider,
        "description": request.description,
        "reference": request.reference,
        "added_by": "admin",
        "timestamp": datetime.datetime.now().isoformat(),
        "verified": True
    }
    
    curated_codes.append(new_code)
    save_curated_codes(curated_codes)
    
    # Also add to safe USSD codes file
    safe_codes = load_safe_ussd()
    if normalized_code not in safe_codes:
        with open(OFFLINE_USSD_CODES, "a") as f:
            f.write(normalized_code + "\n")
    
    logger.info(f"Added curated code: {request.code}")
    return {"message": f"Code {request.code} added successfully"}

@app.post("/curation/bulk-add")
def bulk_add_codes(request: BulkCurationRequest):
    """Bulk add curated codes"""
    curated_codes = load_curated_codes()
    added_count = 0
    
    for code_data in request.codes:
        normalized_code = normalize_code(code_data["code"])
        
        # Skip if already exists
        if any(normalize_code(c["code"]) == normalized_code for c in curated_codes):
            continue
        
        new_code = {
            "code": code_data["code"],
            "type": code_data.get("type", "other"),
            "provider": code_data.get("provider", "Unknown"),
            "description": code_data.get("description", ""),
            "reference": "bulk_import",
            "added_by": "admin",
            "timestamp": datetime.datetime.now().isoformat(),
            "verified": True
        }
        
        curated_codes.append(new_code)
        
        # Add to safe USSD codes
        safe_codes = load_safe_ussd()
        if normalized_code not in safe_codes:
            with open(OFFLINE_USSD_CODES, "a") as f:
                f.write(normalized_code + "\n")
        
        added_count += 1
    
    save_curated_codes(curated_codes)
    logger.info(f"Bulk added {added_count} codes")
    return {"message": f"Added {added_count} new codes"}

@app.post("/curation/approve-report")
def approve_report(request: CodeActionRequest):
    """Approve a community report and add to curated codes"""
    reports = read_reports()
    
    if request.index < 0 or request.index >= len(reports):
        raise HTTPException(400, "Invalid report index")
    
    report = reports[request.index]
    if report.get("report_type") != "ussd":
        raise HTTPException(400, "Not a USSD report")
    
    # Add to curated codes
    curated_codes = load_curated_codes()
    normalized_code = normalize_code(report["content"])
    
    if not any(normalize_code(c["code"]) == normalized_code for c in curated_codes):
        new_code = {
            "code": report["content"],
            "type": "community_verified",
            "provider": "Community Verified",
            "description": f"Verified from community report by {report.get('username', 'Anonymous')}",
            "reference": "community_report",
            "added_by": report.get("username", "Anonymous"),
            "timestamp": datetime.datetime.now().isoformat(),
            "verified": True
        }
        curated_codes.append(new_code)
        save_curated_codes(curated_codes)
        
        # Add to safe USSD codes
        safe_codes = load_safe_ussd()
        if normalized_code not in safe_codes:
            with open(OFFLINE_USSD_CODES, "a") as f:
                f.write(normalized_code + "\n")
    
    # Update report status
    reports[request.index]["status"] = "Verified"
    write_reports(reports)
    
    logger.info(f"Approved community report: {report['content']}")
    return {"message": "Report approved and code added to database"}

@app.post("/curation/reject-report")
def reject_report(request: CodeActionRequest):
    """Reject a community report"""
    reports = read_reports()
    
    if request.index < 0 or request.index >= len(reports):
        raise HTTPException(400, "Invalid report index")
    
    reports[request.index]["status"] = "Rejected"
    write_reports(reports)
    
    logger.info(f"Rejected community report")
    return {"message": "Report rejected"}

@app.delete("/curation/delete")
def delete_curated_code(request: DeleteCodeRequest):
    """Delete a curated code"""
    curated_codes = load_curated_codes()
    normalized_target = normalize_code(request.code)
    
    # Remove from curated codes
    filtered_codes = [c for c in curated_codes if normalize_code(c["code"]) != normalized_target]
    
    if len(filtered_codes) == len(curated_codes):
        raise HTTPException(404, "Code not found in database")
    
    save_curated_codes(filtered_codes)
    
    logger.info(f"Deleted curated code: {request.code}")
    return {"message": f"Code {request.code} deleted successfully"}

@app.get("/curation/export")
def export_curated_codes(format: str = "json"):
    """Export curated codes in various formats"""
    curated_codes = load_curated_codes()
    
    if format == "json":
        content = json.dumps(curated_codes, indent=2)
        media_type = "application/json"
    elif format == "csv":
        output = ["code,type,provider,description,reference,added_by,timestamp"]
        for code in curated_codes:
            row = [
                code["code"],
                code["type"],
                code["provider"].replace(",", ";"),
                code["description"].replace(",", ";").replace("\n", " "),
                code.get("reference", "").replace(",", ";"),
                code.get("added_by", "").replace(",", ";"),
                code.get("timestamp", "")
            ]
            output.append(",".join(f'"{field}"' for field in row))
        content = "\n".join(output)
        media_type = "text/csv"
    elif format == "txt":
        content = "\n".join([f"{code['code']} - {code['provider']} ({code['type']})" for code in curated_codes])
        media_type = "text/plain"
    else:
        raise HTTPException(400, "Unsupported format")
    
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename=ussd-codes.{format}"}
    )

@app.post("/curation/import-file")
async def import_codes_from_file(file: UploadFile = File(...)):
    """Import codes from uploaded file"""
    content = await file.read()
    
    try:
        if file.filename.endswith('.json'):
            codes = json.loads(content)
        elif file.filename.endswith('.csv'):
            csv_content = content.decode('utf-8').splitlines()
            reader = csv.DictReader(csv_content)
            codes = list(reader)
        else:
            # Treat as text file
            lines = content.decode('utf-8').splitlines()
            codes = [{"code": line.strip(), "type": "imported", "provider": "Imported"} for line in lines if line.strip()]
        
        # Process imported codes
        curated_codes = load_curated_codes()
        added_count = 0
        
        for code_data in codes:
            if isinstance(code_data, dict):
                normalized_code = normalize_code(code_data.get("code", ""))
                if normalized_code and not any(normalize_code(c["code"]) == normalized_code for c in curated_codes):
                    new_code = {
                        "code": code_data.get("code"),
                        "type": code_data.get("type", "imported"),
                        "provider": code_data.get("provider", "Imported"),
                        "description": code_data.get("description", "Imported from file"),
                        "reference": "file_import",
                        "added_by": "admin",
                        "timestamp": datetime.datetime.now().isoformat(),
                        "verified": True
                    }
                    curated_codes.append(new_code)
                    added_count += 1
        
        save_curated_codes(curated_codes)
        return {"message": f"Imported {added_count} new codes from file"}
        
    except Exception as e:
        raise HTTPException(400, f"Failed to import file: {str(e)}")

@app.get("/curation/dashboard")
def curation_dashboard():
    """Serve the curation dashboard"""
    p = BASE / "admin_dashboard.html"
    if p.exists():
        return FileResponse(p)
    raise HTTPException(404, "Curation dashboard not found")

@app.get("/device-checklist")
def device_checklist():
    return {
        "cpu_cores": psutil.cpu_count(),
        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "disk_gb": round(psutil.disk_usage('/').total / (1024**3), 2),
        "platform": os.name,
    }

@app.get("/check-password")
def check_password(password: str = Query(...)):
    h = hashlib.sha1(password.encode()).hexdigest().upper()
    try:
        resp = requests.get(f"https://api.pwnedpasswords.com/range/{h[:5]}", timeout=8)
        lines = (ln.split(":") for ln in resp.text.splitlines())
        count = sum(int(c) for hh,c in lines if hh == h[5:])
        return {"password": password, "pwned_count": count, "safe": count == 0}
    except:
        return {"password": password, "pwned_count": -1, "safe": False}

@app.get("/health")
def health_check():
    enhanced_status = "enabled" if ENHANCED_FEATURES else "disabled"
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.3", 
        "online": is_online(), 
        "cache_size": len(read_ussd_cache()),
        "reports_count": len(read_reports()),
        "enhanced_features": enhanced_status
    }

@app.get("/system/info")
def system_info():
    """Get system information including enhanced features status"""
    enhanced_status = {
        "bank_verification": ENHANCED_FEATURES,
        "auto_updater": ENHANCED_FEATURES,
        "ml_detection": ENHANCED_FEATURES,
        "manual_curation": True,  # Always available
        "dependencies_installed": ENHANCED_FEATURES
    }
    
    return {
        "version": "2.3",
        "enhanced_features": enhanced_status,
        "standard_endpoints": [
            "/check-ussd", "/check-sms-scam", "/community/report", "/health"
        ],
        "curation_endpoints": [
            "/curation/dashboard", "/curation/stats", "/curation/add", 
            "/curation/bulk-add", "/curation/export"
        ],
        "enhanced_endpoints": [
            "/check-ussd-enhanced", "/admin/trigger-update", "/feedback/ussd"
        ] if ENHANCED_FEATURES else ["Not available - install ML dependencies"]
    }

@app.get("/dashboard")
def dashboard():
    p = BASE / "dashboard.html"
    if p.exists(): return FileResponse(p)
    raise HTTPException(404, "Dashboard not found")

# =====================
# MOBILE ENDPOINTS - FIXED VERSION
# =====================

@app.get("/mobile/database")
def get_mobile_database():
    """Ultra-lightweight database for mobile apps"""
    try:
        mobile_file = Path("mobile_data/ussd_database.json")
        if mobile_file.exists():
            return FileResponse(mobile_file, media_type="application/json")
        raise HTTPException(404, "Mobile database not found")
    except Exception as e:
        logger.error(f"Mobile database error: {e}")
        raise HTTPException(500, "Internal server error")

@app.get("/mobile/check")
def mobile_check_ussd(code: str = Query(...)):
    """Fast USSD check for mobile - simplified logic"""
    try:
        normalized = normalize_ussd(code)
        
        # Ultra-fast local check only
        safe_codes = load_safe_ussd()
        if normalized in safe_codes:
            return {"safe": True, "reason": "known_safe", "confidence": 95}
        
        # Basic pattern check
        score, reasons = pattern_score_ussd(code)
        
        return {
            "safe": score < 6,
            "score": score,
            "reasons": reasons[:3],  # Limit for mobile
            "confidence": max(0, 100 - (score * 10))
        }
    except Exception as e:
        logger.error(f"Mobile check error: {e}")
        return {"safe": False, "error": "check_failed", "confidence": 0}

@app.post("/mobile/report")
def mobile_report_scam(
    code: str = Query(None), 
    message: str = Query(None), 
    report_type: str = Query("unknown")
):
    """Minimal report endpoint - Enhanced file handling"""
    try:
        # Simple timestamp without datetime issues
        import time
        timestamp = int(time.time())
        report_id = abs(hash(f"{code}{message}{timestamp}")) % 1000000
        
        report = {
            "type": report_type,
            "content": code or message or "unknown",
            "timestamp": timestamp,
            "source": "mobile_app",
            "id": report_id
        }
        
        # Ensure data directory exists
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Append to mobile reports file
        mobile_reports_file = data_dir / "mobile_reports.jsonl"
        
        with open(mobile_reports_file, 'a') as f:
            f.write(json.dumps(report) + '\n')
        
        print(f"✅ Report saved: {report}")  # Debug output
        
        return {"status": "received", "id": report_id}
    
    except Exception as e:
        print(f"❌ Report error: {e}")  # Debug output
        return {"status": "error", "message": str(e)}

@app.get("/mobile/stats")
def mobile_stats():
    """Get mobile app statistics - FIXED"""
    try:
        mobile_file = Path("mobile_data/ussd_database.json")
        if mobile_file.exists():
            with open(mobile_file, 'r') as f:
                data = json.load(f)
            return {
                "database_version": data.get("metadata", {}).get("version", "unknown"),
                "safe_codes_count": len(data.get("safe_ussd_codes", [])),
                "scam_patterns_count": len(data.get("scam_keywords", [])),
                "last_updated": data.get("metadata", {}).get("generated_at", "unknown")
            }
        return {"error": "mobile_database_not_found"}
    
    except json.JSONDecodeError as e:
        logger.error(f"Mobile stats JSON error: {e}")
        return {"error": "database_corrupted", "message": "Mobile database file is corrupted"}
    except Exception as e:
        logger.error(f"Mobile stats error: {e}")
        return {"error": "internal_error", "message": str(e)}

@app.get("/mobile/reports/debug")
def debug_mobile_reports():
    """Debug endpoint to check mobile reports"""
    try:
        mobile_reports_file = Path("data/mobile_reports.jsonl")
        
        if not mobile_reports_file.exists():
            return {
                "status": "no_reports",
                "message": "No reports file found",
                "file_exists": False,
                "data_directory": str(Path("data").absolute()),
                "files_in_data": [f.name for f in Path("data").iterdir()] if Path("data").exists() else []
            }
        
        # Read and parse reports
        with open(mobile_reports_file, 'r') as f:
            reports = [json.loads(line) for line in f if line.strip()]
        
        return {
            "status": "success",
            "file_exists": True,
            "file_path": str(mobile_reports_file.absolute()),
            "total_reports": len(reports),
            "reports": reports[-5:],  # Last 5 reports
            "file_size_bytes": mobile_reports_file.stat().st_size
        }
    
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Production entry point
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        workers=4,
        access_log=True,
        timeout_keep_alive=5
    )
