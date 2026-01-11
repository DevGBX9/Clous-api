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
#              IDENTITY GENERATOR
# ==========================================
@dataclass
class Identity:
    user_agent: str
    guid: str
    headers: Dict[str, str]

def generate_identity() -> Identity:
    """Generate a fresh device identity."""
    device = random.choice(DEVICES)
    version = random.choice(IG_VERSIONS)
    guid = str(uuid4())
    
    user_agent = (
        f"Instagram {version} Android "
        f"({device['android']}/{device['android']}.0; "
        f"{device['dpi']}dpi; {device['res']}; "
        f"{device['manufacturer']}; {device['model']}; "
        f"{device['device']}; {device['board']}; en_US)"
    )
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept-Language': 'en-US',
        'Accept-Encoding': 'gzip, deflate',
        'User-Agent': user_agent,
        'X-IG-App-ID': '567067343352427',
        'X-IG-Device-ID': guid,
        'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE']),
    }
    
    return Identity(user_agent=user_agent, guid=guid, headers=headers)

# ==========================================
#              USERNAME GENERATOR
# ==========================================
def generate_username() -> str:
    """Generate a valid 5-character username."""
    # Start with letter, then 4 alphanumeric
    return random.choice(LETTERS) + ''.join(random.choices(CHARS, k=4))

# ==========================================
#              CORE: CHECK ONE USERNAME
# ==========================================
async def check_one_username(client: httpx.AsyncClient, username: str, identity: Identity) -> Dict[str, Any]:
    """Check a single username. Returns result dict."""
    try:
        data = {"username": username, "_uuid": identity.guid}
        response = await client.post(CONFIG["API_URL"], headers=identity.headers, data=data)
        text = response.text
        
        if '"available":true' in text or '"available": true' in text:
            return {"status": "available", "username": username, "response": text}
        elif '"available":false' in text or '"available": false' in text:
            return {"status": "taken", "username": username}
        elif 'wait a few minutes' in text.lower():
            return {"status": "rate_limit", "username": username}
        else:
            return {"status": "error", "username": username, "response": text[:200]}
            
    except httpx.TimeoutException:
        return {"status": "timeout", "username": username}
    except Exception as e:
        return {"status": "error", "username": username, "error": str(e)[:100]}

# ==========================================
#              CORE: SEARCH (SIMPLE & FAST)
# ==========================================
async def search_available_username() -> Dict[str, Any]:
    """
    Search for ONE available username.
    Stops IMMEDIATELY when found.
    """
    start_time = time.time()
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0}
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "duration": 0}
    
    # Create a client pool (one per proxy)
    clients = []
    for proxy in PROXIES[:30]:  # Use max 30 proxies for speed
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
            
            # Create tasks
            tasks = []
            for i, username in enumerate(usernames):
                client = clients[i % len(clients)]
                identity = generate_identity()
                tasks.append(asyncio.create_task(check_one_username(client, username, identity)))
            
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
                        "stats": stats
                    }
                elif result["status"] == "taken":
                    stats["taken"] += 1
                elif result["status"] == "rate_limit":
                    stats["rate_limits"] += 1
                else:
                    stats["errors"] += 1
        
        # Timeout
        return {
            "status": "failed",
            "reason": "timeout",
            "duration": round(time.time() - start_time, 2),
            "stats": stats
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