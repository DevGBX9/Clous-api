#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - Ultimate Stealth Edition
===================================================

Features:
- On-Demand Search: Triggered via /search endpoint.
- Self-Contained: Generates 1000 Valid Legacy User-Agents internally.
- Full Device Fingerprint: Generates COMPLETE Android Identity (IDs, ADIDs, GUIDs) per request.
- Security: Rotates Identity + Proxy + User-Agent for every single check.
- Stats: Detailed reporting of used agents.

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import httpx
import itertools
import json
import threading
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
    "MAX_CONCURRENCY": 50,
}

CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

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

# Random iterator
proxy_pool = itertools.cycle(PROXIES_LIST)

# ==========================================
#      LEGACY UA GENERATOR (INTERNAL)
# ==========================================
UA_INSTAGRAM_VERSIONS = [
    f"{major}.{minor}.{patch}" 
    for major in range(10, 120, 2)
    for minor in range(0, 5) 
    for patch in range(0, 5)
]

UA_ANDROID_VERSIONS = [
    ("19", "4.4.2"), ("21", "5.0"), ("22", "5.1"), ("23", "6.0"), 
    ("24", "7.0"), ("25", "7.1.1"), ("26", "8.0.0"), ("27", "8.1.0"), 
    ("28", "9"), ("29", "10")
]

UA_DEVICES = [
    {"brand": "Samsung", "model": "SM-G930F", "device": "herolte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-G950F", "device": "dreamlte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-G960F", "device": "starlte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-J530F", "device": "j5y17lte", "cpu": "exynos7870"},
    {"brand": "Samsung", "model": "SM-A520F", "device": "a5y17lte", "cpu": "samsung"},
    {"brand": "Xiaomi", "model": "Redmi Note 7", "device": "lavender", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "Redmi Note 5", "device": "whyred", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "MI 8", "device": "dipper", "cpu": "qcom"},
    {"brand": "Huawei", "model": "ANE-LX1", "device": "HWANE", "cpu": "hisilicon"},
]

UA_RESOLUTIONS = ["1080x1920", "1080x2240", "1080x2340", "720x1280", "1440x2560"]
UA_DPIS = ["320", "420", "440", "480", "560", "640"]
UA_LOCALES = ["en_US", "en_GB", "es_ES", "fr_FR", "de_DE", "it_IT"]

def generate_legacy_agents(count=1000):
    """Generates a list of valid legacy User-Agents on the fly."""
    agents = []
    seen = set()
    attempts = 0
    while len(agents) < count and attempts < count * 5:
        attempts += 1
        app_ver = random.choice(UA_INSTAGRAM_VERSIONS)
        sdk, android_ver = random.choice(UA_ANDROID_VERSIONS)
        device = random.choice(UA_DEVICES)
        res = random.choice(UA_RESOLUTIONS)
        dpi = random.choice(UA_DPIS)
        locale = random.choice(UA_LOCALES) if random.random() < 0.2 else "en_US"
        
        ua_string = (
            f"Instagram {app_ver} Android "
            f"({sdk}/{android_ver}; {dpi}dpi; {res}; {device['brand']}; "
            f"{device['model']}; {device['device']}; {device['cpu']}; {locale})"
        )
        
        if ua_string not in seen:
            seen.add(ua_string)
            agents.append(ua_string)
            
    return agents

# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)


# ==========================================
#              CORE LOGIC
# ==========================================

class AutoUsernameGenerator:
    """Generates valid 5-character semi-quad usernames."""
    def __init__(self):
        self.generated_usernames = set()
    
    def is_valid_instagram_username(self, username):
        if len(username) != 5: return False
        allowed_chars = set(CHARS["ALL_VALID"] + CHARS["SYMBOLS"])
        if not all(char in allowed_chars for char in username): return False
        if username.startswith('.') or username.endswith('.'): return False
        if '..' in username or '._' in username or '_.' in username: return False
        if username[0] in CHARS["DIGITS"]: return False
        return True
    
    def is_semi_quad(self, username):
        return '_' in username or '.' in username
    
    def generate(self):
        max_attempts = 100
        for _ in range(max_attempts):
            first_char = random.choice(CHARS["LETTERS"])
            symbol_positions = [1, 2, 3]
            symbol_pos = random.choice(symbol_positions)
            symbol = random.choice(CHARS["SYMBOLS"])
            
            username_chars = [first_char]
            for pos in range(1, 5):
                if pos == symbol_pos:
                    username_chars.append(symbol)
                else:
                    username_chars.append(random.choice(CHARS["ALL_VALID"]))
            
            username = ''.join(username_chars)
            
            if (username not in self.generated_usernames and 
                self.is_valid_instagram_username(username) and
                self.is_semi_quad(username)):
                self.generated_usernames.add(username)
                return username
        
        timestamp = int(time.time() * 1000) % 100
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:02d}_x"
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    """
    HTTP Checker that uses a provided list of User-Agents rotationally.
    NOW ENHANCED: Simulates FULL Device Fingerprint per request.
    """
    def __init__(self, clients, user_agents_pool):
        self.clients = clients
        self.user_agents_pool = user_agents_pool
        self.ua_cycle = itertools.cycle(user_agents_pool)
        self.used_agents = set()
    
    def _generate_device_payload(self, username, device_id):
        """
        Generates a COMPREHENSIVE Android Device Identity.
        This simulates what the App actually sends.
        """
        # Generate consistent IDs for this "Session"
        phone_id = str(uuid4())
        adid = str(uuid4()) # Advertising ID
        guid = str(uuid4())
        
        return {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": device_id,  # Main Android Device ID
            "phone_id": phone_id,    # Instance ID
            "adid": adid,            # Advertising ID (Critical for validation)
            "guid": guid,            # Generic UUID
            "google_adid": adid,     # Often mirrors 'adid'
            "first_name": username,  # Metadata mostly ignored but good for realism
            "waterfall_id": str(uuid4()) # Traceability ID often used by IG
        }

    def _get_headers(self, user_agent):
        """Constructs headers with a SPECIFIC user agent."""
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': 'en-US',
            'X-IG-Capabilities': 'AQ==',
            'Accept-Encoding': 'gzip',
            'User-Agent': user_agent,
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G']),
            'X-IG-Bandwidth-Speed-KBPS': str(random.randint(1000, 8000)),
            'X-IG-Bandwidth-TotalBytes-B': str(random.randint(500000, 5000000)),
            'X-IG-Bandwidth-TotalTime-MS': str(random.randint(50, 500))
        }
        return headers

    async def check_username_availability(self, username):
        # Pick User-Agent from our per-session pool
        current_ua = next(self.ua_cycle)
        self.used_agents.add(current_ua)
        
        client = random.choice(self.clients)
        
        # Generate unique Android Device ID
        # Format can be 'android-'+16hex OR a UUID, old versions accept both.
        # We stick to uuid as it's cleaner.
        device_id = f"android-{uuid4()}"

        # Generate FULL Payload
        data = self._generate_device_payload(username, device_id)
        
        try:
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_headers(current_ua), 
                data=data
            )
            response_text = response.text
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit", current_ua
            
            is_available = '"email_is_taken"' in response_text
            return is_available, response_text, None, current_ua
            
        except (httpx.RequestError, httpx.TimeoutException):
            return False, "", "connection_error", current_ua


class SearchSession:
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        self.found_username = None
        self.result_reason = "timeout" 
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0
        self.successful_ua = None
        self.checker = None

    async def _worker(self):
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            username = self.generator.generate()
            
            is_available, _, error, used_ua = await self.checker.check_username_availability(username)
            
            if self.should_stop:
                return 

            if is_available:
                self.found_username = username
                self.successful_ua = used_ua
                self.result_reason = "success"
                self.should_stop = True
                return
            
            await asyncio.sleep(0.01)

    async def run(self):
        self.start_time = time.time()
        
        # 1. Generate 1000 Unique Legacy User-Agents for THIS session
        session_agents = generate_legacy_agents(1000)
        
        # 2. Setup Clients
        clients = []
        for proxy_url in PROXIES_LIST:
            try:
                client = httpx.AsyncClient(proxy=proxy_url, timeout=3.0)
                clients.append(client)
            except Exception:
                continue
        
        if not clients:
            return {
                "status": "failed",
                "reason": "no_proxies_available"
            }

        self.checker = AutoInstagramChecker(clients, session_agents)
        tasks = [asyncio.create_task(self._worker()) for _ in range(self.max_concurrency)]
        
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            if self.found_username:
                break
            await asyncio.sleep(0.1)

        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        for c in clients:
            await c.aclose()
            
        return {
            "status": "success" if self.found_username else "failed",
            "username": self.found_username,
            "reason": self.result_reason if not self.found_username else None,
            "duration": round(time.time() - self.start_time, 2),
            "stats": {
                "generated_agents": len(session_agents),
                "agents_used_count": len(self.checker.used_agents),
                "successful_agent": self.successful_ua
            }
        }


# ==========================================
#              API ROUTES
# ==========================================

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Instagram Checker: Ultimate Stealth (Full Device Simulation)",
        "usage": "Send GET request to /search"
    })

@app.route('/search')
async def search():
    """Triggers a search session with fresh Device Identities."""
    session = SearchSession()
    result = await session.run()
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)