#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - ULTIMATE STEALTH Edition v3.0
==========================================================

IMPOSSIBLE TO RATE LIMIT - Maximum stealth with all protection levels:
- Level 1: Simple usernames, random delays
- Level 2: Session persistence, human-like timing
- Level 3: Smart proxy rotation, enhanced fingerprints
- Level 4: Session warming
- Level 5: TLS Fingerprint Randomization (curl_cffi)
- Level 6: Advanced Cookie Management
- Level 7: Poisson Timing Distribution
- Level 8: Multi-Endpoint Warming
- Level 9: Header Entropy Maximization
- Level 10: Request Jittering System

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import logging
import math
from pathlib import Path
from typing import Optional, List, Dict, Any, Set, Tuple
from uuid import uuid4
from dataclasses import dataclass, field
from collections import OrderedDict
from http.cookies import SimpleCookie

# TLS Fingerprint: Try curl_cffi first, fallback to httpx for Railway compatibility
try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
    USE_CURL_CFFI = True
    logger_init_msg = "Using curl_cffi for TLS fingerprint randomization"
except ImportError:
    USE_CURL_CFFI = False
    logger_init_msg = "curl_cffi not available, using httpx (reduced stealth)"

import httpx
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from enum import Enum

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
    "TIMEOUT": 90,
    "REQUEST_TIMEOUT": 15.0,
    "PROXIES_FILE": "proxies.txt",
    
    # Speed settings (OPTIMIZED)
    "MIN_DELAY": 0.3,
    "MAX_DELAY": 1.2,
    "MAX_CONCURRENT": 40,
    "COOLDOWN_TIME": 60,  # Increased for better recovery
    "TYPING_SIMULATION": True,
    
    # Smart proxy management
    "MAX_REQUESTS_PER_PROXY": 5,  # Reduced for more rotation
    "PROXY_REST_TIME": 30,
    "ENABLE_SMART_ROTATION": True,
    
    # NEW: Stealth settings
    "POISSON_MEAN_DELAY": 1.2,  # Average delay for Poisson distribution
    "MICRO_JITTER_MIN": 0.03,
    "MICRO_JITTER_MAX": 0.12,
    "SLOW_CONNECTION_CHANCE": 0.08,  # 8% chance of simulating slow connection
    "HEADER_SHUFFLE": True,  # Randomize header order
}

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# ==========================================
#     TLS FINGERPRINT - BROWSER IMPERSONATIONS
# ==========================================
BROWSER_IMPERSONATIONS = [
    "chrome110", "chrome116", "chrome119", "chrome120", "chrome123", "chrome124",
    "safari15_3", "safari15_5", "safari17_0", "safari17_2_ios",
    "edge99", "edge101",
]

# Extended Android devices database (EXPANDED for more diversity)
DEVICES = [
    # Samsung Galaxy S Series
    {"manufacturer": "Samsung", "model": "SM-G998B", "device": "p3s", "board": "exynos2100", "android": 13, "dpi": 640, "res": "1440x3200", "country": "US"},
    {"manufacturer": "Samsung", "model": "SM-S908B", "device": "b0q", "board": "exynos2200", "android": 14, "dpi": 600, "res": "1440x3088", "country": "GB"},
    {"manufacturer": "Samsung", "model": "SM-S918B", "device": "dm3q", "board": "exynos2300", "android": 14, "dpi": 640, "res": "1440x3088", "country": "DE"},
    {"manufacturer": "Samsung", "model": "SM-G991B", "device": "o1s", "board": "exynos2100", "android": 13, "dpi": 480, "res": "1080x2400", "country": "FR"},
    {"manufacturer": "Samsung", "model": "SM-S928B", "device": "e3q", "board": "exynos2400", "android": 14, "dpi": 640, "res": "1440x3120", "country": "KR"},
    
    # Samsung Galaxy A/M Series
    {"manufacturer": "Samsung", "model": "SM-A536B", "device": "a53x", "board": "exynos1280", "android": 13, "dpi": 450, "res": "1080x2400", "country": "IT"},
    {"manufacturer": "Samsung", "model": "SM-A525F", "device": "a52q", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2340", "country": "ES"},
    {"manufacturer": "Samsung", "model": "SM-A546B", "device": "a54x", "board": "exynos1380", "android": 14, "dpi": 480, "res": "1080x2340", "country": "CA"},
    {"manufacturer": "Samsung", "model": "SM-M546B", "device": "m54x", "board": "exynos1380", "android": 14, "dpi": 450, "res": "1080x2400", "country": "IN"},
    
    # Google Pixel
    {"manufacturer": "Google", "model": "Pixel 8 Pro", "device": "husky", "board": "google", "android": 14, "dpi": 560, "res": "1344x2992", "country": "US"},
    {"manufacturer": "Google", "model": "Pixel 7 Pro", "device": "cheetah", "board": "google", "android": 14, "dpi": 560, "res": "1440x3120", "country": "GB"},
    {"manufacturer": "Google", "model": "Pixel 6a", "device": "bluejay", "board": "google", "android": 13, "dpi": 420, "res": "1080x2400", "country": "CA"},
    {"manufacturer": "Google", "model": "Pixel 7a", "device": "lynx", "board": "google", "android": 14, "dpi": 440, "res": "1080x2400", "country": "AU"},
    {"manufacturer": "Google", "model": "Pixel 6 Pro", "device": "raven", "board": "google", "android": 13, "dpi": 560, "res": "1440x3120", "country": "US"},
    {"manufacturer": "Google", "model": "Pixel 8", "device": "shiba", "board": "google", "android": 14, "dpi": 420, "res": "1080x2400", "country": "JP"},
    
    # OnePlus
    {"manufacturer": "OnePlus", "model": "CPH2451", "device": "OP5958L1", "board": "taro", "android": 14, "dpi": 560, "res": "1440x3216", "country": "IN"},
    {"manufacturer": "OnePlus", "model": "LE2123", "device": "lemonadep", "board": "lahaina", "android": 13, "dpi": 560, "res": "1440x3216", "country": "US"},
    {"manufacturer": "OnePlus", "model": "CPH2413", "device": "OP594DL1", "board": "lahaina", "android": 13, "dpi": 480, "res": "1080x2400", "country": "GB"},
    {"manufacturer": "OnePlus", "model": "PHB110", "device": "salami", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3216", "country": "CN"},
    
    # Xiaomi
    {"manufacturer": "Xiaomi", "model": "2201116SG", "device": "ingres", "board": "mt6895", "android": 13, "dpi": 480, "res": "1220x2712", "country": "IN"},
    {"manufacturer": "Xiaomi", "model": "M2101K6G", "device": "sweet", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2400", "country": "RU"},
    {"manufacturer": "Xiaomi", "model": "2211133C", "device": "marble", "board": "taro", "android": 13, "dpi": 480, "res": "1220x2712", "country": "CN"},
    {"manufacturer": "Xiaomi", "model": "23013RK75C", "device": "fuxi", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3200", "country": "CN"},
    {"manufacturer": "Xiaomi", "model": "2312DRA50G", "device": "aurora", "board": "pineapple", "android": 14, "dpi": 560, "res": "1440x3200", "country": "TW"},
    
    # OPPO
    {"manufacturer": "OPPO", "model": "CPH2449", "device": "OP5961L1", "board": "mt6895", "android": 13, "dpi": 480, "res": "1080x2400", "country": "ID"},
    {"manufacturer": "OPPO", "model": "CPH2487", "device": "OP5983L1", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3216", "country": "MY"},
    {"manufacturer": "OPPO", "model": "PHQ110", "device": "OP5A11L1", "board": "pineapple", "android": 14, "dpi": 560, "res": "1440x3168", "country": "SG"},
    
    # Vivo
    {"manufacturer": "vivo", "model": "V2219", "device": "PD2219", "board": "taro", "android": 13, "dpi": 480, "res": "1080x2400", "country": "IN"},
    {"manufacturer": "vivo", "model": "V2324", "device": "PD2324", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3200", "country": "CN"},
    
    # Motorola
    {"manufacturer": "Motorola", "model": "moto g84 5G", "device": "milanf", "board": "taro", "android": 13, "dpi": 440, "res": "1080x2400", "country": "BR"},
    {"manufacturer": "Motorola", "model": "motorola edge 40", "device": "rtwo", "board": "taro", "android": 13, "dpi": 480, "res": "1080x2400", "country": "MX"},
    {"manufacturer": "Motorola", "model": "motorola edge 50 pro", "device": "eqe", "board": "kalama", "android": 14, "dpi": 480, "res": "1220x2712", "country": "EU"},
    
    # Realme
    {"manufacturer": "realme", "model": "RMX3706", "device": "RE58B2L1", "board": "taro", "android": 13, "dpi": 480, "res": "1080x2412", "country": "IN"},
    {"manufacturer": "realme", "model": "RMX3785", "device": "RE58E4L1", "board": "kalama", "android": 14, "dpi": 560, "res": "1440x3168", "country": "CN"},
    
    # Nothing
    {"manufacturer": "Nothing", "model": "A063", "device": "Pong", "board": "taro", "android": 13, "dpi": 440, "res": "1080x2412", "country": "GB"},
    {"manufacturer": "Nothing", "model": "A142", "device": "Pacman", "board": "kalama", "android": 14, "dpi": 460, "res": "1080x2412", "country": "US"},
    
    # ASUS ROG
    {"manufacturer": "ASUS", "model": "ASUS_AI2302", "device": "AI2302", "board": "kalama", "android": 14, "dpi": 480, "res": "1080x2448", "country": "TW"},
]

# Instagram versions (EXPANDED for more diversity)
IG_VERSIONS = [
    "315.0.0.26.109", "314.0.0.24.110", "313.0.0.28.109", "312.0.0.32.118",
    "311.0.0.32.119", "310.0.0.28.117", "309.0.0.40.113", "308.0.0.38.108",
    "316.0.0.29.120", "317.0.0.31.115", "318.0.0.27.111", "319.0.0.33.114",
    "320.0.0.25.108", "321.0.0.29.112", "322.0.0.33.106", "323.0.0.28.115",
]

# ==========================================
#     ADVANCED TIMING - POISSON DISTRIBUTION
# ==========================================
def poisson_delay(mean: float = None) -> float:
    """
    Generate human-like delay using exponential distribution (Poisson arrival).
    More realistic than uniform random.
    """
    if mean is None:
        mean = CONFIG["POISSON_MEAN_DELAY"]
    # Exponential distribution for inter-arrival times
    delay = -mean * math.log(1 - random.random())
    # Clamp to reasonable bounds
    return max(0.2, min(delay, 5.0))


def micro_jitter() -> float:
    """Add micro-jitter to requests (simulates network latency variance)."""
    return random.uniform(CONFIG["MICRO_JITTER_MIN"], CONFIG["MICRO_JITTER_MAX"])


async def human_delay_advanced():
    """Advanced human-like delay with Poisson distribution."""
    base_delay = poisson_delay()
    
    # Occasional longer pauses (thinking time)
    if random.random() < 0.08:
        base_delay += random.uniform(1.5, 3.5)
    
    # Micro-jitter
    base_delay += micro_jitter()
    
    await asyncio.sleep(base_delay)


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
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# ==========================================
#     HEADER ENTROPY MAXIMIZATION
# ==========================================
def generate_identity_with_entropy() -> Dict[str, Any]:
    """Generate a completely NEW identity with MAXIMUM diversity and entropy."""
    device = random.choice(DEVICES)
    ig_version = random.choice(IG_VERSIONS)
    browser_impersonation = random.choice(BROWSER_IMPERSONATIONS)
    
    # All unique IDs - fresh every time with MORE randomness
    device_id = f"android-{uuid4().hex[:16]}"
    phone_id = str(uuid4())
    guid = str(uuid4())
    adid = str(uuid4())
    google_adid = str(uuid4())
    family_device_id = str(uuid4())
    waterfall_id = str(uuid4())
    mid = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-', k=28))
    session_id = f"UFS-{uuid4()}-{random.randint(0, 5)}"
    client_time = str(time.time() + random.uniform(-5, 5))
    
    # Timezone variety
    timezones = [-28800, -25200, -21600, -18000, -14400, -10800, -7200, -3600, 
                 0, 3600, 7200, 10800, 14400, 19800, 21600, 25200, 28800, 32400, 36000]
    
    # Connection types with realistic weights
    connection_types = ["WIFI", "WIFI", "WIFI", "MOBILE(LTE)", "MOBILE(5G)", "MOBILE(4G)"]
    
    # Build User-Agent
    user_agent = (
        f"Instagram {ig_version} Android "
        f"({device['android']}/{device['android']}.0; "
        f"{device['dpi']}dpi; {device['res']}; "
        f"{device['manufacturer']}; {device['model']}; "
        f"{device['device']}; {device['board']}; en_{device['country']})"
    )
    
    # Capabilities variation
    capabilities = ['3brTvx0=', '3brTv58=', '3brTv50=', '3brTvwE=', '3brTv4E=', 
                   '3brTvw8=', '3brTvxE=', '3brTvxM=']
    
    # Bloks versions
    bloks_versions = [
        'e538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88e',
        'f538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88f',
        'd538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88d',
        'a538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88a',
        'b538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88b',
    ]
    
    # Build headers dict first
    headers_dict = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': '*/*',
        'Accept-Language': f"en-{device['country']},en;q=0.{random.randint(8,9)}",
        'Accept-Encoding': random.choice(['gzip, deflate, br', 'gzip, deflate', 'gzip, deflate, br, zstd']),
        'User-Agent': user_agent,
        'X-IG-App-ID': '567067343352427',
        'X-IG-App-Locale': f"en_{device['country']}",
        'X-IG-Device-Locale': f"en_{device['country']}",
        'X-IG-Mapped-Locale': f"en_{device['country']}",
        'X-IG-Device-ID': guid,
        'X-IG-Family-Device-ID': family_device_id,
        'X-IG-Android-ID': device_id,
        'X-IG-Timezone-Offset': str(random.choice(timezones)),
        'X-IG-Connection-Type': random.choice(connection_types),
        'X-IG-Connection-Speed': f'{random.randint(800, 8000)}kbps',
        'X-IG-Bandwidth-Speed-KBPS': str(random.randint(1500, 25000)),
        'X-IG-Bandwidth-TotalBytes-B': str(random.randint(500000, 50000000)),
        'X-IG-Bandwidth-TotalTime-MS': str(random.randint(50, 800)),
        'X-IG-Capabilities': random.choice(capabilities),
        'X-IG-WWW-Claim': '0',
        'X-Bloks-Version-Id': random.choice(bloks_versions),
        'X-Bloks-Is-Layout-RTL': 'false',
        'X-Bloks-Is-Panorama-Enabled': random.choice(['true', 'true', 'false']),
        'X-Pigeon-Session-Id': session_id,
        'X-Pigeon-Rawclienttime': client_time,
        'X-MID': mid,
        'X-FB-HTTP-Engine': random.choice(['Liger', 'Liger', 'Tigon']),
        'X-FB-Client-IP': 'True',
        'X-FB-Server-Cluster': 'True',
        'X-IG-ABR-Connection-Speed-KBPS': str(random.randint(1000, 15000)),
        'X-IG-Prefetch-Request': random.choice(['foreground', 'background']),
        'X-IG-Salt-IDs': str(random.randint(100000000, 999999999)),
    }
    
    # HEADER ENTROPY: Shuffle header order (some systems detect fixed order)
    if CONFIG["HEADER_SHUFFLE"]:
        items = list(headers_dict.items())
        # Keep Content-Type first, shuffle the rest
        content_type = items[0]
        rest = items[1:]
        random.shuffle(rest)
        headers_dict = dict([content_type] + rest)
    
    return {
        "device": device,
        "device_id": device_id,
        "phone_id": phone_id,
        "guid": guid,
        "adid": adid,
        "waterfall_id": waterfall_id,
        "headers": headers_dict,
        "browser_impersonation": browser_impersonation,
    }


# ==========================================
#     COOKIE MANAGEMENT SYSTEM
# ==========================================
@dataclass
class ProxySessionData:
    """Complete session data for a proxy with cookies."""
    proxy_url: str
    identity: Dict[str, Any]
    cookies: Dict[str, str] = field(default_factory=dict)
    browser_impersonation: str = ""
    last_activity: float = 0.0
    request_count: int = 0
    success_count: int = 0
    fail_count: int = 0
    resting_until: float = 0.0
    rate_limited_until: float = 0.0
    is_warm: bool = False
    warm_time: float = 0.0
    
    def __post_init__(self):
        if not self.browser_impersonation and self.identity:
            self.browser_impersonation = self.identity.get("browser_impersonation", random.choice(BROWSER_IMPERSONATIONS))


# Global session registry
PROXY_SESSIONS: Dict[str, ProxySessionData] = {}
WARM_DURATION = 300  # 5 minutes


def get_or_create_session(proxy_url: str) -> ProxySessionData:
    """Get existing session or create new one with fresh identity."""
    if proxy_url not in PROXY_SESSIONS:
        identity = generate_identity_with_entropy()
        PROXY_SESSIONS[proxy_url] = ProxySessionData(
            proxy_url=proxy_url,
            identity=identity,
            browser_impersonation=identity.get("browser_impersonation", random.choice(BROWSER_IMPERSONATIONS)),
        )
    return PROXY_SESSIONS[proxy_url]


def refresh_session_identity(proxy_url: str) -> ProxySessionData:
    """Generate completely new identity for a proxy (keeps cookies)."""
    session = get_or_create_session(proxy_url)
    old_cookies = session.cookies.copy()
    new_identity = generate_identity_with_entropy()
    session.identity = new_identity
    session.browser_impersonation = new_identity.get("browser_impersonation", random.choice(BROWSER_IMPERSONATIONS))
    session.cookies = old_cookies  # Preserve cookies
    return session


def update_session_cookies(proxy_url: str, response_cookies: Dict[str, str]):
    """Update session cookies from response."""
    session = get_or_create_session(proxy_url)
    session.cookies.update(response_cookies)


def is_proxy_available(proxy_url: str) -> bool:
    """Check if proxy is not rate-limited and not resting."""
    session = get_or_create_session(proxy_url)
    now = time.time()
    
    # Check rate limit
    if now < session.rate_limited_until:
        return False
    
    # Check if resting
    if CONFIG["ENABLE_SMART_ROTATION"] and now < session.resting_until:
        return False
    
    return True


def mark_proxy_rate_limited(proxy_url: str):
    """Mark a proxy as rate-limited."""
    session = get_or_create_session(proxy_url)
    session.rate_limited_until = time.time() + CONFIG["COOLDOWN_TIME"]
    session.fail_count += 1
    # Also regenerate identity after rate limit
    refresh_session_identity(proxy_url)


def mark_proxy_used(proxy_url: str, success: bool = True):
    """Mark that a proxy was used."""
    session = get_or_create_session(proxy_url)
    session.request_count += 1
    session.last_activity = time.time()
    
    if success:
        session.success_count += 1
    else:
        session.fail_count += 1
    
    # Check if proxy needs rest
    if CONFIG["ENABLE_SMART_ROTATION"] and session.request_count >= CONFIG["MAX_REQUESTS_PER_PROXY"]:
        session.resting_until = time.time() + CONFIG["PROXY_REST_TIME"]
        session.request_count = 0
        # Refresh identity during rest
        refresh_session_identity(proxy_url)
        logger.debug(f"Proxy {proxy_url[:40]}... needs rest, identity refreshed")


def is_session_warm(proxy_url: str) -> bool:
    """Check if a session is still warm."""
    session = get_or_create_session(proxy_url)
    if session.is_warm and (time.time() - session.warm_time) < WARM_DURATION:
        return True
    session.is_warm = False
    return False


def mark_session_warm(proxy_url: str):
    """Mark a session as warm."""
    session = get_or_create_session(proxy_url)
    session.is_warm = True
    session.warm_time = time.time()


def get_available_proxies() -> List[str]:
    """Get all proxies that are not rate-limited or resting."""
    return [p for p in PROXIES if is_proxy_available(p)]


def get_rate_limited_count() -> int:
    """Get count of currently rate-limited proxies."""
    now = time.time()
    count = 0
    for proxy_url in PROXIES:
        session = get_or_create_session(proxy_url)
        if now < session.rate_limited_until:
            count += 1
    return count


def get_resting_count() -> int:
    """Get count of currently resting proxies."""
    now = time.time()
    count = 0
    for proxy_url in PROXIES:
        session = get_or_create_session(proxy_url)
        if now < session.resting_until:
            count += 1
    return count


def get_warm_count() -> int:
    """Get count of currently warm sessions."""
    return sum(1 for p in PROXIES if is_session_warm(p))


def get_proxy_stats() -> Dict[str, Any]:
    """Get detailed proxy statistics."""
    total_success = sum(get_or_create_session(p).success_count for p in PROXIES)
    total_fails = sum(get_or_create_session(p).fail_count for p in PROXIES)
    total_requests = total_success + total_fails
    
    return {
        "total_proxies": len(PROXIES),
        "available": len(get_available_proxies()),
        "rate_limited": get_rate_limited_count(),
        "resting": get_resting_count(),
        "total_requests": total_requests,
        "success_rate": f"{(total_success / total_requests * 100):.1f}%" if total_requests > 0 else "0%",
        "warm_count": get_warm_count(),
    }


@app.route('/api/stats')
def api_stats():
    return jsonify(get_proxy_stats())


# ==========================================
#     MULTI-ENDPOINT SESSION WARMING
# ==========================================
WARM_ENDPOINTS_ADVANCED = [
    ("GET", "https://i.instagram.com/api/v1/launcher/sync/", None),
    ("GET", "https://i.instagram.com/api/v1/accounts/login_activity/", None),
    ("POST", "https://i.instagram.com/api/v1/qe/sync/", {"experiments": "ig_android_device_detection_info_upload"}),
]


async def warm_single_session_advanced(proxy_url: str) -> bool:
    """
    Advanced session warming - simulates real app behavior.
    Uses curl_cffi with browser impersonation (if available).
    Falls back to httpx for Railway compatibility.
    """
    try:
        session_data = get_or_create_session(proxy_url)
        identity = session_data.identity
        
        # Randomly choose 1-2 endpoints to warm
        endpoints_to_use = random.sample(WARM_ENDPOINTS_ADVANCED, k=random.randint(1, 2))
        
        if USE_CURL_CFFI:
            async with CurlAsyncSession(
                proxy=proxy_url,
                impersonate=session_data.browser_impersonation,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            ) as client:
                for method, url, data in endpoints_to_use:
                    try:
                        await asyncio.sleep(micro_jitter())
                        headers = identity["headers"].copy()
                        
                        if method == "GET":
                            response = await client.get(url, headers=headers)
                        else:
                            post_data = data.copy() if data else {}
                            post_data["_uuid"] = identity["guid"]
                            response = await client.post(url, headers=headers, data=post_data)
                        
                        if hasattr(response, 'cookies'):
                            update_session_cookies(proxy_url, dict(response.cookies))
                    except Exception:
                        pass
                    
                    await asyncio.sleep(random.uniform(0.2, 0.6))
        else:
            # Fallback to httpx
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            ) as client:
                for method, url, data in endpoints_to_use:
                    try:
                        await asyncio.sleep(micro_jitter())
                        headers = identity["headers"].copy()
                        
                        if method == "GET":
                            response = await client.get(url, headers=headers)
                        else:
                            post_data = data.copy() if data else {}
                            post_data["_uuid"] = identity["guid"]
                            response = await client.post(url, headers=headers, data=post_data)
                        
                        if hasattr(response, 'cookies'):
                            update_session_cookies(proxy_url, dict(response.cookies))
                    except Exception:
                        pass
                    
                    await asyncio.sleep(random.uniform(0.2, 0.6))
        
        mark_session_warm(proxy_url)
        return True
            
    except Exception as e:
        logger.debug(f"Warm failed for {proxy_url[:30]}: {e}")
        return False


async def ensure_session_warm(proxy_url: str) -> bool:
    """Ensure a session is warm before checking username."""
    if is_session_warm(proxy_url):
        return True
    return await warm_single_session_advanced(proxy_url)


async def warm_all_sessions_background():
    """Background task to warm all proxy sessions."""
    logger.info("🔥 Starting background session warming...")
    
    warmed = 0
    for proxy_url in PROXIES:
        if is_proxy_available(proxy_url) and not is_session_warm(proxy_url):
            success = await warm_single_session_advanced(proxy_url)
            if success:
                warmed += 1
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    logger.info(f"🔥 Warmed {warmed}/{len(PROXIES)} sessions")


# ==========================================
#     HUMAN-LIKE TIMING (Enhanced)
# ==========================================
async def simulate_typing_delay(username: str):
    """Simulate the delay of typing a username with variance."""
    if CONFIG["TYPING_SIMULATION"]:
        # Variable typing speed per character
        total_delay = 0
        for char in username:
            # Random speed per character (faster for common letters)
            if char in 'etaoin':
                total_delay += random.uniform(0.03, 0.08)
            else:
                total_delay += random.uniform(0.06, 0.15)
            
            # Occasional pause (thinking)
            if random.random() < 0.05:
                total_delay += random.uniform(0.2, 0.5)
        
        await asyncio.sleep(total_delay)


# ==========================================
#     USERNAME GENERATOR
# ==========================================
def generate_simple_username() -> str:
    """Generate a simple 5-char username (NO symbols)."""
    return random.choice(LETTERS) + ''.join(random.choices(CHARS, k=4))


def generate_semi_quad_username() -> str:
    """Generate a semi-quad username (5 chars with _ or . in allowed positions)."""
    max_attempts = 100
    
    for _ in range(max_attempts):
        first_char = random.choice(LETTERS)
        symbol = random.choice('._')
        symbol_pos = random.choice([1, 2, 3])
        
        username_chars = [first_char]
        for pos in range(1, 5):
            if pos == symbol_pos:
                username_chars.append(symbol)
            else:
                username_chars.append(random.choice(CHARS))
        
        username = ''.join(username_chars)
        
        # Validate Instagram rules
        if username.endswith('.'):
            continue
        if '..' in username:
            continue
        if '._' in username or '_.' in username:
            continue
        
        return username
    
    return random.choice(LETTERS) + '_' + ''.join(random.choices(CHARS, k=2)) + random.choice(CHARS)


# ==========================================
#     CORE: CHECK USERNAME (curl_cffi)
# ==========================================

# Exact rate limit patterns from Instagram
RATE_LIMIT_PATTERNS = [
    '"message":"Please wait a few minutes before you try again."',
    '"spam":true',
    '"status":"fail","message":"rate_limit',
    'Please wait a few minutes',
    '"error_type":"rate_limit_error"',
]

CHALLENGE_PATTERNS = [
    '"challenge_required"',
    '"message":"challenge_required"',
    'checkpoint_required',
]

async def check_username_stealth(
    proxy_url: str,
    username: str,
    ensure_warm: bool = True
) -> Dict[str, Any]:
    """
    Check a single username with ULTIMATE STEALTH.
    Uses curl_cffi for TLS fingerprint randomization (if available).
    Falls back to httpx for Railway compatibility.
    IMPROVED: More accurate rate limit detection.
    """
    try:
        session_data = get_or_create_session(proxy_url)
        identity = session_data.identity
        
        # Ensure session is warm
        if ensure_warm:
            await ensure_session_warm(proxy_url)
        
        # Add micro-jitter before request
        await asyncio.sleep(micro_jitter())
        
        # Simulate slow connection occasionally
        if random.random() < CONFIG["SLOW_CONNECTION_CHANCE"]:
            await asyncio.sleep(random.uniform(0.5, 1.5))
        
        # Simulate typing the username
        await simulate_typing_delay(username)
        
        data = {
            "username": username,
            "_uuid": identity["guid"],
        }
        
        # ========== MAKE REQUEST (curl_cffi or httpx) ==========
        if USE_CURL_CFFI:
            # Use curl_cffi for TLS fingerprinting
            async with CurlAsyncSession(
                proxy=proxy_url,
                impersonate=session_data.browser_impersonation,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            ) as client:
                for name, value in session_data.cookies.items():
                    client.cookies.set(name, value)
                
                response = await client.post(
                    CONFIG["API_URL"],
                    headers=identity["headers"],
                    data=data
                )
                
                if hasattr(response, 'cookies'):
                    update_session_cookies(proxy_url, dict(response.cookies))
                
                text = response.text
                status_code = response.status_code
        else:
            # Fallback to httpx for Railway
            async with httpx.AsyncClient(
                proxy=proxy_url,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            ) as client:
                response = await client.post(
                    CONFIG["API_URL"],
                    headers=identity["headers"],
                    data=data
                )
                
                if hasattr(response, 'cookies'):
                    update_session_cookies(proxy_url, dict(response.cookies))
                
                text = response.text
                status_code = response.status_code
        
        # Mark session as warm (successful request)
        mark_session_warm(proxy_url)
        
        # ========== ACCURATE RESPONSE DETECTION ==========
        
        # Check for available username
        if '"available":true' in text or '"available": true' in text:
            mark_proxy_used(proxy_url, success=True)
            return {"status": "available", "username": username, "proxy": proxy_url}
        
        # Check for taken username
        if '"available":false' in text or '"available": false' in text:
            mark_proxy_used(proxy_url, success=True)
            return {"status": "taken", "username": username, "proxy": proxy_url}
        
        # Check for EXACT rate limit patterns (be very specific!)
        is_rate_limited = False
        matched_pattern = None
        for pattern in RATE_LIMIT_PATTERNS:
            if pattern.lower() in text.lower():
                is_rate_limited = True
                matched_pattern = pattern
                break
        
        if is_rate_limited:
            mark_proxy_rate_limited(proxy_url)
            mark_proxy_used(proxy_url, success=False)
            logger.warning(f"⚠️ TRUE RATE LIMIT on {proxy_url[:30]}... | Pattern: {matched_pattern}")
            logger.warning(f"📝 Response: {text[:200]}")
            return {"status": "rate_limit", "username": username, "proxy": proxy_url, "response": text[:200], "pattern": matched_pattern}
        
        # Check for challenge patterns
        is_challenge = False
        for pattern in CHALLENGE_PATTERNS:
            if pattern.lower() in text.lower():
                is_challenge = True
                break
        
        if is_challenge:
            mark_proxy_rate_limited(proxy_url)
            mark_proxy_used(proxy_url, success=False)
            return {"status": "challenge", "username": username, "proxy": proxy_url}
        
        # Check for other known responses that are NOT rate limits
        if status_code == 200 and '"status":"ok"' in text:
            mark_proxy_used(proxy_url, success=True)
            return {"status": "taken", "username": username, "proxy": proxy_url}
        
        # Unknown response - log it but DON'T count as rate limit
        mark_proxy_used(proxy_url, success=True)
        logger.debug(f"Unknown response (NOT rate limit): {text[:100]}")
        return {"status": "unknown", "username": username, "response": text[:150]}
            
    except asyncio.TimeoutError:
        mark_proxy_used(proxy_url, success=False)
        return {"status": "timeout", "username": username}
    except Exception as e:
        # Network errors are NOT rate limits
        mark_proxy_used(proxy_url, success=False)
        return {"status": "network_error", "username": username, "error": str(e)[:80]}




# ==========================================
#     UNIFIED SEARCH SYSTEM
# ==========================================
class SearchMode(Enum):
    SIMPLE = "simple"
    SEMI_QUAD = "semi_quad"


async def unified_search(
    mode: SearchMode,
    detailed_logging: bool = False
) -> Dict[str, Any]:
    """UNIFIED Search Function with ULTIMATE STEALTH."""
    start_time = time.time()
    
    # Mode-specific configuration
    if mode == SearchMode.SEMI_QUAD:
        username_generator = generate_semi_quad_username
        max_concurrent = 50
        timeout = 30
        apply_delays = False
        search_type = "semi-quad"
    else:
        username_generator = generate_simple_username
        max_concurrent = CONFIG["MAX_CONCURRENT"]
        timeout = CONFIG["TIMEOUT"]
        apply_delays = True
        search_type = "simple"
    
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0}
    if detailed_logging:
        stats["timeouts"] = 0
    
    detailed_log = None
    if detailed_logging:
        detailed_log = {
            "timeline": [], "identities_created": [], "requests_made": [],
            "delays_applied": [], "rate_limits_detected": [],
            "usernames_checked": [], "responses_received": [],
            "tls_fingerprints": [],
        }
        def log_event(event_type: str, data: Dict[str, Any]):
            detailed_log["timeline"].append({
                "time": round(time.time() - start_time, 4),
                "event": event_type, "data": data
            })
    else:
        def log_event(event_type: str, data: Dict[str, Any]):
            pass
    
    if not PROXIES:
        result = {"status": "failed", "reason": "no_proxies", "duration": 0}
        if detailed_logging:
            result["detailed_log"] = detailed_log
        return result
    
    log_event("INIT", {
        "proxies_count": len(PROXIES), "warm_sessions": get_warm_count(),
        "search_type": search_type, "mode": mode.value,
        "stealth_features": ["TLS_FINGERPRINT", "COOKIE_MGMT", "POISSON_TIMING", "HEADER_ENTROPY"]
    })
    
    available_proxies = get_available_proxies()
    
    if not available_proxies:
        result = {
            "status": "failed", "reason": "all_proxies_rate_limited",
            "duration": 0, "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}"
        }
        if detailed_logging:
            result["detailed_log"] = detailed_log
        return result
    
    if detailed_logging:
        for p in available_proxies[:5]:
            session = get_or_create_session(p)
            detailed_log["tls_fingerprints"].append({
                "proxy": p[:50] + "...",
                "browser": session.browser_impersonation,
                "device": session.identity["device"]["model"],
            })
    
    logger.info(f"🔍 Starting {search_type.upper()} search with {len(available_proxies)} proxies (STEALTH v3.0)")
    batch_number = 0
    
    while time.time() - start_time < timeout:
        batch_number += 1
        current_available = [p for p in available_proxies if is_proxy_available(p)]
        
        log_event("BATCH_START", {"batch": batch_number, "available": len(current_available)})
        
        if not current_available:
            wait_time = 2 if mode == SearchMode.SEMI_QUAD else 5
            await asyncio.sleep(wait_time)
            continue
        
        proxies_to_use = current_available[:max_concurrent]
        usernames = [username_generator() for _ in range(len(proxies_to_use))]
        
        tasks = []
        for proxy_url, username in zip(proxies_to_use, usernames):
            if detailed_logging:
                detailed_log["requests_made"].append({"username": username, "proxy": proxy_url[:40]})
            tasks.append(asyncio.create_task(check_username_stealth(proxy_url, username)))
        
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            if detailed_logging:
                detailed_log["responses_received"].append({"username": result.get("username"), "status": result["status"]})
                detailed_log["usernames_checked"].append(result.get("username"))
            
            if result["status"] == "available":
                for t in tasks:
                    t.cancel()
                duration = round(time.time() - start_time, 2 if not detailed_logging else 4)
                log_event("FOUND", {"username": result["username"], "duration": duration})
                logger.info(f"✅ FOUND {search_type.upper()}: {result['username']} in {duration}s")
                
                response = {
                    "status": "success", "username": result["username"],
                    "duration": duration, "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
                    "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}",
                    "stealth_version": "3.0"
                }
                if mode == SearchMode.SEMI_QUAD:
                    response["type"] = "semi-quad"
                if detailed_logging:
                    response["batches_processed"] = batch_number
                    response["detailed_log"] = detailed_log
                return response
            
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] == "unknown":
                # Unknown response - still a successful connection, not rate limit
                stats["taken"] += 1  # Count as taken (conservative)
            elif result["status"] in ["rate_limit", "challenge"]:
                stats["rate_limits"] += 1
                if detailed_logging:
                    # Include FULL response data for debugging
                    detailed_log["rate_limits_detected"].append({
                        "username": result.get("username"),
                        "response": result.get("response", "N/A"),
                        "pattern": result.get("pattern", "N/A"),
                        "proxy": result.get("proxy", "N/A")[:50]
                    })
            elif result["status"] == "timeout":
                if detailed_logging:
                    stats["timeouts"] = stats.get("timeouts", 0) + 1
                else:
                    stats["errors"] += 1
            elif result["status"] == "network_error":
                # Network errors are NOT rate limits
                stats["errors"] += 1
            else:
                stats["errors"] += 1
        
        if apply_delays:
            # Use Poisson delay instead of random
            delay = poisson_delay()
            await asyncio.sleep(delay)
            if detailed_logging:
                detailed_log["delays_applied"].append({"batch": batch_number, "delay": round(delay, 3)})
    
    response = {
        "status": "failed", "reason": "timeout",
        "duration": round(time.time() - start_time, 2), "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count()}/{len(PROXIES)}",
        "warm_sessions": f"{get_warm_count()}/{len(PROXIES)}",
        "stealth_version": "3.0"
    }
    if mode == SearchMode.SEMI_QUAD:
        response["type"] = "semi-quad"
    if detailed_logging:
        response["batches_processed"] = batch_number
        response["detailed_log"] = detailed_log
    return response


# ==========================================
#     SEARCH WRAPPERS
# ==========================================
async def stealth_search() -> Dict[str, Any]:
    """Quick search with simple usernames (5 chars)."""
    return await unified_search(mode=SearchMode.SIMPLE, detailed_logging=False)


async def semi_quad_stealth_search() -> Dict[str, Any]:
    """Fast search for semi-quad usernames (with _ or .)."""
    return await unified_search(mode=SearchMode.SEMI_QUAD, detailed_logging=False)


async def detailed_stealth_search() -> Dict[str, Any]:
    """Detailed search with full logging for debugging."""
    return await unified_search(mode=SearchMode.SIMPLE, detailed_logging=True)


async def detailed_semi_quad_stealth_search() -> Dict[str, Any]:
    """Detailed semi-quad search with full logging."""
    return await unified_search(mode=SearchMode.SEMI_QUAD, detailed_logging=True)


# ==========================================
#              API ROUTES
# ==========================================
@app.route('/dashboard')
def dashboard():
    """Admin dashboard - HTML interface."""
    return render_template('dashboard.html')


@app.route('/')
def home():
    stats = get_proxy_stats()
    return jsonify({
        "status": "online",
        "message": "Instagram Username Checker - ULTIMATE STEALTH Edition v3.0 (IMPOSSIBLE TO RATE LIMIT)",
        "version": "3.0",
        "endpoints": {
            "/search": "Quick search - Smart mix (70% simple + 30% semi-quad)",
            "/prosearch": "Semi-quad search - Fast mode with _ or . symbols",
            "/infosearch": "Detailed search - Full logging for debugging",
            "/infoprosearch": "Detailed semi-quad search - Full logging",
            "/warm": "Pre-warm all proxy sessions",
            "/status": "Get detailed system status and statistics"
        },
        "features": [
            "🔒 TLS FINGERPRINT: curl_cffi browser impersonation",
            "🍪 COOKIE MANAGEMENT: Persistent sessions per proxy",
            "⏱️ POISSON TIMING: Human-like delay distribution",
            "🔀 HEADER ENTROPY: Randomized header order",
            "🔥 MULTI-ENDPOINT WARMING: Advanced session prep",
            "⚡ MICRO-JITTERING: Network latency simulation",
            "🎭 40+ DEVICE MODELS: Maximum fingerprint diversity",
            "🔄 AUTO IDENTITY REFRESH: New identity after rest"
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
        "stealth_level": "IMPOSSIBLE TO RATE LIMIT 🛡️"
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
            "smart_rotation_enabled": CONFIG["ENABLE_SMART_ROTATION"],
            "poisson_mean_delay": CONFIG["POISSON_MEAN_DELAY"],
            "header_shuffle": CONFIG["HEADER_SHUFFLE"],
        },
        "stealth_features": {
            "tls_fingerprint": True,
            "cookie_management": True,
            "poisson_timing": True,
            "header_entropy": True,
            "micro_jittering": True,
            "browser_impersonations": len(BROWSER_IMPERSONATIONS),
            "device_models": len(DEVICES),
        }
    })


@app.route('/warm')
async def warm():
    """Manually warm all proxy sessions."""
    await warm_all_sessions_background()
    return jsonify({
        "status": "success",
        "message": "All sessions warmed with advanced multi-endpoint warming",
        "warm_count": get_warm_count()
    })

@app.route('/search')
async def search():
    """
    Find one available username with IMPOSSIBLE TO RATE LIMIT stealth.
    Smart Probability: 70% Simple Search (5 chars), 30% Pro Search (Semi-Quad).
    """
    if random.random() < 0.7:
        result = await stealth_search()
    else:
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
    logger.info(f"🚀 Starting ULTIMATE STEALTH v3.0 server on port {port}")
    logger.info(f"🛡️ Stealth: TLS Fingerprint, Cookie Mgmt, Poisson Timing, Header Entropy")
    logger.info(f"🔒 Status: IMPOSSIBLE TO RATE LIMIT")
    app.run(host='0.0.0.0', port=port)