#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API
==========================================

This script runs a Flask API that checks for available 5-character Instagram usernames.
It is designed to be deployed on serverless/container environments like Render.

Features:
- On-Demand Search: Triggered via /search endpoint.
- High Concurrency: Uses ThreadPoolExecutor for rapid checking.
- Smart Stopping: Stops immediately upon finding a user, hitting a rate limit, or timing out.
- Decoupled Frontend: Serves a JSON API; frontend logic is in index.html.
- Anonymity: Rotating Proxies, Random User-Agents, Dynamic Device IDs.

Author: @GBX_9 (Original Helper)
"""

import os
import sys
import time
import random
import asyncio
import httpx
import itertools
from uuid import uuid4
from flask import Flask, jsonify
from flask_cors import CORS

# Prevent Python from writing __pycache__ bytecode files
sys.dont_write_bytecode = True

# ==========================================
#              CONFIGURATION
# ==========================================
CONFIG = {
    "INSTAGRAM_API_URL": 'https://i.instagram.com/api/v1/accounts/create/',
    "TIMEOUT_SECONDS": 30,
    "FIXED_EMAIL": "abdo1@gmail.com",
    "MAX_CONCURRENCY": 100,  # Increased for async
    "FIREBASE_STABLE_PROXIES_URL": "https://clous-proxys-qpi-default-rtdb.firebaseio.com/stable_proxies.json",
    "FIREBASE_MAIN_PROXIES_URL": "https://clous-proxys-qpi-default-rtdb.firebaseio.com/proxies.json",
}

# Values for username generation
CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

async def fetch_proxies():
    """
    Fetches the latest proxies from Firebase.
    Prioritizes 'stable_proxies', falls back to 'proxies' if empty.
    Returns a list of formatted proxy URLs.
    """
    # Order of priority: Stable first, then Main pool
    endpoints = [
        CONFIG["FIREBASE_STABLE_PROXIES_URL"],
        CONFIG["FIREBASE_MAIN_PROXIES_URL"]
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for url in endpoints:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        proxies = []
                        for item in data.values():
                            addr = item.get('address')
                            if addr:
                                proxies.append(f"http://{addr}")
                        if proxies:
                            print(f"Successfully fetched {len(proxies)} proxies from {url.split('/')[-1]}")
                            return proxies
            except Exception as e:
                print(f"Error fetching from {url}: {e}")
                continue
    return []


# Expanded User Agents
USER_AGENTS = [
    'Instagram 6.12.1 Android (30/11; 480dpi; 1080x2298; HONOR; ANY-LX2; HNANY-Q1; qcom; en_IQ)',
    'Instagram 10.20.0 Android (28/9; 420dpi; 1080x1920; Samsung; SM-G930F; heroqltesq; qcom; en_US)',
    'Instagram 9.7.0 Android (26/8; 480dpi; 1080x1920; OnePlus; ONEPLUS A6000; A6000; qcom; en_GB)',
    'Instagram 254.0.0.19.109 Android (31/12; 440dpi; 1080x2340; Samsung; SM-A525F; a52q; qcom; en_US)',
    'Instagram 223.0.0.12.102 Android (30/11; 420dpi; 1080x2400; Xiaomi; M2101K6G; sweet; qcom; en_US)',
    'Instagram 219.0.0.12.117 Android (29/10; 450dpi; 1080x2400; OPPO; CPH2083; OP4C2F; mt6765; en_IN)',
    'Instagram 250.0.0.21.109 Android (33/13; 560dpi; 1440x3200; Google; Pixel 6 Pro; raven; google; en_US)',
    'Instagram 198.0.0.32.120 Android (27/8.1.0; 320dpi; 720x1280; HUAWEI; DUB-LX1; HWY9; hisilicon; en_US)',
]

HEADERS_TEMPLATE = {
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept-Language': 'en-US',
    'X-IG-Capabilities': 'AQ==',
    'Accept-Encoding': 'gzip',
}

# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for decoupled frontend access


# ==========================================
#              CORE LOGIC
# ==========================================

class AutoUsernameGenerator:
    """
    Responsible for generating valid 5-character Instagram usernames.
    """
    def __init__(self):
        self.generated_usernames = set()
    
    def is_valid_instagram_username(self, username):
        """
        Validates username against Instagram's rules.
        """
        if len(username) != 5:
            return False
        
        allowed_chars = set(CHARS["ALL_VALID"] + CHARS["SYMBOLS"])
        if not all(char in allowed_chars for char in username):
            return False
        
        if username.startswith('.') or username.endswith('.'):
            return False
        
        if '..' in username or '._' in username or '_.' in username:
            return False
        
        if username[0] in CHARS["DIGITS"]:
            return False
        
        return True
    
    def generate(self):
        """
        Generates a unique, compliant 5-char username.
        """
        max_attempts = 10
        for _ in range(max_attempts):
            username = random.choice(CHARS["LETTERS"])
            username += ''.join(random.choices(CHARS["ALL_VALID"], k=4))
            
            if (username not in self.generated_usernames and 
                self.is_valid_instagram_username(username)):
                self.generated_usernames.add(username)
                return username
        
        timestamp = int(time.time() * 1000) % 10000
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:04d}"[:5]
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    """
    Handles the HTTP communication with Instagram APIs.
    Uses Rotating Proxies and Random User Agents.
    """
    def __init__(self, clients):
        self.clients = clients
    
    def _get_random_headers(self):
        """Generates headers with randomized device bandwidth/connection type."""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = f'Instagram {random.choice(USER_AGENTS)}'
        headers['X-IG-Connection-Type'] = random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G'])
        headers['X-IG-Bandwidth-Speed-KBPS'] = str(random.randint(1000, 8000))
        headers['X-IG-Bandwidth-TotalBytes-B'] = str(random.randint(500000, 5000000))
        headers['X-IG-Bandwidth-TotalTime-MS'] = str(random.randint(50, 500))
        return headers

    async def check_username_availability(self, username):
        """
        Checks availability of a username using a random proxy client.
        """
        # Pick a random client from the pool
        client = random.choice(self.clients)

        # Generate Fresh Device IDs for total anonymity
        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": f"android-{uuid4()}",
            "guid": str(uuid4()),
        }
        
        try:
            # Short timeout (3s)
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_random_headers(), 
                data=data
            )
            response_text = response.text
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit"
            
            is_available = '"email_is_taken"' in response_text
            return is_available, response_text, None
            
        except (httpx.RequestError, httpx.TimeoutException):
            # Proxy error or timeout is common, treat as not found/skip to keep moving
            return False, "", "connection_error"


class SearchSession:
    """
    Orchestrates a single on-demand search request.
    """
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        
        # Result State
        self.found_username = None
        self.result_reason = "timeout" 
        
        # Concurrency Control
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0

    async def _worker(self, checker):
        """Code running inside each async worker."""
        while not self.should_stop:
            # 1. Check Timeout
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            # 2. Generate
            username = self.generator.generate()
            
            # 3. Check
            is_available, _, error = await checker.check_username_availability(username)
            
            # 4. Handle Result
            if self.should_stop:
                return 

            if error == "rate_limit":
                # With proxies, a single 429 might not mean global stop.
                # We continue with other proxies.
                pass 
            
            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.should_stop = True
                return
            
            # Minimal yield
            await asyncio.sleep(0.01)

    async def run(self):
        """Starts the async task pool."""
        self.start_time = time.time()
        
        # 1. Fetch Dynamic Proxies
        proxies_list = await fetch_proxies()
        
        if not proxies_list:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }

        # 2. Initialize clients for each proxy
        clients = []
        for proxy_url in proxies_list:
            try:
                # httpx.AsyncClient manages the connection pool for this proxy
                client = httpx.AsyncClient(proxy=proxy_url, timeout=3.0)
                clients.append(client)
            except Exception:
                continue
        
        if not clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_reachable",
                "duration": 0
            }

        checker = AutoInstagramChecker(clients)
        
        # Launch workers
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        # Wait for completion or stop
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            
            # Check if all tasks finished (e.g. if we had limited attempts, but here we loop forever)
            # Actually, we should check if we found something
            if self.found_username:
                break
                
            await asyncio.sleep(0.1)

        # Ensure all tasks stop
        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cleanup clients
        for c in clients:
            await c.aclose()
            
        return {
            "status": "success" if self.found_username else "failed",
            "username": self.found_username,
            "reason": self.result_reason if not self.found_username else None,
            "duration": round(time.time() - self.start_time, 2)
        }


# ==========================================
#              API ROUTES
# ==========================================

@app.route('/')
def home():
    """Root endpoint for health checks."""
    return jsonify({
        "status": "online",
        "message": "Instagram Checker API is running with Proxy Rotation.",
        "usage": "Send GET request to /search to find a user."
    })

@app.route('/search')
async def search():
    """
    Triggers a search session.
    """
    session = SearchSession()
    result = await session.run()
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)