#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - Dynamic Proxy API ONLY
====================================================

Uses PubProxy API exclusively with maximum speed optimization.

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import httpx
from uuid import uuid4
from flask import Flask, jsonify
from flask_cors import CORS

sys.dont_write_bytecode = True

# ==========================================
#              CONFIGURATION
# ==========================================
CONFIG = {
    "INSTAGRAM_API_URL": 'https://i.instagram.com/api/v1/accounts/create/',
    "TIMEOUT_SECONDS": 30,
    "FIXED_EMAIL": "abdo1@gmail.com",
    "MAX_CONCURRENCY": 100,
    "PROXY_REFRESH_INTERVAL": 15,
    # Multiple proxy APIs for redundancy and more proxies
    "PROXY_APIS": [
        "http://pubproxy.com/api/proxy?limit=20&format=txt&http=true&last_check=5",
        "http://pubproxy.com/api/proxy?limit=20&format=txt&https=true&last_check=5",
    ],
}

CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

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

app = Flask(__name__)
CORS(app)


# ==========================================
#    ULTRA-FAST ASYNC PROXY FETCHER
# ==========================================

async def fetch_proxies_ultra_fast():
    """
    Fetch proxies from multiple APIs concurrently using httpx async.
    Much faster than requests library.
    """
    all_proxies = []
    
    async with httpx.AsyncClient(timeout=3.0) as client:
        # Fetch from all APIs concurrently
        tasks = []
        for api_url in CONFIG["PROXY_APIS"]:
            tasks.append(client.get(api_url))
        
        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for response in responses:
            if isinstance(response, Exception):
                continue
            try:
                if response.status_code == 200:
                    proxy_text = response.text.strip()
                    if proxy_text:
                        for line in proxy_text.split('\n'):
                            line = line.strip()
                            if line and line not in all_proxies:
                                if not line.startswith('http'):
                                    all_proxies.append(f"http://{line}")
                                else:
                                    all_proxies.append(line)
            except Exception:
                continue
    
    print(f"[ProxyFetcher] Got {len(all_proxies)} proxies")
    return all_proxies


async def create_clients_fast(proxy_urls):
    """Create httpx clients for all proxies concurrently."""
    clients = []
    for proxy_url in proxy_urls:
        try:
            client = httpx.AsyncClient(
                proxy=proxy_url, 
                timeout=2.0,  # Short timeout for speed
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            clients.append(client)
        except Exception:
            continue
    return clients


# ==========================================
#              CORE LOGIC
# ==========================================

class AutoUsernameGenerator:
    def __init__(self):
        self.generated_usernames = set()
    
    def is_valid_instagram_username(self, username):
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
    def __init__(self, clients):
        self.clients = clients
        self.idx = 0
    
    def _get_random_headers(self):
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = f'Instagram {random.choice(USER_AGENTS)}'
        headers['X-IG-Connection-Type'] = random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G'])
        headers['X-IG-Bandwidth-Speed-KBPS'] = str(random.randint(1000, 8000))
        headers['X-IG-Bandwidth-TotalBytes-B'] = str(random.randint(500000, 5000000))
        headers['X-IG-Bandwidth-TotalTime-MS'] = str(random.randint(50, 500))
        return headers

    async def check_username_availability(self, username):
        if not self.clients:
            return False, "", "no_client"
        
        # Round-robin for even distribution
        client = self.clients[self.idx % len(self.clients)]
        self.idx += 1

        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": f"android-{uuid4()}",
            "guid": str(uuid4()),
        }
        
        try:
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
            return False, "", "connection_error"


class SearchSession:
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        self.found_username = None
        self.result_reason = "timeout"
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0
        self.last_refresh = 0
        self.clients = []
        self.refresh_lock = asyncio.Lock()

    async def _refresh_proxies(self):
        """Refresh proxies from API."""
        async with self.refresh_lock:
            if time.time() - self.last_refresh < 5:  # Prevent spam
                return
            
            print("[Session] Refreshing proxies...")
            new_proxies = await fetch_proxies_ultra_fast()
            
            if new_proxies:
                # Close old clients
                for c in self.clients:
                    try:
                        await c.aclose()
                    except:
                        pass
                
                # Create new clients
                self.clients = await create_clients_fast(new_proxies)
                self.last_refresh = time.time()
                print(f"[Session] Now using {len(self.clients)} clients")

    async def _worker(self, checker):
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            # Check if refresh needed (15s rule)
            if time.time() - self.last_refresh > CONFIG["PROXY_REFRESH_INTERVAL"]:
                await self._refresh_proxies()

            username = self.generator.generate()
            is_available, _, error = await checker.check_username_availability(username)
            
            if self.should_stop:
                return

            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.should_stop = True
                return
            
            await asyncio.sleep(0)  # Yield without delay

    async def run(self):
        self.start_time = time.time()
        
        # Fetch proxies from API
        print("[Session] Fetching proxies from API...")
        proxy_urls = await fetch_proxies_ultra_fast()
        
        if not proxy_urls:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_from_api",
                "duration": round(time.time() - self.start_time, 2)
            }
        
        self.clients = await create_clients_fast(proxy_urls)
        self.last_refresh = time.time()
        
        if not self.clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "clients_creation_failed",
                "duration": round(time.time() - self.start_time, 2)
            }

        print(f"[Session] Starting with {len(self.clients)} clients")
        checker = AutoInstagramChecker(self.clients)
        
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            if self.found_username:
                break
            await asyncio.sleep(0.05)

        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        for c in self.clients:
            try:
                await c.aclose()
            except:
                pass
            
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
    return jsonify({
        "status": "online",
        "message": "Instagram Checker - Dynamic Proxy API Only",
        "usage": "GET /search"
    })

@app.route('/search')
def search():
    session = SearchSession()
    result = asyncio.run(session.run())
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)