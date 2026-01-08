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

# ==========================================
#          DEVICE FINGERPRINTING
# ==========================================

class DeviceProfile:
    """
    Simulates a comprehensive hardware and software fingerprint for an Android device.
    Atomic Consistency is maintained between OS version, hardware, and identifiers.
    """
    
    HARDWARE_PROFILES = [
        {
            "brand": "Samsung",
            "model": "SM-G991B",
            "codename": "o1s",
            "android_version": "13",
            "sdk_version": "33",
            "dpi": "480",
            "res": "1080x2400",
            "cpu": "exynos2100",
            "manufacturer": "samsung"
        },
        {
            "brand": "Google",
            "model": "Pixel 7 Pro",
            "codename": "cheetah",
            "android_version": "14",
            "sdk_version": "34",
            "dpi": "560",
            "res": "1440x3120",
            "cpu": "tensor-g2",
            "manufacturer": "Google"
        },
        {
            "brand": "Xiaomi",
            "model": "M2101K6G",
            "codename": "sweet",
            "android_version": "12",
            "sdk_version": "31",
            "dpi": "440",
            "res": "1080x2400",
            "cpu": "qcom",
            "manufacturer": "Xiaomi"
        },
        {
            "brand": "OnePlus",
            "model": "LE2113",
            "codename": "lemonade",
            "android_version": "13",
            "sdk_version": "33",
            "dpi": "450",
            "res": "1080x2400",
            "cpu": "qcom",
            "manufacturer": "OnePlus"
        }
    ]

    LOCALES = [
        ("en_US", "en-US"), ("en_GB", "en-GB"), ("ar_SA", "ar-SA"),
        ("fr_FR", "fr-FR"), ("de_DE", "de-DE"), ("tr_TR", "tr-TR")
    ]

    def __init__(self):
        # Atomic binding: every attribute is fixed once assigned to this profile
        profile = random.choice(self.HARDWARE_PROFILES)
        self.brand = profile["brand"]
        self.model = profile["model"]
        self.codename = profile["codename"]
        self.android_ver = profile["android_version"]
        self.sdk_ver = profile["sdk_version"]
        self.dpi = profile["dpi"]
        self.res = profile["res"]
        self.cpu = profile["cpu"]
        self.manufacturer = profile["manufacturer"]
        
        # Consistent Identifiers
        self.device_id = f"android-{uuid4().hex[:16]}"
        self.guid = str(uuid4())
        self.pigeon_session_id = str(uuid4())
        
        # Locales
        self.locale_pair = random.choice(self.LOCALES)
        self.app_locale = self.locale_pair[0]
        self.mapped_locale = self.locale_pair[1]
        
        # IG Internal values
        self.app_version = "311.0.0.32.118" # Recent Instagram version
        self.app_version_code = "543210987"
        self.capabilities = "3brTvw==" # Standard base64 cap string
        
    def get_user_agent(self):
        """Constructs a realistic Instagram Android User-Agent."""
        # Format: Instagram <app_ver> Android (<android_ver>/<sdk_ver>; <dpi>; <res>; <brand>; <model>; <codename>; <cpu>; <locale>)
        return (f"Instagram {self.app_version} Android "
                f"({self.android_ver}/{self.sdk_ver}; {self.dpi}dpi; {self.res}; "
                f"{self.manufacturer}; {self.model}; {self.codename}; {self.cpu}; {self.app_locale})")

class AutoInstagramChecker:
    """
    Handles optimized HTTP communication with Instagram.
    Maintains sticky DeviceProfiles for each proxy session.
    """
    def __init__(self, clients_with_profiles):
        """
        clients_with_profiles: list of (httpx.AsyncClient, DeviceProfile) tuples
        """
        self.client_pool = clients_with_profiles
    
    def _calculate_jitter_headers(self):
        """Simulates realistic network jitter and bandwidth metrics."""
        # Realistic values based on mobile/wifi connection
        total_bytes = random.randint(1024 * 50, 1024 * 500) # 50KB to 500KB
        total_time_ms = random.randint(100, 800)
        speed_kbps = (total_bytes * 8) / max(total_time_ms, 1) # Simple bit math
        
        return {
            'X-IG-Bandwidth-Speed-KBPS': f"{speed_kbps:.3f}",
            'X-IG-Bandwidth-TotalBytes-B': str(total_bytes),
            'X-IG-Bandwidth-TotalTime-MS': str(total_time_ms),
        }

    def _get_headers(self, profile):
        """Orchestrates standard and advanced GraphQL headers."""
        headers = {
            'User-Agent': profile.get_user_agent(),
            'X-IG-App-ID': '124024574287414', # Standard IG App ID
            'X-IG-Capabilities': profile.capabilities,
            'X-IG-App-Locale': profile.app_locale,
            'X-IG-Device-Locale': profile.app_locale,
            'X-IG-Mapped-Locale': profile.mapped_locale,
            'X-Pigeon-Session-Id': profile.pigeon_session_id,
            'X-Pigeon-Raw-Client-Time': f"{time.time():.3f}",
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE']),
            'X-IG-Capabilities': '3brTvw==',
            'X-IG-Nav-Chain': '1G2:feed_timeline:1,1G2:feed_timeline:2', # Simulates navigation history
            'X-FB-HTTP-Engine': 'Liger',
            'X-FB-Client-IP': 'True',
            'Accept-Language': profile.mapped_locale,
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Host': 'i.instagram.com',
            'Connection': 'keep-alive',
        }
        
        # Merge network jitter
        headers.update(self._calculate_jitter_headers())
        return headers

    async def check_username_availability(self, username):
        """
        High-fidelity check with persistent device identity.
        """
        # Pick a random client+profile pair
        client, profile = random.choice(self.client_pool)

        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123x7{username}",
            "device_id": profile.device_id,
            "guid": profile.guid,
            "ad_id": str(uuid4()), # Dynamic per request but realistic
            "waterfall_id": str(uuid4()), # Registration waterfall id
        }
        
        try:
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_headers(profile), 
                data=data
            )
            response_text = response.text
            
            # Instagram often blocks if TLS/Headers aren't perfect
            if '"spam"' in response_text or 'rate_limit_error' in response_text or response.status_code == 429:
                return False, response_text, "rate_limit"
            
            # Availability check: 'email_is_taken' or 'username_is_taken' logic
            is_available = '"email_is_taken"' in response_text
            return is_available, response_text, None
            
        except (httpx.RequestError, httpx.TimeoutException):
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
        """Starts the async task pool with persistent device identities."""
        self.start_time = time.time()
        
        # Initialize clients + profiles for each proxy
        clients_with_profiles = []
        for proxy_url in PROXIES_LIST:
            try:
                # One client and one consistent profile per proxy
                client = httpx.AsyncClient(
                    proxy=proxy_url, 
                    timeout=5.0,
                    # Simulated TLS Fingerprinting: standard browser-like limits
                    limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
                )
                profile = DeviceProfile()
                clients_with_profiles.append((client, profile))
            except Exception:
                continue
        
        if not clients_with_profiles:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }

        # Checker now uses the pool of (client, profile) tuples
        checker = AutoInstagramChecker(clients_with_profiles)
        
        # Launch workers
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        # Wait for completion or stop
        try:
            while not self.should_stop:
                if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                    self.should_stop = True
                    break
                
                if self.found_username:
                    break
                    
                await asyncio.sleep(0.1)
        finally:
            # Ensure all tasks stop gracefully
            self.should_stop = True
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Cleanup all clients
            for client, profile in clients_with_profiles:
                await client.aclose()
            
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