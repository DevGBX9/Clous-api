#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - High-Stealth Mobile API Edition
==========================================================

Features:
- Mobile API (High Speed): matches the behavior of the Instagram Android App.
- High Stealth: Rotates User-Agents, Device IDs, and Fingerprints per request.
- Secure Transport: 100% Proxy usage, No IP Leakage.
- Semi-Quad Generation: Guarantees 5-char usernames with '_' or '.'.

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

sys.dont_write_bytecode = True

# ==========================================
#              CONFIGURATION
# ==========================================
CONFIG = {
    # Original Mobile API - Proven to be fast
    "INSTAGRAM_API_URL": 'https://i.instagram.com/api/v1/accounts/create/',
    "TIMEOUT_SECONDS": 30,
    "FIXED_EMAIL": "abdo1@gmail.com",
    "MAX_CONCURRENCY": 30, # slightly reduced for better stealth stability
}

CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

# Rotating Proxies
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

# 50+ Modern User-Agents (Realistic Diversity)
REAL_USER_AGENTS = [
    # SAMSUNG
    'Instagram 316.0.0.38.109 Android (34/14; 450dpi; 1080x2340; Samsung; SM-S911B; kalama; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 480dpi; 1080x2400; Samsung; SM-A546B; s5e8835; samsung; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 420dpi; 1080x2400; Samsung; SM-A346B; k6895v1_64; mt6877; en_US)',
    'Instagram 313.0.0.28.108 Android (34/14; 560dpi; 1440x3088; Samsung; SM-S908B; b0q; samsung; en_US)',
    'Instagram 312.0.0.26.107 Android (34/14; 440dpi; 1080x2316; Samsung; SM-S901B; r0q; samsung; en_US)',
    
    # GOOGLE PIXEL
    'Instagram 316.0.0.38.109 Android (34/14; 560dpi; 1344x2992; Google; Pixel 8 Pro; husky; google; en_US)',
    'Instagram 315.0.0.34.111 Android (34/14; 420dpi; 1080x2400; Google; Pixel 8; shiba; google; en_US)',
    'Instagram 314.0.0.30.110 Android (34/14; 560dpi; 1440x3120; Google; Pixel 7 Pro; cheetah; google; en_US)',
    'Instagram 313.0.0.28.108 Android (33/13; 411dpi; 1080x2400; Google; Pixel 7; panther; google; en_US)',
    'Instagram 312.0.0.26.107 Android (33/13; 400dpi; 1080x2400; Google; Pixel 6a; bluejay; google; en_US)',

    # XIAOMI
    'Instagram 316.0.0.38.109 Android (33/13; 490dpi; 1080x2400; Xiaomi; 2210132G; fuxi; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 440dpi; 1220x2712; Xiaomi; 23049PCD8G; socrates; qcom; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 393dpi; 1080x2400; Xiaomi; M2102J20SG; vayu; qcom; en_US)',
    'Instagram 313.0.0.28.108 Android (32/12; 440dpi; 1080x2400; Xiaomi; M2101K6G; sweet; qcom; en_US)',
    'Instagram 312.0.0.26.107 Android (33/13; 400dpi; 1080x2400; Redmi; 2201117TY; spes; qcom; en_US)',

    # ONEPLUS
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1440x3216; OnePlus; CPH2551; salami; qcom; en_US)',
    'Instagram 315.0.0.34.111 Android (34/14; 420dpi; 1080x2412; OnePlus; CPH2447; ovaltine; qcom; en_US)',
    'Instagram 314.0.0.30.110 Android (33/13; 560dpi; 1440x3216; OnePlus; NE2213; lemonade; qcom; en_US)', # 10 Pro
    'Instagram 313.0.0.28.108 Android (33/13; 450dpi; 1080x2400; OnePlus; MT2111; martini; mt6893; en_US)', # 9RT
    
    # MOTOROLA
    'Instagram 316.0.0.38.109 Android (34/14; 420dpi; 1080x2400; motorola; motorola edge 40; taro; mt6891; en_US)',
    'Instagram 315.0.0.34.111 Android (33/13; 400dpi; 1080x2400; motorola; moto g(60); hanoip; qcom; en_US)',

    # REALME
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1080x2412; realme; RMX3771; RMX3771; mt6877; en_US)', # 11 Pro
    'Instagram 315.0.0.34.111 Android (33/13; 450dpi; 1080x2400; realme; RMX3363; RMX3363; qcom; en_US)', # GT Master
    
    # OPPO
    'Instagram 316.0.0.38.109 Android (34/14; 480dpi; 1200x2668; OPPO; CPH2437; CPH2437; qcom; en_US)', # Find N2 Flip
    'Instagram 315.0.0.34.111 Android (33/13; 420dpi; 1080x2400; OPPO; CPH2359; CPH2359; qcom; en_US)', # Reno 8
    
    # VIVO
    'Instagram 316.0.0.38.109 Android (34/14; 440dpi; 1200x2800; vivo; V2219; V2219; mt6893; en_US)', # V25 Pro
    'Instagram 315.0.0.34.111 Android (33/13; 400dpi; 1080x2400; vivo; V2025; V2025; qcom; en_US)', # V20
    
    # SONY
    'Instagram 316.0.0.38.109 Android (34/14; 640dpi; 1644x3840; Sony; XQ-DQ72; PDX-234; qcom; en_US)', # Xperia 1 V
    'Instagram 315.0.0.34.111 Android (33/13; 420dpi; 1080x2520; Sony; XQ-DC72; PDX-233; qcom; en_US)', # Xperia 10 V
]

# Random iterator to pick proxies efficiently
proxy_pool = itertools.cycle(PROXIES_LIST)

# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)


# ==========================================
#              CORE LOGIC
# ==========================================

def create_secure_client(proxy_url: str) -> httpx.AsyncClient:
    """
    Create a secure HTTP client that routes ALL traffic through proxy.
    NO IP LEAKAGE - DNS resolution also goes through proxy.
    """
    transport = httpx.AsyncHTTPTransport(
        proxy=proxy_url,
        verify=True,
        retries=0, # No fallback to direct connection
    )
    
    client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(10.0, connect=5.0),
        trust_env=False, # Ignore system proxies/env vars
        http2=False, # Better for stealth (looks more like standard App requests)
    )
    
    return client


class AutoUsernameGenerator:
    """
    Generates compliant 5-char semi-quad usernames.
    """
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
        
        # Fallback
        timestamp = int(time.time() * 1000) % 100
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:02d}_x"
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    """
    The High-Stealth Checker.
    Generates unique identity for EVERY request.
    """
    def __init__(self, clients):
        self.clients = clients
    
    def _get_dynamic_headers(self, user_agent):
        """
        Generates highly realistic headers that match valid Android App traffic.
        """
        # Parse connection type to simulate realistic bandwidth
        conn_type = random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G'])
        
        if conn_type == 'WIFI':
            speed_kbps = f"{random.randint(100000, 300000)}"
            bandwidth_bytes = f"{random.randint(2000000, 5000000)}"
        else:
            speed_kbps = f"{random.randint(5000, 50000)}"
            bandwidth_bytes = f"{random.randint(500000, 2000000)}"

        return {
            'User-Agent': user_agent,
            'Accept-Language': 'en-US',
            'X-IG-Capabilities': 'AQ==',
            'Accept-Encoding': 'gzip',
            'X-IG-Connection-Type': conn_type,
            'X-IG-Capabilities': '3brTvw==', # Common capability string for modern args
            'X-IG-Connection-Speed': f'{random.randint(1000, 5000)}kbps',
            'X-IG-Bandwidth-Speed-KBPS': f'{random.randint(1000, 8000)}.000',
            'X-IG-Bandwidth-TotalBytes-B': f'{random.randint(500000, 5000000)}',
            'X-IG-Bandwidth-TotalTime-MS': f'{random.randint(50, 500)}',
            'X-IG-App-Locale': 'en_US',
            'X-IG-Device-Locale': 'en_US', 
            'X-IG-Android-ID': ''.join(random.choices('0123456789abcdef', k=16)),
            'X-IG-Device-ID': f'android-{uuid4()}',
        }

    async def check_username_availability(self, username):
        """
        Checks username availability with a fresh, unique identity.
        """
        # 1. Pick Client (Proxy)
        client = random.choice(self.clients)

        # 2. Generate Fresh Identity
        user_agent = random.choice(REAL_USER_AGENTS)
        device_id = f"android-{uuid4()}" 
        phone_id = str(uuid4())
        adid = str(uuid4()) # Advertising ID
        guid = str(uuid4())
        
        # 3. Construct Payload
        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": device_id,
            "phone_id": phone_id,
            "adid": adid,
            "guid": guid,
            "first_name": username,
            "google_adid": adid,
            "waterfall_id": str(uuid4())
        }
        
        try:
            # 4. Send Request with Dynamic Headers
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_dynamic_headers(user_agent), 
                data=data
            )
            response_text = response.text
            
            # 5. Parse Response
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit"
                
            if 'challenge_required' in response_text:
                 return False, response_text, "challenge"
            
            # If email is taken, it means the username passed the check!
            is_available = '"email_is_taken"' in response_text
            
            # Sometimes it returns account_created: false but with errors about email/password, which means username is OK
            if '"account_created":false' in response_text and '"username":' not in response_text:
                 # Double check if there is an explicit username check error
                if "username_is_taken" not in response_text:
                     return True, response_text, None

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
            
            # Slight delay to allow other tasks to process
            await asyncio.sleep(0.01)

    async def run(self):
        self.start_time = time.time()
        
        # Setup Secure Clients
        clients = []
        for proxy_url in PROXIES_LIST:
            try:
                client = create_secure_client(proxy_url)
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
    return jsonify({
        "status": "online",
        "message": "Instagram Checker API - Verified High-Stealth",
        "usage": "Send GET request to /search"
    })

@app.route('/search')
async def search():
    session = SearchSession()
    result = await session.run()
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)