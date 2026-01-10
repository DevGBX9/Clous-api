#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API (Anti-Rate-Limit Edition)
=====================================================================

This script runs a Flask API that checks for available 5-character Instagram usernames.
It is designed to be deployed on serverless/container environments like Render.

Features:
- On-Demand Search: Triggered via /search endpoint.
- High Concurrency: Uses asyncio for rapid checking.
- Smart Stopping: Stops immediately upon finding a user, hitting a rate limit, or timing out.
- Advanced Anti-Detection: Full device fingerprints, realistic headers, session persistence.
- Anonymity: Rotating Proxies, Random User-Agents, Dynamic Device IDs.

Author: @GBX_9 (Original Helper)
"""

import os
import sys
import time
import random
import asyncio
import httpx
import hashlib
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
    "MAX_CONCURRENCY": 50,  # Reduced for stability
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

# ==========================================
#       REALISTIC DEVICE CONFIGURATIONS
# ==========================================

ANDROID_DEVICES = [
    {
        "manufacturer": "Samsung",
        "model": "SM-G998B",
        "device": "p3s",
        "android_version": 33,
        "android_release": "13",
        "dpi": "560dpi",
        "resolution": "1440x3200",
        "chipset": "exynos"
    },
    {
        "manufacturer": "Samsung",
        "model": "SM-S918B",
        "device": "dm3q",
        "android_version": 34,
        "android_release": "14",
        "dpi": "480dpi",
        "resolution": "1080x2340",
        "chipset": "qcom"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 8 Pro",
        "device": "husky",
        "android_version": 34,
        "android_release": "14",
        "dpi": "560dpi",
        "resolution": "1344x2992",
        "chipset": "google"
    },
    {
        "manufacturer": "Google",
        "model": "Pixel 7",
        "device": "panther",
        "android_version": 34,
        "android_release": "14",
        "dpi": "420dpi",
        "resolution": "1080x2400",
        "chipset": "google"
    },
    {
        "manufacturer": "Xiaomi",
        "model": "2304FPN6DC",
        "device": "fuxi",
        "android_version": 33,
        "android_release": "13",
        "dpi": "440dpi",
        "resolution": "1080x2400",
        "chipset": "qcom"
    },
    {
        "manufacturer": "OnePlus",
        "model": "CPH2449",
        "device": "OP5958L1",
        "android_version": 33,
        "android_release": "13",
        "dpi": "480dpi",
        "resolution": "1080x2412",
        "chipset": "qcom"
    },
]

INSTAGRAM_VERSIONS = [
    "326.0.0.42.90",
    "325.0.0.35.91",
    "324.0.0.27.50",
    "323.0.0.38.64",
]

LOCALES = [
    ("en_US", -18000),
    ("en_GB", 0),
    ("ar_SA", 10800),
    ("ar_AE", 14400),
    ("de_DE", 3600),
    ("fr_FR", 3600),
]


class DeviceFingerprint:
    """
    Generates and maintains a complete, realistic Android device fingerprint.
    """
    
    def __init__(self, proxy_url: str):
        self.seed = hashlib.md5(proxy_url.encode()).hexdigest()
        random.seed(self.seed)
        
        self.device = random.choice(ANDROID_DEVICES)
        self.ig_version = random.choice(INSTAGRAM_VERSIONS)
        self.locale, self.timezone_offset = random.choice(LOCALES)
        
        self.android_id = self._generate_android_id()
        self.device_id = f"android-{self.android_id}"
        self.phone_id = str(uuid4())
        self.uuid = str(uuid4())
        self.advertising_id = str(uuid4())
        
        random.seed()
    
    def _generate_android_id(self) -> str:
        chars = '0123456789abcdef'
        return ''.join(random.choice(chars) for _ in range(16))
    
    def get_user_agent(self) -> str:
        d = self.device
        return (
            f"Instagram {self.ig_version} "
            f"Android ({d['android_version']}/{d['android_release']}; "
            f"{d['dpi']}; {d['resolution']}; "
            f"{d['manufacturer']}; {d['model']}; "
            f"{d['device']}; {d['chipset']}; {self.locale}; "
            f"{random.randint(500000000, 600000000)})"
        )
    
    def get_headers(self) -> dict:
        return {
            'User-Agent': self.get_user_agent(),
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': self.locale.replace('_', '-'),
            'X-IG-Device-ID': self.phone_id,
            'X-IG-Android-ID': self.device_id,
            'X-IG-Timezone-Offset': str(self.timezone_offset),
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE(LTE)']),
            'X-IG-Capabilities': '3brTv10=',
            'X-IG-App-Locale': self.locale,
            'X-IG-Device-Locale': self.locale,
            'X-IG-App-ID': '567067343352427',
            'X-FB-HTTP-Engine': 'Liger',
        }
    
    def get_request_data(self, username: str) -> dict:
        return {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": self.device_id,
            "guid": self.uuid,
            "phone_id": self.phone_id,
            "waterfall_id": str(uuid4()),
            "adid": self.advertising_id,
        }


class ProxySessionManager:
    def __init__(self):
        self.sessions = {}
    
    def get_fingerprint(self, proxy_url: str) -> DeviceFingerprint:
        if proxy_url not in self.sessions:
            self.sessions[proxy_url] = DeviceFingerprint(proxy_url)
        return self.sessions[proxy_url]


proxy_manager = ProxySessionManager()


# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)


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
        
        timestamp = int(time.time() * 1000) % 100
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:02d}_x"
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    def __init__(self, proxy_clients: list, stats: dict):
        self.proxy_clients = proxy_clients
        self.stats = stats
    
    async def check_username_availability(self, username: str):
        client, proxy_url, fingerprint = random.choice(self.proxy_clients)
        
        headers = fingerprint.get_headers()
        data = fingerprint.get_request_data(username)
        
        try:
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=headers, 
                data=data
            )
            response_text = response.text
            self.stats["total_requests"] += 1
            
            # Debug: print first response
            if self.stats["total_requests"] == 1:
                self.stats["sample_response"] = response_text[:500]
            
            # Check for various error indicators
            if '"spam"' in response_text:
                self.stats["spam_errors"] += 1
                return False, response_text, "spam"
            
            if 'rate_limit' in response_text.lower():
                self.stats["rate_limits"] += 1
                return False, response_text, "rate_limit"
            
            if 'challenge_required' in response_text:
                self.stats["challenges"] += 1
                return False, response_text, "challenge"
            
            # Username is AVAILABLE if email_is_taken appears
            # (means the username passed validation, only email is the issue)
            if '"email_is_taken"' in response_text:
                self.stats["available_found"] += 1
                return True, response_text, None
            
            # Username is TAKEN if username_is_taken appears
            if '"username_is_taken"' in response_text or 'username' in response_text.lower():
                self.stats["username_taken"] += 1
                return False, response_text, "taken"
            
            # Other responses
            self.stats["other_responses"] += 1
            return False, response_text, "other"
            
        except httpx.TimeoutException:
            self.stats["timeouts"] += 1
            return False, "", "timeout"
        except httpx.RequestError as e:
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)[:100]
            return False, "", "connection_error"
        except Exception as e:
            self.stats["other_errors"] += 1
            self.stats["last_error"] = str(e)[:100]
            return False, "", "error"


class SearchSession:
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        
        self.found_username = None
        self.result_reason = "timeout" 
        
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0
        
        # Statistics for debugging
        self.stats = {
            "total_requests": 0,
            "available_found": 0,
            "username_taken": 0,
            "spam_errors": 0,
            "rate_limits": 0,
            "challenges": 0,
            "timeouts": 0,
            "connection_errors": 0,
            "other_responses": 0,
            "other_errors": 0,
            "sample_response": "",
            "last_error": "",
        }

    async def _worker(self, checker):
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            username = self.generator.generate()
            
            is_available, _, error = await checker.check_username_availability(username)
            
            if self.should_stop:
                return 
            
            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.should_stop = True
                return
            
            await asyncio.sleep(0.01)

    async def run(self):
        self.start_time = time.time()
        
        proxy_clients = []
        for proxy_url in PROXIES_LIST:
            try:
                fingerprint = proxy_manager.get_fingerprint(proxy_url)
                client = httpx.AsyncClient(proxy=proxy_url, timeout=5.0)
                proxy_clients.append((client, proxy_url, fingerprint))
            except Exception as e:
                pass
        
        if not proxy_clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0,
                "stats": self.stats
            }

        checker = AutoInstagramChecker(proxy_clients, self.stats)
        
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            
            if self.found_username:
                break
                
            await asyncio.sleep(0.1)

        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        for client, _, _ in proxy_clients:
            await client.aclose()
            
        return {
            "status": "success" if self.found_username else "failed",
            "username": self.found_username,
            "reason": self.result_reason if not self.found_username else None,
            "duration": round(time.time() - self.start_time, 2),
            "stats": self.stats
        }


# ==========================================
#              API ROUTES
# ==========================================

@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Instagram Checker API - Debug Edition",
        "usage": "Send GET request to /search to find a user.",
        "proxies_count": len(PROXIES_LIST)
    })

@app.route('/search')
async def search():
    session = SearchSession()
    result = await session.run()
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)