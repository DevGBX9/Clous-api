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
- Semi-Quad Only: Generates usernames with at least one underscore or dot.

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
    "MAX_CONCURRENCY": 50,  # Increased for async
}

# Values for username generation
CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

# Rotating Proxies (Format: http://user:pass@ip:port)
PROXIES_LIST = [
    "http://mpdmbsys:r36zb0uyv1ls@142.111.48.253:7030",
    "http://mpdmbsys:r36zb0uyv1ls@23.95.150.145:6114",
    "http://mpdmbsys:r36zb0uyv1ls@198.23.239.134:6540",
    "http://mpdmbsys:r36zb0uyv1ls@107.172.163.27:6543",
    "http://mpdmbsys:r36zb0uyv1ls@198.105.121.200:6462",
    "http://mpdmbsys:r36zb0uyv1ls@64.137.96.74:6641",
    "http://mpdmbsys:r36zb0uyv1ls@84.247.60.125:6095",
    "http://mpdmbsys:r36zb0uyv1ls@216.10.27.159:6837",
    "http://mpdmbsys:r36zb0uyv1ls@23.26.71.145:5628",
    "http://mpdmbsys:r36zb0uyv1ls@23.27.208.120:5830",
    "http://wjeirsdr:jw66naw4tr9i@142.111.48.253:7030",
    "http://wjeirsdr:jw66naw4tr9i@23.95.150.145:6114",
    "http://wjeirsdr:jw66naw4tr9i@198.23.239.134:6540",
    "http://wjeirsdr:jw66naw4tr9i@107.172.163.27:6543",
    "http://wjeirsdr:jw66naw4tr9i@198.105.121.200:6462",
    "http://wjeirsdr:jw66naw4tr9i@64.137.96.74:6641",
    "http://wjeirsdr:jw66naw4tr9i@84.247.60.125:6095",
    "http://wjeirsdr:jw66naw4tr9i@216.10.27.159:6837",
    "http://wjeirsdr:jw66naw4tr9i@23.26.71.145:5628",
    "http://wjeirsdr:jw66naw4tr9i@23.27.208.120:5830",
    "http://yfryygud:8o2xjhpyq9xj@142.111.48.253:7030",
    "http://yfryygud:8o2xjhpyq9xj@23.95.150.145:6114",
    "http://yfryygud:8o2xjhpyq9xj@198.23.239.134:6540",
    "http://yfryygud:8o2xjhpyq9xj@107.172.163.27:6543",
    "http://yfryygud:8o2xjhpyq9xj@198.105.121.200:6462",
    "http://yfryygud:8o2xjhpyq9xj@64.137.96.74:6641",
    "http://yfryygud:8o2xjhpyq9xj@84.247.60.125:6095",
    "http://yfryygud:8o2xjhpyq9xj@216.10.27.159:6837",
    "http://yfryygud:8o2xjhpyq9xj@23.26.71.145:5628",
    "http://yfryygud:8o2xjhpyq9xj@23.27.208.120:5830",
    "http://axjoyxsu:nkeue7p68pag@142.111.48.253:7030",
    "http://axjoyxsu:nkeue7p68pag@23.95.150.145:6114",
    "http://axjoyxsu:nkeue7p68pag@198.23.239.134:6540",
    "http://axjoyxsu:nkeue7p68pag@107.172.163.27:6543",
    "http://axjoyxsu:nkeue7p68pag@198.105.121.200:6462",
    "http://axjoyxsu:nkeue7p68pag@64.137.96.74:6641",
    "http://axjoyxsu:nkeue7p68pag@84.247.60.125:6095",
    "http://axjoyxsu:nkeue7p68pag@216.10.27.159:6837",
    "http://axjoyxsu:nkeue7p68pag@23.26.71.145:5628",
    "http://axjoyxsu:nkeue7p68pag@23.27.208.120:5830",
    "http://rxfjeodt:tjf4ikwjokhr@142.111.48.253:7030",
    "http://rxfjeodt:tjf4ikwjokhr@23.95.150.145:6114",
    "http://rxfjeodt:tjf4ikwjokhr@198.23.239.134:6540",
    "http://rxfjeodt:tjf4ikwjokhr@107.172.163.27:6543",
    "http://rxfjeodt:tjf4ikwjokhr@198.105.121.200:6462",
    "http://rxfjeodt:tjf4ikwjokhr@64.137.96.74:6641",
    "http://rxfjeodt:tjf4ikwjokhr@84.247.60.125:6095",
    "http://rxfjeodt:tjf4ikwjokhr@216.10.27.159:6837",
    "http://rxfjeodt:tjf4ikwjokhr@23.26.71.145:5628",
    "http://rxfjeodt:tjf4ikwjokhr@23.27.208.120:5830",
    "http://egfosers:kf2wh571ar1z@142.111.48.253:7030",
    "http://egfosers:kf2wh571ar1z@23.95.150.145:6114",
    "http://egfosers:kf2wh571ar1z@198.23.239.134:6540",
    "http://egfosers:kf2wh571ar1z@107.172.163.27:6543",
    "http://egfosers:kf2wh571ar1z@198.105.121.200:6462",
    "http://egfosers:kf2wh571ar1z@64.137.96.74:6641",
    "http://egfosers:kf2wh571ar1z@84.247.60.125:6095",
    "http://egfosers:kf2wh571ar1z@216.10.27.159:6837",
    "http://egfosers:kf2wh571ar1z@23.26.71.145:5628",
    "http://egfosers:kf2wh571ar1z@23.27.208.120:5830",
    "http://kgghxbly:csswtnznqrey@142.111.48.253:7030",
    "http://kgghxbly:csswtnznqrey@23.95.150.145:6114",
    "http://kgghxbly:csswtnznqrey@198.23.239.134:6540",
    "http://kgghxbly:csswtnznqrey@107.172.163.27:6543",
    "http://kgghxbly:csswtnznqrey@198.105.121.200:6462",
    "http://kgghxbly:csswtnznqrey@64.137.96.74:6641",
    "http://kgghxbly:csswtnznqrey@84.247.60.125:6095",
    "http://kgghxbly:csswtnznqrey@216.10.27.159:6837",
    "http://kgghxbly:csswtnznqrey@23.26.71.145:5628",
    "http://kgghxbly:csswtnznqrey@23.27.208.120:5830",
    "http://lnydwdms:n7c0x0qtyrvp@142.111.48.253:7030",
    "http://lnydwdms:n7c0x0qtyrvp@23.95.150.145:6114",
    "http://lnydwdms:n7c0x0qtyrvp@198.23.239.134:6540",
    "http://lnydwdms:n7c0x0qtyrvp@107.172.163.27:6543",
    "http://lnydwdms:n7c0x0qtyrvp@198.105.121.200:6462",
    "http://lnydwdms:n7c0x0qtyrvp@64.137.96.74:6641",
    "http://lnydwdms:n7c0x0qtyrvp@84.247.60.125:6095",
    "http://lnydwdms:n7c0x0qtyrvp@216.10.27.159:6837",
    "http://lnydwdms:n7c0x0qtyrvp@23.26.71.145:5628",
    "http://lnydwdms:n7c0x0qtyrvp@23.27.208.120:5830",
    "http://idzfeaih:tg11yrege1lz@142.111.48.253:7030",
    "http://idzfeaih:tg11yrege1lz@23.95.150.145:6114",
    "http://idzfeaih:tg11yrege1lz@198.23.239.134:6540",
    "http://idzfeaih:tg11yrege1lz@107.172.163.27:6543",
    "http://idzfeaih:tg11yrege1lz@198.105.121.200:6462",
    "http://idzfeaih:tg11yrege1lz@64.137.96.74:6641",
    "http://idzfeaih:tg11yrege1lz@84.247.60.125:6095",
    "http://idzfeaih:tg11yrege1lz@216.10.27.159:6837",
    "http://idzfeaih:tg11yrege1lz@23.26.71.145:5628",
    "http://idzfeaih:tg11yrege1lz@23.27.208.120:5830",
]

# Random iterator to pick proxies efficiently
# We use random.choice mostly, but cycle can be used for round-robin
proxy_pool = itertools.cycle(PROXIES_LIST)

# Expanded User Agents
# Expanded User Agents (50+ Real Devices)
USER_AGENTS = [
    # SAMSUNG - S23/S22/S21 Series
    'Instagram 316.0.0.38.109 Android (34/14; 450dpi; 1080x2340; Samsung; SM-S911B; kalama; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 480dpi; 1080x2400; Samsung; SM-A546B; s5e8835; samsung; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 420dpi; 1080x2400; Samsung; SM-A346B; k6895v1_64; mt6877; en_US)',
    'Instagram 313.0.0.28.108 Android (34/14; 560dpi; 1440x3088; Samsung; SM-S908B; b0q; samsung; en_US)',
    'Instagram 312.0.0.26.107 Android (34/14; 440dpi; 1080x2316; Samsung; SM-S901B; r0q; samsung; en_US)',
    'Instagram 311.0.0.32.118 Android (33/13; 450dpi; 1080x2400; Samsung; SM-G991B; o1s; samsung; en_US)',
    'Instagram 310.0.0.28.115 Android (32/12; 420dpi; 1080x2400; Samsung; SM-G780G; r8q; samsung; en_US)',
    
    # GOOGLE PIXEL - 8/7/6 Series
    'Instagram 316.0.0.38.109 Android (34/14; 560dpi; 1344x2992; Google; Pixel 8 Pro; husky; google; en_US)',
    'Instagram 315.0.0.34.111 Android (34/14; 420dpi; 1080x2400; Google; Pixel 8; shiba; google; en_US)',
    'Instagram 314.0.0.30.110 Android (34/14; 560dpi; 1440x3120; Google; Pixel 7 Pro; cheetah; google; en_US)',
    'Instagram 313.0.0.28.108 Android (33/13; 411dpi; 1080x2400; Google; Pixel 7; panther; google; en_US)',
    'Instagram 312.0.0.26.107 Android (33/13; 400dpi; 1080x2400; Google; Pixel 6a; bluejay; google; en_US)',
    'Instagram 311.0.0.32.118 Android (33/13; 560dpi; 1440x3120; Google; Pixel 6 Pro; raven; google; en_US)',

    # XIAOMI - 13/12/Redmi Note
    'Instagram 316.0.0.38.109 Android (33/13; 490dpi; 1080x2400; Xiaomi; 2210132G; fuxi; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 440dpi; 1220x2712; Xiaomi; 23049PCD8G; socrates; qcom; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 393dpi; 1080x2400; Xiaomi; M2102J20SG; vayu; qcom; en_US)',
    'Instagram 313.0.0.28.108 Android (32/12; 440dpi; 1080x2400; Xiaomi; M2101K6G; sweet; qcom; en_US)',
    'Instagram 312.0.0.26.107 Android (33/13; 400dpi; 1080x2400; Redmi; 2201117TY; spes; qcom; en_US)',
    'Instagram 318.0.0.22.112 Android (33/13; 395dpi; 1080x2400; POCO; 2201116PG; veux; qcom; en_US)',
    
    # ONEPLUS
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1440x3216; OnePlus; CPH2551; salami; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (34/14; 420dpi; 1080x2412; OnePlus; CPH2447; ovaltine; qcom; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 560dpi; 1440x3216; OnePlus; NE2213; lemonade; qcom; en_US)',
    'Instagram 313.0.0.28.108 Android (33/13; 450dpi; 1080x2400; OnePlus; MT2111; martini; mt6893; en_US)',
    
    # MOTOROLA
    'Instagram 316.0.0.38.109 Android (34/14; 420dpi; 1080x2400; motorola; motorola edge 40; taro; mt6891; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 400dpi; 1080x2400; motorola; moto g(60); hanoip; qcom; en_US)',
    
    # REALME
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1080x2412; realme; RMX3771; RMX3771; mt6877; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 450dpi; 1080x2400; realme; RMX3363; RMX3363; qcom; en_US)',
    
    # OPPO
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1200x2668; OPPO; CPH2437; CPH2437; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 420dpi; 1080x2400; OPPO; CPH2359; CPH2359; qcom; en_US)',
    
    # VIVO
    'Instagram 316.0.0.38.109 Android (34/14; 440dpi; 1200x2800; vivo; V2219; V2219; mt6893; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 400dpi; 1080x2400; vivo; V2025; V2025; qcom; en_US)',
    
    # SONY
    'Instagram 316.0.0.38.109 Android (34/14; 640dpi; 1644x3840; Sony; XQ-DQ72; PDX-234; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 420dpi; 1080x2520; Sony; XQ-DC72; PDX-233; qcom; en_US)',
    
    # OLDER BUT RELIABLE (Android 11/12)
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
    Now generates ONLY semi-quad usernames (with at least one underscore or dot).
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
    
    def is_semi_quad(self, username):
        """
        Checks if the username is a 'semi-quad' (contains at least one underscore or dot).
        """
        return '_' in username or '.' in username
    
    def generate(self):
        """
        Generates a unique, compliant 5-char semi-quad username.
        Semi-quad means it must contain at least one underscore or dot.
        """
        max_attempts = 100
        
        for _ in range(max_attempts):
            # Start with a letter (Instagram requirement)
            first_char = random.choice(CHARS["LETTERS"])
            
            # Choose a random position (1-3) to insert a symbol (. or _)
            symbol_positions = [1, 2, 3]
            symbol_pos = random.choice(symbol_positions)
            
            # Choose symbol - dot or underscore
            symbol = random.choice(CHARS["SYMBOLS"])
            
            # Build the username
            username_chars = [first_char]
            
            for pos in range(1, 5):
                if pos == symbol_pos:
                    username_chars.append(symbol)
                else:
                    username_chars.append(random.choice(CHARS["ALL_VALID"]))
            
            username = ''.join(username_chars)
            
            # Validate and ensure it's a semi-quad
            if (username not in self.generated_usernames and 
                self.is_valid_instagram_username(username) and
                self.is_semi_quad(username)):
                self.generated_usernames.add(username)
                return username
        
        # Fallback: Generate a guaranteed semi-quad username
        for _ in range(50):
            username = (
                random.choice(CHARS["LETTERS"]) +
                random.choice(CHARS["ALL_VALID"]) +
                random.choice(CHARS["SYMBOLS"]) +
                random.choice(CHARS["ALL_VALID"]) +
                random.choice(CHARS["ALL_VALID"])
            )
            if (username not in self.generated_usernames and 
                self.is_valid_instagram_username(username)):
                self.generated_usernames.add(username)
                return username
        
        # Ultimate fallback with timestamp
        timestamp = int(time.time() * 1000) % 100
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:02d}_x"
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
        # The new USER_AGENTS list already contains the full string "Instagram ... "
        # so we don't need to prepend 'Instagram ' anymore if the list has it.
        # However, checking the list above, they start with 'Instagram'.
        headers['User-Agent'] = random.choice(USER_AGENTS)
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
        
        # Initialize clients for each proxy
        # We assume PROXIES_LIST has valid proxy URLs
        clients = []
        for proxy_url in PROXIES_LIST:
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
                "reason": "no_proxies_available",
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