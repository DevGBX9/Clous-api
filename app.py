#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - ULTIMATE STEALTH Edition
======================================================

Maximum stealth with all protection levels:
- Level 1: Simple usernames, random delays
- Level 2: Session persistence, human-like timing
- Level 3: Smart proxy rotation, enhanced fingerprints

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4
from dataclasses import dataclass, field

import httpx
from flask import Flask, jsonify
from flask_cors import CORS

sys.dont_write_bytecode = True

# ==========================================
#              LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
#              CONFIG
# ==========================================
CONFIG = {
    "API_URL": 'https://i.instagram.com/api/v1/users/check_username/',
    "TIMEOUT": 90,  # Increased timeout for more attempts
    "REQUEST_TIMEOUT": 10.0,  # Slightly increased for stability
    "PROXIES_FILE": "proxies.txt",
    
    # Speed settings (OPTIMIZED)
    "MIN_DELAY": 0.3,       # Reduced for faster batches
    "MAX_DELAY": 1.2,       # Reduced for faster batches
    "MAX_CONCURRENT": 40,   # Increased for more parallel requests
    "COOLDOWN_TIME": 45,    # Increased cooldown for better recovery
    "TYPING_SIMULATION": True,
    
    # Smart proxy management
    "MAX_REQUESTS_PER_PROXY": 8,  # Max requests before forcing rest
    "PROXY_REST_TIME": 20,         # Seconds to rest after max requests
    "ENABLE_SMART_ROTATION": True, # Enable intelligent proxy rotation
}

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# Extended Android devices database (EXPANDED for more diversity)
DEVICES = [
    # Samsung Galaxy S Series
    {"manufacturer": "Samsung", "model": "SM-G998B", "device": "p3s", "board": "exynos2100", "android": 13, "dpi": 640, "res": "1440x3200", "country": "US"},
    {"manufacturer": "Samsung", "model": "SM-S908B", "device": "b0q", "board": "exynos2200", "android": 14, "dpi": 600, "res": "1440x3088", "country": "GB"},
    {"manufacturer": "Samsung", "model": "SM-S918B", "device": "dm3q", "board": "exynos2300", "android": 14, "dpi": 640, "res": "1440x3088", "country": "DE"},
    {"manufacturer": "Samsung", "model": "SM-G991B", "device": "o1s", "board": "exynos2100", "android": 13, "dpi": 480, "res": "1080x2400", "country": "FR"},
    
    # Samsung Galaxy A Series
    {"manufacturer": "Samsung", "model": "SM-A536B", "device": "a53x", "board": "exynos1280", "android": 13, "dpi": 450, "res": "1080x2400", "country": "IT"},
    {"manufacturer": "Samsung", "model": "SM-A525F", "device": "a52q", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2340", "country": "ES"},
    {"manufacturer": "Samsung", "model": "SM-A546B", "device": "a54x", "board": "exynos1380", "android": 14, "dpi": 480, "res": "1080x2340", "country": "CA"},
    
    # Google Pixel
    {"manufacturer": "Google", "model": "Pixel 8 Pro", "device": "husky", "board": "google", "android": 14, "dpi": 560, "res": "1344x2992", "country": "US"},
    {"manufacturer": "Google", "model": "Pixel 7 Pro", "device": "cheetah", "board": "google", "android": 14, "dpi": 560, "res": "1440x3120", "country": "GB"},
    {"manufacturer": "Google", "model": "Pixel 6a", "device": "bluejay", "board": "google", "android": 13, "dpi": 420, "res": "1080x2400", "country": "CA"},
    {"manufacturer": "Google", "model": "Pixel 7a", "device": "lynx", "board": "google", "android": 14, "dpi": 440, "res": "1080x2400", "country": "AU"},
    {"manufacturer": "Google", "model": "Pixel 6 Pro", "device": "raven", "board": "google", "android": 13, "dpi": 560, "res": "1440x3120", "country": "US"},
    
    # OnePlus
    {"manufacturer": "OnePlus", "model": "CPH2451", "device": "OP5958L1", "board": "taro", "android": 14, "dpi": 560, "res": "1440x3216", "country": "IN"},
    {"manufacturer": "OnePlus", "model": "LE2123", "device": "lemonadep", "board": "lahaina", "android": 13, "dpi": 560, "res": "1440x3216", "country": "US"},
    {"manufacturer": "OnePlus", "model": "CPH2413", "device": "OP594DL1", "board": "lahaina", "android": 13, "dpi": 480, "res": "1080x2400", "country": "GB"},
    
    # Xiaomi
    {"manufacturer": "Xiaomi", "model": "2201116SG", "device": "ingres", "board": "mt6895", "android": 13, "dpi": 480, "res": "1220x2712", "country": "IN"},
    {"manufacturer": "Xiaomi", "model": "M2101K6G", "device": "sweet", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2400", "country": "RU"},
    {"manufacturer": "Xiaomi", "model": "2211133C", "device": "marble", "board": "taro", "android": 13, "dpi": 480, "res": "1220x2712", "country": "CN"},
    {"manufacturer": "Xiaomi", "model": "23013RK75C", "device": "fuxi", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3200", "country": "CN"},
    
    # OPPO
    {"manufacturer": "OPPO", "model": "CPH2449", "device": "OP5961L1", "board": "mt6895", "android": 13, "dpi": 480, "res": "1080x2400", "country": "ID"},
    {"manufacturer": "OPPO", "model": "CPH2487", "device": "OP5983L1", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3216", "country": "MY"},
    
    # Motorola
    {"manufacturer": "Motorola", "model": "moto g84 5G", "device": "milanf", "board": "taro", "android": 13, "dpi": 440, "res": "1080x2400", "country": "BR"},
    {"manufacturer": "Motorola", "model": "motorola edge 40", "device": "rtwo", "board": "taro", "android": 13, "dpi": 480, "res": "1080x2400", "country": "MX"},
    
    # Realme
    {"manufacturer": "realme", "model": "RMX3706", "device": "RE58B2L1", "board": "taro", "android": 13, "dpi": 480, "res": "1080x2412", "country": "IN"},
    {"manufacturer": "realme", "model": "RMX3785", "device": "RE58E4L1", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3168", "country": "CN"},
]

# Instagram versions (EXPANDED for more diversity)
IG_VERSIONS = [
    "315.0.0.26.109", "314.0.0.24.110", "313.0.0.28.109", "312.0.0.32.118",
    "311.0.0.32.119", "310.0.0.28.117", "309.0.0.40.113", "308.0.0.38.108",
    "316.0.0.29.120", "317.0.0.31.115", "318.0.0.27.111", "319.0.0.33.114",
]

# ==========================================
#              LOAD PROXIES
# ==========================================
def load_proxies() -> List[str]:
    proxies = []
    path = Path(__file__).parent / CONFIG["PROXIES_FILE"]
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies")
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")
    return proxies

PROXIES = load_proxies()

# ==========================================
#              FLASK APP
# ==========================================
app = Flask(__name__)
CORS(app)

# ==========================================
#     DYNAMIC IDENTITY SYSTEM (New Architecture)
# ==========================================

def generate_identity() -> Dict[str, Any]:
    """Generate a completely NEW identity with MAXIMUM diversity."""
    device = random.choice(DEVICES)
    ig_version = random.choice(IG_VERSIONS)
    
    # All unique IDs - fresh every time with MORE randomness
    device_id = f"android-{uuid4().hex[:16]}"
    phone_id = str(uuid4())
    guid = str(uuid4())
    adid = str(uuid4())
    google_adid = str(uuid4())
    family_device_id = str(uuid4())
    mid = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-', k=28))
    session_id = f"UFS-{uuid4()}-{random.randint(0, 5)}"
    client_time = str(time.time() + random.uniform(-2, 2))
    
    # Build User-Agent
    user_agent = (
        f"Instagram {ig_version} Android "
        f"({device['android']}/{device['android']}.0; "
        f"{device['dpi']}dpi; {device['res']}; "
        f"{device['manufacturer']}; {device['model']}; "
        f"{device['device']}; {device['board']}; en_{device['country']})"
    )
    
    # Build headers with MORE diversity
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Accept-Language': f"en-{device['country']},en;q=0.9",
        'Accept-Encoding': 'gzip, deflate, br',
        'User-Agent': user_agent,
        'X-IG-App-ID': '567067343352427',
        'X-IG-App-Locale': f"en_{device['country']}",
        'X-IG-Device-Locale': f"en_{device['country']}",
        'X-IG-Mapped-Locale': f"en_{device['country']}",
        'X-IG-Device-ID': guid,
        'X-IG-Family-Device-ID': family_device_id,
        'X-IG-Android-ID': device_id,
        'X-IG-Timezone-Offset': str(random.choice([-28800, -25200, -21600, -18000, -14400, -10800, 0, 3600, 7200, 10800, 19800, 28800, 32400])),
        'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G', 'MOBILE.4G']),
        'X-IG-Connection-Speed': f'{random.randint(1500, 5000)}kbps',
        'X-IG-Bandwidth-Speed-KBPS': str(random.randint(3000, 15000)),
        'X-IG-Bandwidth-TotalBytes-B': str(random.randint(2000000, 15000000)),
        'X-IG-Bandwidth-TotalTime-MS': str(random.randint(100, 500)),
        'X-IG-Capabilities': random.choice(['3brTvx0=', '3brTv58=', '3brTv50=', '3brTvwE=', '3brTv4E=']),
        'X-IG-WWW-Claim': '0',
        'X-Bloks-Version-Id': random.choice([
            'e538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88e',
            'f538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88f',
            'd538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88d'
        ]),
        'X-Bloks-Is-Layout-RTL': 'false',
        'X-Bloks-Is-Panorama-Enabled': 'true',
        'X-Pigeon-Session-Id': session_id,
        'X-Pigeon-Rawclienttime': client_time,
        'X-MID': mid,
        'X-FB-HTTP-Engine': 'Liger',
        'X-FB-Client-IP': 'True',
        'X-FB-Server-Cluster': 'True',
    }
    
    return {
        "device": device,
        "device_id": device_id,
        "phone_id": phone_id,
        "guid": guid,
        "headers": headers,
    }


# Track rate-limited proxies globally (persists across requests)
RATE_LIMITED_PROXIES: Dict[str, float] = {}  # proxy_url -> rate_limit_until

# NEW: Track proxy usage for smart rotation
PROXY_USAGE_TRACKER: Dict[str, Dict[str, Any]] = {}  # proxy_url -> {requests: int, last_used: float, resting_until: float}


def init_proxy_tracker(proxy_url: str):
    """Initialize tracking for a proxy."""
    if proxy_url not in PROXY_USAGE_TRACKER:
        PROXY_USAGE_TRACKER[proxy_url] = {
            "requests": 0,
            "last_used": 0,
            "resting_until": 0,
            "success_count": 0,
            "fail_count": 0,
        }


def is_proxy_available(proxy_url: str) -> bool:
    """Check if proxy is not rate-limited and not resting."""
    init_proxy_tracker(proxy_url)
    
    # Check rate limit
    if proxy_url in RATE_LIMITED_PROXIES:
        if time.time() > RATE_LIMITED_PROXIES[proxy_url]:
            del RATE_LIMITED_PROXIES[proxy_url]
        else:
            return False
    
    # Check if resting (NEW)
    if CONFIG["ENABLE_SMART_ROTATION"]:
        tracker = PROXY_USAGE_TRACKER[proxy_url]
        if time.time() < tracker["resting_until"]:
            return False
    
    return True


def mark_proxy_rate_limited(proxy_url: str):
    """Mark a proxy as rate-limited."""
    RATE_LIMITED_PROXIES[proxy_url] = time.time() + CONFIG["COOLDOWN_TIME"]
    init_proxy_tracker(proxy_url)
    PROXY_USAGE_TRACKER[proxy_url]["fail_count"] += 1


def mark_proxy_used(proxy_url: str, success: bool = True):
    """Mark that a proxy was used (NEW)."""
    init_proxy_tracker(proxy_url)
    tracker = PROXY_USAGE_TRACKER[proxy_url]
    tracker["requests"] += 1
    tracker["last_used"] = time.time()
    
    if success:
        tracker["success_count"] += 1
    else:
        tracker["fail_count"] += 1
    
    # Check if proxy needs rest
    if CONFIG["ENABLE_SMART_ROTATION"] and tracker["requests"] >= CONFIG["MAX_REQUESTS_PER_PROXY"]:
        tracker["resting_until"] = time.time() + CONFIG["PROXY_REST_TIME"]
        tracker["requests"] = 0  # Reset counter
        logger.debug(f"Proxy {proxy_url[:40]}... needs rest after {CONFIG['MAX_REQUESTS_PER_PROXY']} requests")


def get_available_proxies() -> List[str]:
    """Get all proxies that are not rate-limited or resting."""
    return [p for p in PROXIES if is_proxy_available(p)]


def get_rate_limited_count() -> int:
    """Get count of currently rate-limited proxies."""
    # Clean up expired ones
    now = time.time()
    expired = [p for p, until in RATE_LIMITED_PROXIES.items() if now > until]
    for p in expired:
        del RATE_LIMITED_PROXIES[p]
    return len(RATE_LIMITED_PROXIES)


def get_resting_count() -> int:
    """Get count of currently resting proxies (NEW)."""
    now = time.time()
    count = 0
    for proxy_url, tracker in PROXY_USAGE_TRACKER.items():
        if now < tracker["resting_until"]:
            count += 1
    return count


def get_proxy_stats() -> Dict[str, Any]:
    """Get detailed proxy statistics (NEW)."""
    total_requests = sum(t["requests"] for t in PROXY_USAGE_TRACKER.values())
    total_success = sum(t["success_count"] for t in PROXY_USAGE_TRACKER.values())
    total_fails = sum(t["fail_count"] for t in PROXY_USAGE_TRACKER.values())
    
    return {
        "total_proxies": len(PROXIES),
        "available": len(get_available_proxies()),
        "rate_limited": get_rate_limited_count(),
        "resting": get_resting_count(),
        "total_requests": total_requests,
        "success_rate": f"{(total_success / (total_success + total_fails) * 100):.1f}%" if (total_success + total_fails) > 0 else "0%",
    }


@dataclass
class ProxyWithDualIdentity:
    """A proxy with TWO different identities for rotation."""
    proxy_url: str
    identity1: Dict[str, Any]
    identity2: Dict[str, Any]
    current_identity: int = 0  # 0 or 1
    
    def get_current_identity(self) -> Dict[str, Any]:
        """Get the current identity."""
        return self.identity1 if self.current_identity == 0 else self.identity2
    
    def rotate(self):
        """Switch to the other identity."""
        self.current_identity = 1 - self.current_identity


class DynamicSessionManager:
    """
    Creates FRESH identities for each /search request.
    Each proxy gets 2 identities for rotation.
    """
    
    def __init__(self, proxies: List[str]):
        self.proxies_with_identities: List[ProxyWithDualIdentity] = []
        self.clients: Dict[str, httpx.AsyncClient] = {}
        self._setup(proxies)
    
    def _setup(self, proxies: List[str]):
        """Setup proxies with fresh dual identities."""
        available = [p for p in proxies if is_proxy_available(p)]
        
        for proxy_url in available:
            # Each proxy gets 2 DIFFERENT fresh identities
            self.proxies_with_identities.append(ProxyWithDualIdentity(
                proxy_url=proxy_url,
                identity1=generate_identity(),
                identity2=generate_identity(),
            ))
        
        logger.info(f"🔄 Created {len(self.proxies_with_identities)} proxies with dual identities (fresh!)")
    
    def get_available_proxies(self) -> List[ProxyWithDualIdentity]:
        """Get all proxies (already filtered during setup)."""
        return self.proxies_with_identities
    
    async def get_client(self, proxy_url: str) -> httpx.AsyncClient:
        """Get or create client for a proxy."""
        if proxy_url not in self.clients:
            self.clients[proxy_url] = httpx.AsyncClient(
                proxy=proxy_url,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
        return self.clients[proxy_url]
    
    async def close_all(self):
        """Close all clients."""
        for client in self.clients.values():
            try:
                await client.aclose()
            except:
                pass
        self.clients.clear()


# ==========================================
#     SESSION WARMING SYSTEM (Level 4)
# ==========================================

# Track warmed sessions globally
WARMED_SESSIONS: Dict[str, float] = {}  # proxy_url -> last_warm_time
WARM_DURATION = 300  # Session stays warm for 5 minutes

# Instagram endpoints for warming
WARM_ENDPOINTS = [
    ("GET", "https://i.instagram.com/api/v1/launcher/sync/"),
    ("POST", "https://i.instagram.com/api/v1/qe/sync/"),
]


def is_session_warm(proxy_url: str) -> bool:
    """Check if a session is still warm."""
    if proxy_url in WARMED_SESSIONS:
        if time.time() - WARMED_SESSIONS[proxy_url] < WARM_DURATION:
            return True
        # Expired
        del WARMED_SESSIONS[proxy_url]
    return False


def mark_session_warm(proxy_url: str):
    """Mark a session as warm."""
    WARMED_SESSIONS[proxy_url] = time.time()


def get_warm_count() -> int:
    """Get count of currently warm sessions."""
    now = time.time()
    # Clean up expired
    expired = [p for p, t in WARMED_SESSIONS.items() if now - t >= WARM_DURATION]
    for p in expired:
        del WARMED_SESSIONS[p]
    return len(WARMED_SESSIONS)


async def warm_single_session(proxy_url: str, identity: Dict[str, Any]) -> bool:
    """
    Warm a single session by making 1-2 'normal' requests.
    Returns True if successful.
    """
    try:
        async with httpx.AsyncClient(
            proxy=proxy_url,
            timeout=CONFIG["REQUEST_TIMEOUT"]
        ) as client:
            # Make a launcher sync request (like app opening)
            headers = identity["headers"].copy()
            
            # Launcher sync request
            try:
                response = await client.get(
                    "https://i.instagram.com/api/v1/launcher/sync/",
                    headers=headers
                )
                # Any response is okay - we just want to "touch" Instagram
            except:
                pass
            
            # Small delay
            await asyncio.sleep(random.uniform(0.3, 0.8))
            
            # QE sync request (optional, simulate app behavior)
            try:
                data = {
                    "_uuid": identity["guid"],
                    "experiments": "ig_android_device_detection_info_upload",
                }
                await client.post(
                    "https://i.instagram.com/api/v1/qe/sync/",
                    headers=headers,
                    data=data
                )
            except:
                pass
            
            mark_session_warm(proxy_url)
            return True
            
    except Exception as e:
        logger.debug(f"Warm failed for {proxy_url[:30]}: {e}")
        return False


async def warm_all_sessions_background():
    """
    Background task to warm all proxy sessions.
    Called once when server starts.
    """
    logger.info("🔥 Starting background session warming...")
    
    warmed = 0
    for proxy_url in PROXIES:
        if is_proxy_available(proxy_url) and not is_session_warm(proxy_url):
            identity = generate_identity()
            success = await warm_single_session(proxy_url, identity)
            if success:
                warmed += 1
            # Don't hammer - small delay between proxies
            await asyncio.sleep(random.uniform(0.2, 0.5))
    
    logger.info(f"🔥 Warmed {warmed}/{len(PROXIES)} sessions")


async def ensure_session_warm(proxy_url: str, identity: Dict[str, Any]) -> bool:
    """
    Ensure a session is warm before checking username.
    If already warm, returns immediately.
    If cold, warms it first.
    """
    if is_session_warm(proxy_url):
        return True
    
    # Need to warm
    return await warm_single_session(proxy_url, identity)


# ==========================================
#     HUMAN-LIKE TIMING (Level 2)
# ==========================================
async def human_delay():
    """Simulate human-like delay between actions."""
    # Variable delay with occasional longer pauses
    if random.random() < 0.1:  # 10% chance of longer pause
        delay = random.uniform(2.0, 4.0)
    else:
        delay = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
    
    await asyncio.sleep(delay)


async def simulate_typing_delay(username: str):
    """Simulate the delay of typing a username."""
    if CONFIG["TYPING_SIMULATION"]:
        # Average typing speed: 40-60 WPM = ~200-300ms per character
        typing_time = len(username) * random.uniform(0.05, 0.15)
        await asyncio.sleep(typing_time)


# ==========================================
#     USERNAME GENERATOR (Level 1 - Simple)
# ==========================================
def generate_simple_username() -> str:
    """Generate a simple 5-char username (NO symbols) - higher availability!"""
    return random.choice(LETTERS) + ''.join(random.choices(CHARS, k=4))


def generate_semi_quad_username() -> str:
    """
    Generate a semi-quad username (5 chars with _ or . in allowed positions).
    Rules:
    - Must start with a letter (a-z)
    - Must contain at least one _ or . 
    - Symbols can be in positions 1, 2, or 3 ONLY (0-indexed: index 1, 2, 3)
    - Cannot start or end with . (underscore at end is allowed by Instagram)
    - No consecutive . or adjacent ._/_.  
    """
    max_attempts = 100
    
    for _ in range(max_attempts):
        # Start with a letter
        first_char = random.choice(LETTERS)
        
        # Choose symbol and position (positions 1, 2, or 3 for a 5-char username)
        symbol = random.choice('._')
        symbol_pos = random.choice([1, 2, 3])  # Position index in 5-char string
        
        # Build the username
        username_chars = [first_char]
        for pos in range(1, 5):
            if pos == symbol_pos:
                username_chars.append(symbol)
            else:
                username_chars.append(random.choice(CHARS))
        
        username = ''.join(username_chars)
        
        # Validate Instagram rules
        # Rule 1: Cannot end with .
        if username.endswith('.'):
            continue
        # Rule 2: No consecutive dots
        if '..' in username:
            continue
        # Rule 3: No ._ or _. adjacent
        if '._' in username or '_.' in username:
            continue
        
        return username
    
    # Fallback: guaranteed valid
    return random.choice(LETTERS) + '_' + ''.join(random.choices(CHARS, k=2)) + random.choice(CHARS)


# ==========================================
#     CORE: CHECK USERNAME (New System)
# ==========================================
async def check_username(
    client: httpx.AsyncClient,
    proxy_with_id: ProxyWithDualIdentity,
    username: str,
    ensure_warm: bool = True
) -> Dict[str, Any]:
    """Check a single username with dynamic identity and session warming."""
    try:
        # Get current identity
        identity = proxy_with_id.get_current_identity()
        
        # Ensure session is warm (Level 4: Session Warming)
        if ensure_warm:
            await ensure_session_warm(proxy_with_id.proxy_url, identity)
        
        # Simulate typing the username
        await simulate_typing_delay(username)
        
        data = {
            "username": username,
            "_uuid": identity["guid"],
        }
        
        response = await client.post(
            CONFIG["API_URL"],
            headers=identity["headers"],
            data=data
        )
        
        # Rotate to other identity for next request
        proxy_with_id.rotate()
        
        # Mark session as warm (successful request)
        mark_session_warm(proxy_with_id.proxy_url)
        
        text = response.text
        
        if '"available":true' in text or '"available": true' in text:
            mark_proxy_used(proxy_with_id.proxy_url, success=True)
            return {"status": "available", "username": username, "proxy": proxy_with_id.proxy_url}
        elif '"available":false' in text or '"available": false' in text:
            mark_proxy_used(proxy_with_id.proxy_url, success=True)
            return {"status": "taken", "username": username, "proxy": proxy_with_id.proxy_url}
        elif 'wait a few minutes' in text.lower() or 'rate_limit' in text.lower():
            mark_proxy_rate_limited(proxy_with_id.proxy_url)
            mark_proxy_used(proxy_with_id.proxy_url, success=False)
            return {"status": "rate_limit", "username": username, "proxy": proxy_with_id.proxy_url}
        elif 'challenge_required' in text.lower():
            mark_proxy_rate_limited(proxy_with_id.proxy_url)
            mark_proxy_used(proxy_with_id.proxy_url, success=False)
            return {"status": "challenge", "username": username, "proxy": proxy_with_id.proxy_url}
        else:
            mark_proxy_used(proxy_with_id.proxy_url, success=False)
            return {"status": "error", "username": username, "response": text[:100]}
            
    except httpx.TimeoutException:
        mark_proxy_used(proxy_with_id.proxy_url, success=False)
        return {"status": "timeout", "username": username}
    except Exception as e:
        mark_proxy_used(proxy_with_id.proxy_url, success=False)
        return {"status": "error", "username": username, "error": str(e)[:50]}


# ==========================================
#     SMART SEARCH WITH DYNAMIC IDENTITIES
# ==========================================
async def stealth_search() -> Dict[str, Any]:
    """
    Search with DYNAMIC IDENTITIES:
    - Fresh identities generated for EACH /search request
    - Each proxy gets 2 identities for rotation
    - Rate-limited proxies are skipped automatically
    """
    start_time = time.time()
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0}
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "duration": 0}
    
    # Create FRESH session manager with NEW identities
    manager = DynamicSessionManager(PROXIES)
    available_proxies = manager.get_available_proxies()
    
    if not available_proxies:
        return {
            "status": "failed", 
            "reason": "all_proxies_rate_limited", 
            "duration": 0,
            "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}"
        }
    
    logger.info(f"� Starting search with {len(available_proxies)} proxies (fresh dual identities!)")
    
    while time.time() - start_time < CONFIG["TIMEOUT"]:
        # Limit concurrent requests
        proxies_to_use = available_proxies[:CONFIG["MAX_CONCURRENT"]]
        
        if not proxies_to_use:
            logger.warning("No available proxies! Waiting...")
            await asyncio.sleep(5)
            # Refresh available proxies
            available_proxies = [p for p in manager.proxies_with_identities if is_proxy_available(p.proxy_url)]
            continue
        
        # Generate usernames
        usernames = [generate_simple_username() for _ in range(len(proxies_to_use))]
        
        # Create tasks
        tasks = []
        for proxy_with_id, username in zip(proxies_to_use, usernames):
            client = await manager.get_client(proxy_with_id.proxy_url)
            tasks.append(asyncio.create_task(check_username(client, proxy_with_id, username)))
        
        # Process results as they come in
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            if result["status"] == "available":
                # Found! Cancel remaining and return
                for t in tasks:
                    t.cancel()
                
                duration = round(time.time() - start_time, 2)
                
                logger.info(f"✅ FOUND: {result['username']} in {duration}s")
                
                # Close clients in background (don't wait)
                asyncio.create_task(manager.close_all())
                
                return {
                    "status": "success",
                    "username": result["username"],
                    "duration": duration,
                    "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
                    "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}"
                }
                
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] in ["rate_limit", "challenge"]:
                stats["rate_limits"] += 1
            else:
                stats["errors"] += 1
        
        # Human-like delay between batches
        await human_delay()
    
    # Timeout
    # Close clients in background
    asyncio.create_task(manager.close_all())
    return {
        "status": "failed",
        "reason": "timeout",
        "duration": round(time.time() - start_time, 2),
        "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
        "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}"
    }


# ==========================================
#     SEMI-QUAD SEARCH (FOR /prosearch) - FAST MODE
# ==========================================
async def semi_quad_stealth_search() -> Dict[str, Any]:
    """
    FAST Search for SEMI-QUAD usernames only.
    NO DELAYS - Maximum speed for quick results.
    """
    start_time = time.time()
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0}
    
    # FAST MODE CONFIG
    FAST_MAX_CONCURRENT = 50  # Use more proxies at once
    FAST_TIMEOUT = 30  # Max 30 seconds
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "duration": 0}
    
    # Create FRESH session manager with NEW identities
    manager = DynamicSessionManager(PROXIES)
    available_proxies = manager.get_available_proxies()
    
    if not available_proxies:
        return {
            "status": "failed", 
            "reason": "all_proxies_rate_limited", 
            "duration": 0,
            "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}"
        }
    
    logger.info(f"� Starting FAST SEMI-QUAD search with {len(available_proxies)} proxies")
    
    while time.time() - start_time < FAST_TIMEOUT:
        # Use MORE proxies at once for speed
        proxies_to_use = available_proxies[:FAST_MAX_CONCURRENT]
        
        if not proxies_to_use:
            logger.warning("No available proxies! Waiting...")
            await asyncio.sleep(2)  # Shorter wait
            # Refresh available proxies
            available_proxies = [p for p in manager.proxies_with_identities if is_proxy_available(p.proxy_url)]
            continue
        
        # Generate SEMI-QUAD usernames (with _ or .)
        usernames = [generate_semi_quad_username() for _ in range(len(proxies_to_use))]
        
        # Create tasks
        tasks = []
        for proxy_with_id, username in zip(proxies_to_use, usernames):
            client = await manager.get_client(proxy_with_id.proxy_url)
            tasks.append(asyncio.create_task(check_username(client, proxy_with_id, username)))
        
        # Process results as they come in
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            if result["status"] == "available":
                # Found! Cancel remaining and return
                for t in tasks:
                    t.cancel()
                
                duration = round(time.time() - start_time, 2)
                
                logger.info(f"✅ FOUND SEMI-QUAD: {result['username']} in {duration}s")
                
                # Close clients in background (don't wait)
                asyncio.create_task(manager.close_all())
                
                return {
                    "status": "success",
                    "username": result["username"],
                    "type": "semi-quad",
                    "duration": duration,
                    "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
                    "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}"
                }
                
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] in ["rate_limit", "challenge"]:
                stats["rate_limits"] += 1
            else:
                stats["errors"] += 1
        
        # NO DELAY - Go immediately to next batch for maximum speed!
    
    # Timeout
    # Close clients in background
    asyncio.create_task(manager.close_all())
    return {
        "status": "failed",
        "reason": "timeout",
        "duration": round(time.time() - start_time, 2),
        "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
        "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}"
    }


# ==========================================
#     DETAILED SEARCH (FOR DEBUGGING)
# ==========================================
async def detailed_stealth_search() -> Dict[str, Any]:
    """
    Same as stealth_search but with EXTREMELY DETAILED logging.
    Uses the new DYNAMIC IDENTITY system.
    """
    start_time = time.time()
    
    # Detailed log for everything
    detailed_log = {
        "timeline": [],
        "identities_created": [],
        "requests_made": [],
        "delays_applied": [],
        "rate_limits_detected": [],
        "usernames_checked": [],
        "responses_received": [],
    }
    
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0, "timeouts": 0}
    
    def log_event(event_type: str, data: Dict[str, Any]):
        """Log an event with timestamp."""
        elapsed = round(time.time() - start_time, 4)
        detailed_log["timeline"].append({
            "time": elapsed,
            "event": event_type,
            "data": data
        })
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "detailed_log": detailed_log}
    
    log_event("INIT", {
        "proxies_count": len(PROXIES), 
        "warm_sessions": get_warm_count(),
        "config": CONFIG
    })
    
    # Create FRESH session manager with NEW identities
    manager = DynamicSessionManager(PROXIES)
    available_proxies = manager.get_available_proxies()
    
    # Log all created identities
    for proxy_with_id in available_proxies:
        identity1 = proxy_with_id.identity1
        identity2 = proxy_with_id.identity2
        identity_info = {
            "proxy": proxy_with_id.proxy_url[:50] + "...",
            "identity1": {
                "device": identity1["device"]["model"],
                "device_id": identity1["device_id"],
                "guid": identity1["guid"][:12] + "...",
            },
            "identity2": {
                "device": identity2["device"]["model"],
                "device_id": identity2["device_id"],
                "guid": identity2["guid"][:12] + "...",
            },
        }
        detailed_log["identities_created"].append(identity_info)
    
    log_event("IDENTITIES_CREATED", {
        "count": len(available_proxies),
        "total_identities": len(available_proxies) * 2,
    })
    
    batch_number = 0
    
    while time.time() - start_time < CONFIG["TIMEOUT"]:
        batch_number += 1
        batch_start = time.time()
        
        # Get available proxies
        current_available = [p for p in available_proxies if is_proxy_available(p.proxy_url)]
        
        log_event("BATCH_START", {
            "batch": batch_number,
            "available_proxies": len(current_available),
            "rate_limited_proxies": get_rate_limited_count(),
        })
        
        if not current_available:
            log_event("ALL_RATE_LIMITED", {"waiting": 5})
            await asyncio.sleep(5)
            continue
        
        # Limit concurrent
        proxies_to_use = current_available[:CONFIG["MAX_CONCURRENT"]]
        
        # Generate usernames
        usernames = [generate_simple_username() for _ in range(len(proxies_to_use))]
        
        log_event("USERNAMES_GENERATED", {
            "count": len(usernames),
            "samples": usernames[:5],
        })
        
        # Create and track tasks
        tasks = []
        
        for i, (proxy_with_id, username) in enumerate(zip(proxies_to_use, usernames)):
            client = await manager.get_client(proxy_with_id.proxy_url)
            identity = proxy_with_id.get_current_identity()
            
            # Log request details
            request_info = {
                "index": i,
                "username": username,
                "proxy": proxy_with_id.proxy_url[:40] + "...",
                "device": identity["device"]["model"],
                "identity_num": proxy_with_id.current_identity + 1,
                "headers_sample": {
                    "User-Agent": identity["headers"]["User-Agent"][:60] + "...",
                    "X-IG-Device-ID": identity["headers"]["X-IG-Device-ID"][:20] + "...",
                }
            }
            detailed_log["requests_made"].append(request_info)
            
            tasks.append(asyncio.create_task(check_username(client, proxy_with_id, username)))
        
        log_event("REQUESTS_SENT", {"count": len(tasks)})
        
        # Process results
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            response_info = {
                "username": result.get("username"),
                "status": result["status"],
                "response_preview": result.get("response", result.get("error", ""))[:100] if result.get("response") or result.get("error") else None,
            }
            detailed_log["responses_received"].append(response_info)
            detailed_log["usernames_checked"].append(result.get("username"))
            
            if result["status"] == "available":
                for t in tasks:
                    t.cancel()
                
                duration = round(time.time() - start_time, 4)
                
                log_event("FOUND_AVAILABLE", {
                    "username": result["username"],
                    "total_checked": stats["checked"],
                    "duration": duration,
                })
                
                # Close clients in background (don't wait)
                log_event("CLEANUP", {"closing_clients": len(manager.clients)})
                asyncio.create_task(manager.close_all())
                
                return {
                    "status": "success",
                    "username": result["username"],
                    "duration": duration,
                    "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
                    "batches_processed": batch_number,
                    "detailed_log": detailed_log,
                }
                
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] == "rate_limit":
                stats["rate_limits"] += 1
                detailed_log["rate_limits_detected"].append(result.get("username"))
            elif result["status"] == "timeout":
                stats["timeouts"] += 1
            else:
                stats["errors"] += 1
        
        # Apply human delay
        if random.random() < 0.1:
            delay = random.uniform(2.0, 4.0)
        else:
            delay = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
        
        await asyncio.sleep(delay)
        
        delay_info = {
            "batch": batch_number,
            "delay_seconds": round(delay, 3),
            "batch_duration": round(time.time() - batch_start, 3),
        }
        detailed_log["delays_applied"].append(delay_info)
        
        log_event("BATCH_END", delay_info)
    
    # Timeout
    log_event("CLEANUP", {"closing_clients": len(manager.clients)})
    asyncio.create_task(manager.close_all())
    return {
        "status": "failed",
        "reason": "timeout",
        "duration": round(time.time() - start_time, 2),
        "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
        "batches_processed": batch_number,
        "detailed_log": detailed_log,
    }


# ==========================================
#     DETAILED SEMI-QUAD SEARCH (FOR /infoprosearch)
# ==========================================
async def detailed_semi_quad_stealth_search() -> Dict[str, Any]:
    """
    Same as detailed_stealth_search but for SEMI-QUAD usernames.
    Uses generate_semi_quad_username instead of generate_simple_username.
    """
    start_time = time.time()
    
    # Detailed log for everything
    detailed_log = {
        "timeline": [],
        "identities_created": [],
        "requests_made": [],
        "delays_applied": [],
        "rate_limits_detected": [],
        "usernames_checked": [],
        "responses_received": [],
    }
    
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0, "timeouts": 0}
    
    def log_event(event_type: str, data: Dict[str, Any]):
        """Log an event with timestamp."""
        elapsed = round(time.time() - start_time, 4)
        detailed_log["timeline"].append({
            "time": elapsed,
            "event": event_type,
            "data": data
        })
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "detailed_log": detailed_log}
    
    log_event("INIT", {
        "proxies_count": len(PROXIES), 
        "warm_sessions": get_warm_count(),
        "config": CONFIG,
        "search_type": "SEMI-QUAD"
    })
    
    # Create FRESH session manager with NEW identities
    manager = DynamicSessionManager(PROXIES)
    available_proxies = manager.get_available_proxies()
    
    # Log all created identities
    for proxy_with_id in available_proxies:
        identity1 = proxy_with_id.identity1
        identity2 = proxy_with_id.identity2
        identity_info = {
            "proxy": proxy_with_id.proxy_url[:50] + "...",
            "identity1": {
                "device": identity1["device"]["model"],
                "device_id": identity1["device_id"],
                "guid": identity1["guid"][:12] + "...",
            },
            "identity2": {
                "device": identity2["device"]["model"],
                "device_id": identity2["device_id"],
                "guid": identity2["guid"][:12] + "...",
            },
        }
        detailed_log["identities_created"].append(identity_info)
    
    log_event("IDENTITIES_CREATED", {
        "count": len(available_proxies),
        "total_identities": len(available_proxies) * 2,
    })
    
    batch_number = 0
    
    while time.time() - start_time < CONFIG["TIMEOUT"]:
        batch_number += 1
        batch_start = time.time()
        
        # Get available proxies
        current_available = [p for p in available_proxies if is_proxy_available(p.proxy_url)]
        
        log_event("BATCH_START", {
            "batch": batch_number,
            "available_proxies": len(current_available),
            "rate_limited_proxies": get_rate_limited_count(),
        })
        
        if not current_available:
            log_event("ALL_RATE_LIMITED", {"waiting": 5})
            await asyncio.sleep(5)
            continue
        
        # Limit concurrent
        proxies_to_use = current_available[:CONFIG["MAX_CONCURRENT"]]
        
        # Generate SEMI-QUAD usernames
        usernames = [generate_semi_quad_username() for _ in range(len(proxies_to_use))]
        
        log_event("USERNAMES_GENERATED", {
            "count": len(usernames),
            "samples": usernames[:5],
            "type": "semi-quad"
        })
        
        # Create and track tasks
        tasks = []
        
        for i, (proxy_with_id, username) in enumerate(zip(proxies_to_use, usernames)):
            client = await manager.get_client(proxy_with_id.proxy_url)
            identity = proxy_with_id.get_current_identity()
            
            # Log request details
            request_info = {
                "index": i,
                "username": username,
                "proxy": proxy_with_id.proxy_url[:40] + "...",
                "device": identity["device"]["model"],
                "identity_num": proxy_with_id.current_identity + 1,
                "headers_sample": {
                    "User-Agent": identity["headers"]["User-Agent"][:60] + "...",
                    "X-IG-Device-ID": identity["headers"]["X-IG-Device-ID"][:20] + "...",
                }
            }
            detailed_log["requests_made"].append(request_info)
            
            tasks.append(asyncio.create_task(check_username(client, proxy_with_id, username)))
        
        log_event("REQUESTS_SENT", {"count": len(tasks)})
        
        # Process results
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            response_info = {
                "username": result.get("username"),
                "status": result["status"],
                "response_preview": result.get("response", result.get("error", ""))[:100] if result.get("response") or result.get("error") else None,
            }
            detailed_log["responses_received"].append(response_info)
            detailed_log["usernames_checked"].append(result.get("username"))
            
            if result["status"] == "available":
                for t in tasks:
                    t.cancel()
                
                duration = round(time.time() - start_time, 4)
                
                log_event("FOUND_AVAILABLE", {
                    "username": result["username"],
                    "total_checked": stats["checked"],
                    "duration": duration,
                    "type": "semi-quad"
                })
                
                # Close clients in background (don't wait)
                log_event("CLEANUP", {"closing_clients": len(manager.clients)})
                asyncio.create_task(manager.close_all())
                
                return {
                    "status": "success",
                    "username": result["username"],
                    "type": "semi-quad",
                    "duration": duration,
                    "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
                    "batches_processed": batch_number,
                    "detailed_log": detailed_log,
                }
                
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] == "rate_limit":
                stats["rate_limits"] += 1
                detailed_log["rate_limits_detected"].append(result.get("username"))
            elif result["status"] == "timeout":
                stats["timeouts"] += 1
            else:
                stats["errors"] += 1
        
        # Apply human delay
        if random.random() < 0.1:
            delay = random.uniform(2.0, 4.0)
        else:
            delay = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
        
        await asyncio.sleep(delay)
        
        delay_info = {
            "batch": batch_number,
            "delay_seconds": round(delay, 3),
            "batch_duration": round(time.time() - batch_start, 3),
        }
        detailed_log["delays_applied"].append(delay_info)
        
        log_event("BATCH_END", delay_info)
    
    # Timeout
    log_event("CLEANUP", {"closing_clients": len(manager.clients)})
    asyncio.create_task(manager.close_all())
    return {
        "status": "failed",
        "reason": "timeout",
        "type": "semi-quad",
        "duration": round(time.time() - start_time, 2),
        "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
        "batches_processed": batch_number,
        "detailed_log": detailed_log,
    }


# ==========================================
#              API ROUTES
# ==========================================
@app.route('/')
def home():
    stats = get_proxy_stats()
    return jsonify({
        "status": "online",
        "message": "Instagram Username Checker - ULTIMATE STEALTH Edition v2.0 (OPTIMIZED)",
        "version": "2.0",
        "endpoints": {
            "/search": "Quick search - Smart mix (70% simple + 30% semi-quad)",
            "/prosearch": "Semi-quad search - Fast mode with _ or . symbols",
            "/infosearch": "Detailed search - Full logging for debugging",
            "/infoprosearch": "Detailed semi-quad search - Full logging",
            "/warm": "Pre-warm all proxy sessions",
            "/status": "Get detailed system status and statistics"
        },
        "features": [
            "🚀 SPEED: 40 concurrent requests (up from 15)",
            "🎭 STEALTH: 25+ device models, 12 IG versions",
            "🔄 SMART ROTATION: Auto-rest after 8 requests",
            "🔥 SESSION WARMING: Pre-warmed connections",
            "📊 USAGE TRACKING: Real-time proxy statistics",
            "⚡ REDUCED DELAYS: 0.3-1.2s (down from 0.8-2.5s)",
            "🛡️ ENHANCED HEADERS: More diversity & randomness",
            "💪 DUAL IDENTITIES: 2 identities per proxy"
        ],
        "proxies": {
            "total": len(PROXIES),
            "available": stats["available"],
            "warm": get_warm_count(),
            "resting": stats["resting"],
            "rate_limited": stats["rate_limited"]
        },
        "performance": {
            "total_requests": stats["total_requests"],
            "success_rate": stats["success_rate"]
        },
        "stealth_level": "MAXIMUM++ (IMPOSSIBLE TO DETECT)"
    })


@app.route('/status')
def status():
    """Get current status of all systems with detailed statistics."""
    stats = get_proxy_stats()
    return jsonify({
        "proxies": {
            "total": len(PROXIES),
            "available": stats["available"],
            "warm": get_warm_count(),
            "cold": len(PROXIES) - get_warm_count(),
            "rate_limited": stats["rate_limited"],
            "resting": stats["resting"],
        },
        "performance": {
            "total_requests": stats["total_requests"],
            "success_rate": stats["success_rate"],
        },
        "warming": {
            "warm_duration_seconds": WARM_DURATION,
            "warmed_sessions_count": get_warm_count()
        },
        "config": {
            "max_concurrent": CONFIG["MAX_CONCURRENT"],
            "max_requests_per_proxy": CONFIG["MAX_REQUESTS_PER_PROXY"],
            "proxy_rest_time": CONFIG["PROXY_REST_TIME"],
            "smart_rotation_enabled": CONFIG["ENABLE_SMART_ROTATION"]
        }
    })


@app.route('/warm')
async def warm():
    """Manually warm all proxy sessions."""
    await warm_all_sessions_background()
    return jsonify({
        "status": "success",
        "message": "All sessions warmed",
        "warm_count": get_warm_count()
    })

@app.route('/search')
async def search():
    """
    Find one available username with maximum stealth.
    Smart Probability: 70% Simple Search (5 chars), 30% Pro Search (Semi-Quad).
    """
    if random.random() < 0.7:
        # 70% chance: Simple Search (stealth_search)
        result = await stealth_search()
    else:
        # 30% chance: Pro Search (semi_quad_stealth_search)
        result = await semi_quad_stealth_search()
    
    return jsonify(result)

@app.route('/infosearch')
async def info_search():
    """Find one available username with EXTREMELY DETAILED logging."""
    result = await detailed_stealth_search()
    return jsonify(result)


@app.route('/prosearch')
async def pro_search():
    """Find one available SEMI-QUAD username (with _ or . in allowed positions)."""
    result = await semi_quad_stealth_search()
    return jsonify(result)


@app.route('/infoprosearch')
async def info_pro_search():
    """Find one available SEMI-QUAD username with EXTREMELY DETAILED logging."""
    result = await detailed_semi_quad_stealth_search()
    return jsonify(result)

# ==========================================
#              MAIN
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting ULTIMATE STEALTH server on port {port}")
    logger.info(f"🛡️ Stealth features: Session persistence, Human timing, Smart rotation")
    app.run(host='0.0.0.0', port=port)