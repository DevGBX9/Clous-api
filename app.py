#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API with Advanced Device Fingerprinting
================================================================================

This script runs a Flask API that checks for available 5-character Instagram usernames.
Enhanced with complete Android device simulation and mobile API reverse engineering.

Features:
- On-Demand Search: Triggered via /search endpoint.
- High Concurrency: Uses asyncio for rapid checking with 100+ concurrent requests.
- Advanced Device Fingerprinting: Full Android hardware/software simulation.
- Proxy Rotation: 80+ residential/mobile proxies with session persistence.
- GraphQL & Pigeon Session: Complete Instagram mobile API simulation.
- Zero Speed Impact: O(1) header generation with atomic consistency.

Author: @GBX_9 (Original Helper)
Enhanced by: Senior Security Engineer (Network Deobfuscation Specialist)
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
    "MAX_CONCURRENCY": 100,
}

# Values for username generation
CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

# Rotating Proxies (Format: http://user:pass@ip:port) - 80+ proxies
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
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for decoupled frontend access


# ==========================================
#              DEVICE FINGERPRINTING
# ==========================================

class DeviceProfile:
    """
    Atomic Device Fingerprinting - Simulates real Android hardware/software stack.
    Once instantiated, all attributes remain consistent for the session.
    """
    
    # Real-world Android device database (O(1) lookup)
    DEVICE_DATABASE = {
        # Samsung Galaxy S21 Ultra (5G)
        "samsung_s21u": {
            "manufacturer": "samsung",
            "model": "SM-G998B",
            "codename": "z3s",
            "android_version": "13",
            "android_sdk": "33",
            "screen_res": "1440x3200",
            "density": "515dpi",
            "cpu_arch": "arm64-v8a",
            "build_id": "TP1A.220624.014.G998BXXS7EWI2",
            "kernel": "5.4.86-qgki-g9d6d6d3d8d4e",
            "chipset": "Qualcomm Snapdragon 888",
            "gpu": "Adreno 660",
            "ram_mb": "12288",
            "storage_gb": "256",
            "board": "z3sxxx",
            "bootloader": "G998BXXS7EWI2",
            "hardware": "qcom",
            "radio_version": "G998BXXU7EWAC",
            "carrier": "android",
            "locale_weight": 35  # Percentage weight for region distribution
        },
        # Google Pixel 7 Pro
        "pixel_7pro": {
            "manufacturer": "Google",
            "model": "Pixel 7 Pro",
            "codename": "raven",
            "android_version": "14",
            "android_sdk": "34",
            "screen_res": "1440x3120",
            "density": "512dpi",
            "cpu_arch": "arm64-v8a",
            "build_id": "UQ1A.240105.002",
            "kernel": "5.10.81-android12-9-00001-gb5c4b4b4b4b4",
            "chipset": "Google Tensor G2",
            "gpu": "Mali-G710",
            "ram_mb": "12288",
            "storage_gb": "128",
            "board": "raven",
            "bootloader": "slider-1.2-8735139",
            "hardware": "raven",
            "radio_version": "g5123b-00008-220602-B-8810521",
            "carrier": "google",
            "locale_weight": 25
        },
        # OnePlus 11
        "oneplus_11": {
            "manufacturer": "OnePlus",
            "model": "CPH2449",
            "codename": "lemonade",
            "android_version": "13",
            "android_sdk": "33",
            "screen_res": "1440x3216",
            "density": "525dpi",
            "cpu_arch": "arm64-v8a",
            "build_id": "CPH2449_11_A.06",
            "kernel": "5.10.66-android12-9-00001-g77c9c9c9c9c",
            "chipset": "Qualcomm Snapdragon 8 Gen 2",
            "gpu": "Adreno 740",
            "ram_mb": "16384",
            "storage_gb": "256",
            "board": "lemonade",
            "bootloader": "unknown",
            "hardware": "qcom",
            "radio_version": "LEMONADET_11_A.06",
            "carrier": "oneplus",
            "locale_weight": 20
        },
        # Xiaomi 13 Pro
        "xiaomi_13pro": {
            "manufacturer": "Xiaomi",
            "model": "2210132C",
            "codename": "nuwa",
            "android_version": "13",
            "android_sdk": "33",
            "screen_res": "1440x3200",
            "density": "522dpi",
            "cpu_arch": "arm64-v8a",
            "build_id": "TKQ1.221114.001",
            "kernel": "5.15.41-android12-9-00001-g8a2b2b2b2b",
            "chipset": "Qualcomm Snapdragon 8 Gen 2",
            "gpu": "Adreno 740",
            "ram_mb": "12288",
            "storage_gb": "256",
            "board": "nuwa",
            "bootloader": "unknown",
            "hardware": "qcom",
            "radio_version": "2210132C_V14.0.4.0.TMBCNXM",
            "carrier": "xiaomi",
            "locale_weight": 15
        },
        # Samsung Galaxy A54
        "samsung_a54": {
            "manufacturer": "samsung",
            "model": "SM-A546B",
            "codename": "a54x",
            "android_version": "13",
            "android_sdk": "33",
            "screen_res": "1080x2340",
            "density": "450dpi",
            "cpu_arch": "arm64-v8a",
            "build_id": "TP1A.220624.014.A546BXXS4AWG6",
            "kernel": "5.15.41-android12-9-00001-g8a2b2b2b2b",
            "chipset": "Samsung Exynos 1380",
            "gpu": "Mali-G68 MP5",
            "ram_mb": "8192",
            "storage_gb": "128",
            "board": "a54x",
            "bootloader": "A546BXXS4AWG6",
            "hardware": "s5e8835",
            "radio_version": "A546BXXU4AWG7",
            "carrier": "android",
            "locale_weight": 5
        }
    }
    
    # Global region distribution with locale mappings (weighted)
    REGION_DISTRIBUTION = {
        "en_US": {"weight": 40, "country": "US", "language": "en", "timezone": "America/New_York"},
        "en_GB": {"weight": 15, "country": "GB", "language": "en", "timezone": "Europe/London"},
        "de_DE": {"weight": 12, "country": "DE", "language": "de", "timezone": "Europe/Berlin"},
        "fr_FR": {"weight": 10, "country": "FR", "language": "fr", "timezone": "Europe/Paris"},
        "es_ES": {"weight": 8, "country": "ES", "language": "es", "timezone": "Europe/Madrid"},
        "it_IT": {"weight": 5, "country": "IT", "language": "it", "timezone": "Europe/Rome"},
        "pt_BR": {"weight": 5, "country": "BR", "language": "pt", "timezone": "America/Sao_Paulo"},
        "ja_JP": {"weight": 3, "country": "JP", "language": "ja", "timezone": "Asia/Tokyo"},
        "ar_SA": {"weight": 2, "country": "SA", "language": "ar", "timezone": "Asia/Riyadh"}
    }
    
    # Instagram Capability Bitmasks (real-world observed)
    IG_CAPABILITIES = [
        "3brTvw==",     # Standard capabilities
        "AQ==",         # Minimal
        "3brTvx==",     # Extended
        "3brTvwE=",     # With Explore
        "3brTvwM=",     # With Maps
    ]
    
    def __init__(self, device_key=None):
        """Initialize atomic device fingerprint - O(1) complexity"""
        # Select device profile
        if device_key and device_key in self.DEVICE_DATABASE:
            self.device = self.DEVICE_DATABASE[device_key]
        else:
            # Weighted random selection
            devices = list(self.DEVICE_DATABASE.keys())
            weights = [self.DEVICE_DATABASE[d]["locale_weight"] for d in devices]
            selected = random.choices(devices, weights=weights, k=1)[0]
            self.device = self.DEVICE_DATABASE[selected]
        
        # Generate consistent unique identifiers
        self.session_id = str(uuid4())
        self.device_id = f"android-{uuid4()}"
        self.android_id = self._generate_android_id()
        self.phone_id = str(uuid4())
        self.ad_id = str(uuid4())
        
        # Generate installation fingerprint
        self.app_install_id = str(uuid4())
        self.app_startup_count = random.randint(1, 5000)
        
        # Select locale based on weighted distribution
        locales = list(self.REGION_DISTRIBUTION.keys())
        weights = [self.REGION_DISTRIBUTION[l]["weight"] for l in locales]
        self.locale = random.choices(locales, weights=weights, k=1)[0]
        self.region_info = self.REGION_DISTRIBUTION[self.locale]
        
        # Session persistence counters
        self.nav_chain = []
        self.request_count = 0
        self.pigeon_session_id = str(uuid4())
        
        # TLS/Network simulation
        self.tls_version = "1.3"
        self.cipher_suite = "TLS_AES_128_GCM_SHA256"
        
        # Pre-compute headers for O(1) performance
        self._cached_headers = None
        
    def _generate_android_id(self):
        """Generate 16-character hex Android ID"""
        return ''.join(random.choices('0123456789abcdef', k=16))
    
    def _generate_nav_chain(self):
        """Generate realistic navigation chain"""
        actions = ["DirectHome", "FeedTimeline", "Profile", "ExplorePop", "Notification"]
        chain = []
        depth = random.randint(1, 5)
        
        for i in range(depth):
            action = random.choice(actions)
            if not chain or action != chain[-1]:
                chain.append(action)
        
        self.nav_chain = chain
        return ".".join(chain)
    
    def _generate_bandwidth_headers(self):
        """Generate realistic network bandwidth headers with jitter simulation"""
        # Base values with device-specific adjustments
        base_speed = random.randint(5000, 30000)  # Kbps
        jitter = random.randint(-1000, 1000)
        speed = max(1000, base_speed + jitter)
        
        # Simulate network conditions
        if random.random() < 0.3:  # 30% chance of poor connection
            speed = random.randint(1000, 5000)
        
        # Calculate bytes transferred with realistic variance
        total_bytes = random.randint(500000, 5000000)
        total_time = int((total_bytes * 8) / (speed * 1024))  # Convert to ms
        
        # Add ±20% variance for realism
        time_variance = random.randint(-int(total_time * 0.2), int(total_time * 0.2))
        total_time = max(50, total_time + time_variance)
        
        return {
            "X-IG-Bandwidth-Speed-KBPS": str(speed),
            "X-IG-Bandwidth-TotalBytes-B": str(total_bytes),
            "X-IG-Bandwidth-TotalTime-MS": str(total_time)
        }
    
    def get_headers(self):
        """Get complete Instagram Android headers - O(1) after initialization"""
        if self._cached_headers is None:
            self._cached_headers = self._build_headers()
        return self._cached_headers.copy()
    
    def _build_headers(self):
        """Build atomic header set with GraphQL and Pigeon session integration"""
        self.request_count += 1
        
        # Core Instagram headers
        headers = {
            # Identity Headers
            'X-IG-Device-ID': self.device_id,
            'X-IG-Android-ID': self.android_id,
            'X-IG-Pigeon-Session-Id': self.pigeon_session_id,
            'X-IG-Pigeon-Rawclienttime': str(int(time.time() * 1000)),
            'X-IG-Device-Locale': self.locale,
            'X-IG-Mapped-Locale': self.locale,
            'X-IG-App-Locale': self.locale,
            'X-IG-App-Startup-Count': str(self.app_startup_count),
            
            # Application Headers
            'X-IG-App-ID': '567067343352427',  # Instagram Android
            'X-IG-Capabilities': random.choice(self.IG_CAPABILITIES),
            'X-IG-Connection-Type': random.choice(['WIFI', 'WIFI.802.11ac', 'MOBILE.LTE', 'MOBILE.5G']),
            'X-IG-Nav-Chain': self._generate_nav_chain(),
            'X-IG-Nav-Start': str(int((time.time() - random.randint(1, 3600)) * 1000)),
            
            # Facebook Infrastructure
            'X-FB-HTTP-Engine': 'Liger',
            'X-FB-Client-IP': 'True',
            'X-FB-Connection-Type': 'WIFI',
            'X-FB-Net-HNI': str(random.randint(10000, 99999)),
            'X-FB-SIM-HNI': str(random.randint(10000, 99999)),
            
            # Device Hardware Headers
            'X-IG-Device-SIM-Country': self.region_info["country"],
            'X-IG-Device-Country': self.region_info["country"],
            'X-IG-Timezone-Offset': str(random.randint(-43200, 50400)),
            'X-IG-Connection-Speed': f"{random.randint(1, 5)}G",
            
            # Standard Headers
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': self.region_info["language"] + '-US',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Host': 'i.instagram.com',
            
            # TLS Fingerprint Simulation
            'X-IG-TLS-Version': self.tls_version,
            'X-IG-Cipher-Suite': self.cipher_suite,
        }
        
        # Add bandwidth headers with jitter
        headers.update(self._generate_bandwidth_headers())
        
        # Build User-Agent with atomic consistency
        device = self.device
        headers['User-Agent'] = (
            f'Instagram {random.choice(["291.0", "292.0", "293.0", "294.0"])}.0.0.'
            f'{random.randint(19, 26)}.{random.randint(109, 128)} Android '
            f'({device["android_sdk"]}/{device["android_version"]}; '
            f'{device["density"]}; {device["screen_res"]}; {device["manufacturer"]}; '
            f'{device["model"]}; {device["codename"]}; {device["hardware"]}; {self.locale})'
        )
        
        return headers


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
    Enhanced Instagram checker with complete mobile API simulation.
    Maintains atomic device consistency per proxy session.
    """
    def __init__(self, client_proxy_pairs):
        # Store (client, proxy_url) pairs
        self.client_proxy_pairs = client_proxy_pairs
        
        # Map proxy URLs to device profiles
        self.proxy_profiles = {}
        
        # Initialize device profile for each unique proxy
        for _, proxy_url in self.client_proxy_pairs:
            if proxy_url not in self.proxy_profiles:
                self.proxy_profiles[proxy_url] = DeviceProfile()
    
    def _get_instagram_payload(self, username, device_profile):
        """Build Instagram API payload with device-specific parameters"""
        return {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "first_name": "Instagram",
            "password": f"Aa123456{username}@{random.randint(1000, 9999)}",
            "device_id": device_profile.device_id,
            "guid": device_profile.android_id,
            "phone_id": device_profile.phone_id,
            "ad_id": device_profile.ad_id,
            "session_id": device_profile.session_id,
            "waterfall_id": str(uuid4()),
            "reg_flow_taken": "1",
            "force_sign_up_code": "",
            "qs_stamp": "",
            "day": str(random.randint(1, 28)),
            "month": str(random.randint(1, 12)),
            "year": str(random.randint(1980, 2005)),
            "tos_version": "row",
            "one_tap_opt_in": "true"
        }
    
    async def check_username_availability(self, username):
        """
        Check username availability with full device simulation.
        Returns: (is_available, response_text, error_type)
        """
        # Pick random client and its associated proxy URL
        client, proxy_url = random.choice(self.client_proxy_pairs)
        device_profile = self.proxy_profiles[proxy_url]
        
        try:
            # Generate payload and headers
            payload = self._get_instagram_payload(username, device_profile)
            headers = device_profile.get_headers()
            
            # Add GraphQL-specific headers for API v1
            headers.update({
                'X-IG-API-Version': '3',
                'X-IG-WWW-Claim': '0',
                'X-IG-Set-Authorization': 'Bearer IGT:2',
                'X-MID': device_profile.session_id[:20],
                'X-Pigeon-Rawclienttime': str(int(time.time() * 1000)),
                'X-Pigeon-Session-Id': device_profile.pigeon_session_id,
            })
            
            # Simulate request timing variance (1-50ms)
            await asyncio.sleep(random.uniform(0.001, 0.05))
            
            # Execute request
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"],
                headers=headers,
                data=payload,
                timeout=httpx.Timeout(3.0, connect=1.0)
            )
            
            response_text = response.text
            
            # Rate limit detection with enhanced patterns
            rate_limit_indicators = [
                '"spam"',
                'rate_limit_error',
                'challenge_required',
                'checkpoint_required',
                'sentry_block',
                'login_required',
                'invalid_request',
                'Please wait a few minutes'
            ]
            
            if any(indicator in response_text for indicator in rate_limit_indicators):
                return False, response_text, "rate_limit"
            
            # Check username availability
            # Instagram returns "email_is_taken": true when username is taken
            # "username_is_taken" field may not always be present
            if '"email_is_taken"' in response_text:
                # Username is available
                return True, response_text, None
            elif '"username_is_taken"' in response_text:
                # Username is taken
                return False, response_text, None
            elif '"errors"' in response_text:
                # Other validation errors
                return False, response_text, "validation_error"
            else:
                # Default fallback - if no clear indicators, assume taken
                return False, response_text, "unknown_response"
            
        except httpx.TimeoutException:
            return False, "", "timeout"
        except httpx.ProxyError:
            return False, "", "proxy_error"
        except httpx.RequestError as e:
            return False, str(e), "request_error"
        except Exception as e:
            return False, str(e), "unexpected_error"


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
        
        # Initialize clients with their proxy URLs
        client_proxy_pairs = []
        for proxy_url in PROXIES_LIST:
            try:
                # httpx.AsyncClient manages the connection pool for this proxy
                client = httpx.AsyncClient(
                    proxy=proxy_url,
                    timeout=httpx.Timeout(3.0, connect=1.0),
                    limits=httpx.Limits(max_keepalive_connections=10, max_connections=100)
                )
                client_proxy_pairs.append((client, proxy_url))
            except Exception:
                continue
        
        if not client_proxy_pairs:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }

        checker = AutoInstagramChecker(client_proxy_pairs)
        
        # Launch workers
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        # Wait for completion or stop
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            
            # Check if all tasks finished
            if self.found_username:
                break
                
            await asyncio.sleep(0.1)

        # Ensure all tasks stop
        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cleanup clients
        for client, _ in client_proxy_pairs:
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
        "message": "Instagram Checker API is running with Advanced Device Fingerprinting.",
        "version": "6.0",
        "features": [
            "80+ Rotating Proxies",
            "Complete Android Device Simulation",
            "GraphQL & Pigeon Session Support",
            "TLS Fingerprinting Awareness",
            "Regional Localization (9 regions)"
        ],
        "usage": "Send GET request to /search to find a 5-character username."
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
    # Use waitress for production
    from waitress import serve
    serve(app, host='0.0.0.0', port=port)