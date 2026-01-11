#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - Clean & Fast API
==============================================

Simple, fast, and reliable username checking.
Stops IMMEDIATELY when first available username is found.

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4
from dataclasses import dataclass

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
    "TIMEOUT": 30,
    "REQUEST_TIMEOUT": 5.0,
    "PROXIES_FILE": "proxies.txt",
}

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# Android devices database
DEVICES = [
    {"manufacturer": "Samsung", "model": "SM-G998B", "device": "p3s", "board": "exynos2100", "android": 13, "dpi": 640, "res": "1440x3200"},
    {"manufacturer": "Samsung", "model": "SM-A525F", "device": "a52q", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2340"},
    {"manufacturer": "Google", "model": "Pixel 7 Pro", "device": "cheetah", "board": "google", "android": 14, "dpi": 560, "res": "1440x3120"},
    {"manufacturer": "Google", "model": "Pixel 6a", "device": "bluejay", "board": "google", "android": 13, "dpi": 420, "res": "1080x2400"},
    {"manufacturer": "OnePlus", "model": "LE2123", "device": "lemonadep", "board": "lahaina", "android": 13, "dpi": 560, "res": "1440x3216"},
    {"manufacturer": "Xiaomi", "model": "M2101K6G", "device": "sweet", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2400"},
    {"manufacturer": "OPPO", "model": "CPH2207", "device": "OP4F7C", "board": "mt6893", "android": 12, "dpi": 480, "res": "1080x2400"},
]

IG_VERSIONS = ["269.0.0.18.75", "268.0.0.23.118", "267.0.0.19.93", "266.0.0.22.105", "265.0.0.19.301"]

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
#              FULL DEVICE FINGERPRINT
# ==========================================
@dataclass
class Identity:
    """Complete Android device identity for maximum stealth."""
    user_agent: str
    device_id: str
    phone_id: str
    guid: str
    adid: str
    google_adid: str
    family_device_id: str
    headers: Dict[str, str]

def generate_identity() -> Identity:
    """
    Generate a COMPLETE device identity for maximum stealth.
    Simulates a real Android device with all fingerprint data.
    """
    device = random.choice(DEVICES)
    version = random.choice(IG_VERSIONS)
    
    # Generate all unique IDs
    device_id = f"android-{uuid4().hex[:16]}"
    phone_id = str(uuid4())
    guid = str(uuid4())
    adid = str(uuid4())  # Google Advertising ID
    google_adid = str(uuid4())
    family_device_id = str(uuid4())
    
    # Build realistic User-Agent
    user_agent = (
        f"Instagram {version} Android "
        f"({device['android']}/{device['android']}.0; "
        f"{device['dpi']}dpi; {device['res']}; "
        f"{device['manufacturer']}; {device['model']}; "
        f"{device['device']}; {device['board']}; en_US)"
    )
    
    # Complete headers for maximum stealth
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept-Language': random.choice(['en-US', 'en-GB', 'en-CA', 'en-AU', 'en-IN']),
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': user_agent,
        'X-IG-App-ID': '567067343352427',
        'X-IG-App-Locale': 'en_US',
        'X-IG-Device-Locale': 'en_US',
        'X-IG-Device-ID': guid,
        'X-IG-Android-ID': device_id,
        'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G', 'MOBILE.4G']),
        'X-IG-Connection-Speed': f'{random.randint(1000, 5000)}kbps',
        'X-IG-Bandwidth-Speed-KBPS': str(random.randint(2000, 10000)),
        'X-IG-Bandwidth-TotalBytes-B': str(random.randint(1000000, 8000000)),
        'X-IG-Bandwidth-TotalTime-MS': str(random.randint(50, 300)),
        'X-IG-Capabilities': random.choice(['3brTvx0=', '3brTvwE=', '3brTvw8=']),
        'X-Bloks-Version-Id': 'ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6a9c9e',
        'X-Bloks-Is-Layout-RTL': 'false',
        'X-Pigeon-Session-Id': f'UFS-{uuid4()}-0',
        'X-Pigeon-Rawclienttime': str(time.time()),
        'X-MID': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', k=28)),
    }
    
    return Identity(
        user_agent=user_agent,
        device_id=device_id,
        phone_id=phone_id,
        guid=guid,
        adid=adid,
        google_adid=google_adid,
        family_device_id=family_device_id,
        headers=headers
    )

# ==========================================
#              USERNAME GENERATOR
# ==========================================
def generate_username() -> str:
    """
    Generate a valid 5-character username containing _ or . (or both).
    
    Instagram rules:
    - Cannot start with .
    - Cannot end with .
    - No consecutive special chars (.. ._ _. __)
    """
    # Valid patterns for 5-char username with special char
    # Position 0: must be letter
    # Position 4: cannot be dot
    # No consecutive specials
    
    patterns = [
        # Single underscore patterns
        "L_LLL", "LL_LL", "LLL_L", "LLLL_",
        # Single dot patterns (not at end)
        "L.LLL", "LL.LL", "LLL.L",
        # Underscore + dot combinations (not consecutive)
        "L_L.L", "L.L_L", "L_LL_",
    ]
    
    pattern = random.choice(patterns)
    result = []
    
    for char in pattern:
        if char == 'L':
            # Letter or digit (but first must be letter)
            if len(result) == 0:
                result.append(random.choice(LETTERS))
            else:
                result.append(random.choice(CHARS))
        elif char == '_':
            result.append('_')
        elif char == '.':
            result.append('.')
    
    return ''.join(result)

# ==========================================
#              CORE: CHECK ONE USERNAME
# ==========================================
async def check_one_username(client: httpx.AsyncClient, username: str, identity: Identity, proxy_index: int) -> Dict[str, Any]:
    """Check a single username. Returns result dict with proxy_index."""
    try:
        data = {"username": username, "_uuid": identity.guid}
        response = await client.post(CONFIG["API_URL"], headers=identity.headers, data=data)
        text = response.text
        
        if '"available":true' in text or '"available": true' in text:
            return {"status": "available", "username": username, "proxy_index": proxy_index}
        elif '"available":false' in text or '"available": false' in text:
            return {"status": "taken", "username": username, "proxy_index": proxy_index}
        elif 'wait a few minutes' in text.lower():
            return {"status": "rate_limit", "username": username, "proxy_index": proxy_index}
        else:
            return {"status": "error", "username": username, "proxy_index": proxy_index}
            
    except httpx.TimeoutException:
        return {"status": "timeout", "username": username, "proxy_index": proxy_index}
    except Exception as e:
        return {"status": "error", "username": username, "proxy_index": proxy_index}

# ==========================================
#              CORE: SEARCH (SIMPLE & FAST)
# ==========================================
async def search_available_username() -> Dict[str, Any]:
    """
    Search for ONE available username.
    Stops IMMEDIATELY when found.
    """
    start_time = time.time()
    stats = {"checked": 0, "taken": 0, "errors": 0}
    rate_limited_proxies = set()  # Track unique proxies with rate limits
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "duration": 0}
    
    # Create a client pool (one per proxy) - use ALL proxies
    clients = []
    for proxy in PROXIES:
        try:
            clients.append(httpx.AsyncClient(proxy=proxy, timeout=CONFIG["REQUEST_TIMEOUT"]))
        except:
            pass
    
    if not clients:
        return {"status": "failed", "reason": "no_valid_proxies", "duration": 0}
    
    logger.info(f"Starting search with {len(clients)} proxies...")
    
    try:
        batch_size = len(clients)
        
        while time.time() - start_time < CONFIG["TIMEOUT"]:
            # Generate batch of usernames
            usernames = [generate_username() for _ in range(batch_size)]
            
            # Create tasks with proxy index
            tasks = []
            for i, username in enumerate(usernames):
                proxy_index = i % len(clients)
                client = clients[proxy_index]
                identity = generate_identity()
                tasks.append(asyncio.create_task(check_one_username(client, username, identity, proxy_index)))
            
            # Process results AS THEY COME IN - return immediately on first available!
            for coro in asyncio.as_completed(tasks):
                result = await coro
                stats["checked"] += 1
                
                if result["status"] == "available":
                    # Cancel remaining tasks
                    for t in tasks:
                        t.cancel()
                    
                    duration = round(time.time() - start_time, 2)
                    logger.info(f"✅ FOUND: {result['username']} in {duration}s after {stats['checked']} checks")
                    
                    return {
                        "status": "success",
                        "username": result["username"],
                        "duration": duration,
                        "stats": stats,
                        "rate_limited_proxies": f"{len(rate_limited_proxies)}/{len(clients)}"
                    }
                elif result["status"] == "taken":
                    stats["taken"] += 1
                elif result["status"] == "rate_limit":
                    rate_limited_proxies.add(result["proxy_index"])
                else:
                    stats["errors"] += 1
        
        # Timeout
        return {
            "status": "failed",
            "reason": "timeout",
            "duration": round(time.time() - start_time, 2),
            "stats": stats,
            "rate_limited_proxies": f"{len(rate_limited_proxies)}/{len(clients)}"
        }
        
    finally:
        # Cleanup
        for client in clients:
            try:
                await client.aclose()
            except:
                pass

# ==========================================
#              API ROUTES
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Instagram Username Checker - Clean & Fast",
        "usage": "GET /search",
        "proxies": len(PROXIES)
    })

@app.route('/search')
async def search():
    """Find one available username."""
    result = await search_available_username()
    return jsonify(result)

# ==========================================
#              MAIN
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port)