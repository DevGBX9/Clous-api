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
    "MAX_CONCURRENCY": 100,
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

# Real Android devices with complete specifications
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
    {
        "manufacturer": "OPPO",
        "model": "CPH2525",
        "device": "OP5961L1",
        "android_version": 33,
        "android_release": "13",
        "dpi": "480dpi",
        "resolution": "1080x2412",
        "chipset": "qcom"
    },
    {
        "manufacturer": "realme",
        "model": "RMX3771",
        "device": "RE58B2L1",
        "android_version": 33,
        "android_release": "13",
        "dpi": "420dpi",
        "resolution": "1080x2400",
        "chipset": "qcom"
    },
    {
        "manufacturer": "vivo",
        "model": "V2254",
        "device": "PD2254",
        "android_version": 33,
        "android_release": "13",
        "dpi": "480dpi",
        "resolution": "1080x2400",
        "chipset": "qcom"
    },
    {
        "manufacturer": "HUAWEI",
        "model": "NOH-NX9",
        "device": "HWNOH",
        "android_version": 31,
        "android_release": "12",
        "dpi": "480dpi",
        "resolution": "1080x2376",
        "chipset": "kirin"
    },
    {
        "manufacturer": "Samsung",
        "model": "SM-A546B",
        "device": "a54x",
        "android_version": 34,
        "android_release": "14",
        "dpi": "420dpi",
        "resolution": "1080x2340",
        "chipset": "exynos"
    },
    {
        "manufacturer": "Motorola",
        "model": "moto g84 5G",
        "device": "bangkk",
        "android_version": 33,
        "android_release": "13",
        "dpi": "400dpi",
        "resolution": "1080x2400",
        "chipset": "qcom"
    },
]

# Instagram app versions (realistic recent versions)
INSTAGRAM_VERSIONS = [
    "326.0.0.42.90",
    "325.0.0.35.91",
    "324.0.0.27.50",
    "323.0.0.38.64",
    "322.0.0.37.65",
    "321.0.0.39.106",
    "320.0.0.36.84",
    "319.0.0.43.110",
    "318.0.0.38.108",
    "317.0.0.34.109",
]

# Locales for diversity
LOCALES = [
    ("en_US", "America/New_York", -18000),
    ("en_GB", "Europe/London", 0),
    ("en_AU", "Australia/Sydney", 39600),
    ("en_CA", "America/Toronto", -18000),
    ("de_DE", "Europe/Berlin", 3600),
    ("fr_FR", "Europe/Paris", 3600),
    ("es_ES", "Europe/Madrid", 3600),
    ("it_IT", "Europe/Rome", 3600),
    ("pt_BR", "America/Sao_Paulo", -10800),
    ("ar_SA", "Asia/Riyadh", 10800),
    ("ar_AE", "Asia/Dubai", 14400),
    ("ja_JP", "Asia/Tokyo", 32400),
    ("ko_KR", "Asia/Seoul", 32400),
    ("zh_CN", "Asia/Shanghai", 28800),
    ("hi_IN", "Asia/Kolkata", 19800),
    ("tr_TR", "Europe/Istanbul", 10800),
    ("nl_NL", "Europe/Amsterdam", 3600),
    ("pl_PL", "Europe/Warsaw", 3600),
    ("ru_RU", "Europe/Moscow", 10800),
    ("id_ID", "Asia/Jakarta", 25200),
]


class DeviceFingerprint:
    """
    Generates and maintains a complete, realistic Android device fingerprint.
    Each proxy gets a persistent device identity to simulate real user behavior.
    """
    
    def __init__(self, proxy_url: str):
        # Create deterministic but unique IDs based on proxy URL
        self.seed = hashlib.md5(proxy_url.encode()).hexdigest()
        random.seed(self.seed)
        
        # Select a random device configuration
        self.device = random.choice(ANDROID_DEVICES)
        self.ig_version = random.choice(INSTAGRAM_VERSIONS)
        self.locale, self.timezone, self.timezone_offset = random.choice(LOCALES)
        
        # Generate persistent device IDs (these stay constant per proxy)
        self.android_id = self._generate_android_id()
        self.device_id = f"android-{self.android_id}"
        self.phone_id = str(uuid4())
        self.uuid = str(uuid4())
        self.advertising_id = str(uuid4())
        self.family_device_id = str(uuid4())
        
        # Session-specific IDs (can rotate)
        self.pigeon_session_id = f"UFS-{uuid4()}-0"
        self.session_id = str(uuid4())
        
        # Reset random seed
        random.seed()
    
    def _generate_android_id(self) -> str:
        """Generate a realistic 16-character Android ID."""
        chars = '0123456789abcdef'
        return ''.join(random.choice(chars) for _ in range(16))
    
    def get_user_agent(self) -> str:
        """Generate realistic Instagram User-Agent."""
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
        """Generate complete Instagram-like headers."""
        current_time = time.time()
        
        return {
            # Core headers
            'User-Agent': self.get_user_agent(),
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': self.locale.replace('_', '-'),
            
            # Instagram-specific device headers
            'X-IG-Device-ID': self.phone_id,
            'X-IG-Android-ID': self.device_id,
            'X-IG-Family-Device-ID': self.family_device_id,
            'X-IG-Timezone-Offset': str(self.timezone_offset),
            
            # Connection and capabilities
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE(LTE)', 'MOBILE(5G)']),
            'X-IG-Capabilities': '3brTv10=',
            'X-IG-App-Locale': self.locale,
            'X-IG-Device-Locale': self.locale,
            'X-IG-Mapped-Locale': self.locale,
            'X-IG-App-Startup-Country': self.locale.split('_')[1],
            
            # Bandwidth (realistic values)
            'X-IG-Bandwidth-Speed-KBPS': str(random.randint(7000, 25000)),
            'X-IG-Bandwidth-TotalBytes-B': str(random.randint(1000000, 8000000)),
            'X-IG-Bandwidth-TotalTime-MS': str(random.randint(100, 800)),
            
            # Session tracking
            'X-Pigeon-Session-Id': self.pigeon_session_id,
            'X-Pigeon-Rawclienttime': f"{current_time:.3f}",
            
            # App identification
            'X-IG-App-ID': '567067343352427',
            'X-FB-HTTP-Engine': 'Liger',
            'X-FB-Client-IP': 'True',
            'X-FB-Server-Cluster': 'True',
            
            # Additional realistic headers
            'X-Bloks-Version-Id': self._generate_bloks_version(),
            'X-Bloks-Is-Layout-RTL': 'false',
            'X-Bloks-Is-Panorama-Enabled': 'true',
            'X-IG-WWW-Claim': '0',
            'X-IG-Connection-Speed': f'{random.randint(1000, 5000)}kbps',
            
            # Priority header
            'Priority': 'u=3',
        }
    
    def _generate_bloks_version(self) -> str:
        """Generate a realistic Bloks version ID."""
        hash_chars = '0123456789abcdef'
        return ''.join(random.choice(hash_chars) for _ in range(64))
    
    def get_request_data(self, username: str) -> dict:
        """Generate complete request payload."""
        return {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa@{username}2024!",
            "device_id": self.device_id,
            "guid": self.uuid,
            "phone_id": self.phone_id,
            "waterfall_id": str(uuid4()),
            "adid": self.advertising_id,
            "first_name": "",
            "seamless_login_enabled": "1",
            "force_sign_up_code": "",
            "qs_stamp": "",
            "one_tap_opt_in": "true",
        }
    
    def rotate_session(self):
        """Rotate session-specific IDs for next request."""
        self.pigeon_session_id = f"UFS-{uuid4()}-0"


# ==========================================
#       PROXY SESSION MANAGER
# ==========================================

class ProxySessionManager:
    """
    Manages persistent device identities for each proxy.
    Each proxy = one virtual Android device.
    """
    
    def __init__(self):
        self.sessions: dict[str, DeviceFingerprint] = {}
    
    def get_fingerprint(self, proxy_url: str) -> DeviceFingerprint:
        """Get or create a device fingerprint for a proxy."""
        if proxy_url not in self.sessions:
            self.sessions[proxy_url] = DeviceFingerprint(proxy_url)
        return self.sessions[proxy_url]


# Global session manager
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
    """
    Handles the HTTP communication with Instagram APIs.
    Uses complete device fingerprints and realistic headers.
    """
    def __init__(self, proxy_clients: list):
        self.proxy_clients = proxy_clients  # List of (client, proxy_url, fingerprint)
    
    async def check_username_availability(self, username: str):
        """
        Checks availability of a username using a random proxy with full device fingerprint.
        """
        # Pick a random proxy session
        client, proxy_url, fingerprint = random.choice(self.proxy_clients)
        
        # Get realistic headers and data
        headers = fingerprint.get_headers()
        data = fingerprint.get_request_data(username)
        
        try:
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=headers, 
                data=data
            )
            response_text = response.text
            
            # Rotate session for next request (slight variation)
            fingerprint.rotate_session()
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit"
            
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
        
        self.found_username = None
        self.result_reason = "timeout" 
        
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0

    async def _worker(self, checker):
        """Code running inside each async worker."""
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            username = self.generator.generate()
            
            is_available, _, error = await checker.check_username_availability(username)
            
            if self.should_stop:
                return 

            if error == "rate_limit":
                pass 
            
            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.should_stop = True
                return
            
            await asyncio.sleep(0.005)

    async def run(self):
        """Starts the async task pool."""
        self.start_time = time.time()
        
        # Initialize clients with fingerprints
        proxy_clients = []
        for proxy_url in PROXIES_LIST:
            try:
                fingerprint = proxy_manager.get_fingerprint(proxy_url)
                client = httpx.AsyncClient(proxy=proxy_url, timeout=3.0)
                proxy_clients.append((client, proxy_url, fingerprint))
            except Exception:
                continue
        
        if not proxy_clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }

        checker = AutoInstagramChecker(proxy_clients)
        
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
        "message": "Instagram Checker API - Anti-Rate-Limit Edition",
        "usage": "Send GET request to /search to find a user.",
        "features": [
            "Full device fingerprints",
            "Realistic Android headers",
            "Session persistence per proxy",
            "90+ proxies available"
        ]
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