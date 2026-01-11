#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API
==========================================

Features:
- On-Demand Search: Triggered via /search endpoint.
- High Concurrency: Uses asyncio for rapid checking.
- Smart Identity System: Each proxy gets 2 unique identities to alternate between.
- Full Device Fingerprinting: Complete Android device simulation.
- Per-Request Isolation: Each search request generates fresh fingerprints.

Author: @GBX_9 (Original Helper)
"""

import os
import sys
import time
import random
import asyncio
import logging
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from uuid import uuid4
from dataclasses import dataclass

import httpx
from flask import Flask, jsonify
from flask_cors import CORS

sys.dont_write_bytecode = True

# ==========================================
#              LOGGING SETUP
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


# ==========================================
#              CONFIGURATION
# ==========================================
CONFIG: Dict[str, Any] = {
    "INSTAGRAM_API_URL": 'https://i.instagram.com/api/v1/accounts/create/',
    "TIMEOUT_SECONDS": 30,
    "FIXED_EMAIL": "abdo1@gmail.com",
    "MAX_CONCURRENCY": 100,
    "REQUEST_TIMEOUT": 3.0,
    "PROXIES_FILE": "proxies.txt",
    "IDENTITIES_PER_PROXY": 2,  # Each proxy gets 2 identities to alternate
}

CHARS: Dict[str, str] = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._',
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]


# ==========================================
#       ANDROID DEVICE DATABASE
# ==========================================
# Real Android devices for realistic fingerprinting
ANDROID_DEVICES: List[Dict[str, Any]] = [
    {"manufacturer": "Samsung", "model": "SM-G998B", "device": "p3s", "board": "exynos2100", "android": 13, "dpi": 640, "res": "1440x3200"},
    {"manufacturer": "Samsung", "model": "SM-S908B", "device": "b0q", "board": "exynos2200", "android": 13, "dpi": 600, "res": "1440x3088"},
    {"manufacturer": "Samsung", "model": "SM-A536B", "device": "a53x", "board": "exynos1280", "android": 13, "dpi": 450, "res": "1080x2400"},
    {"manufacturer": "Samsung", "model": "SM-A525F", "device": "a52q", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2340"},
    {"manufacturer": "Samsung", "model": "SM-G930F", "device": "herolte", "board": "exynos8890", "android": 8, "dpi": 640, "res": "1440x2560"},
    {"manufacturer": "Google", "model": "Pixel 7 Pro", "device": "cheetah", "board": "google", "android": 14, "dpi": 560, "res": "1440x3120"},
    {"manufacturer": "Google", "model": "Pixel 6 Pro", "device": "raven", "board": "google", "android": 13, "dpi": 560, "res": "1440x3120"},
    {"manufacturer": "Google", "model": "Pixel 6a", "device": "bluejay", "board": "google", "android": 13, "dpi": 420, "res": "1080x2400"},
    {"manufacturer": "OnePlus", "model": "LE2123", "device": "lemonadep", "board": "lahaina", "android": 13, "dpi": 560, "res": "1440x3216"},
    {"manufacturer": "OnePlus", "model": "KB2001", "device": "kebab", "board": "kona", "android": 12, "dpi": 420, "res": "1080x2400"},
    {"manufacturer": "OnePlus", "model": "GM1917", "device": "guacamoleb", "board": "sdm855", "android": 11, "dpi": 420, "res": "1080x2340"},
    {"manufacturer": "Xiaomi", "model": "2201116SG", "device": "ingres", "board": "mt6895", "android": 13, "dpi": 480, "res": "1220x2712"},
    {"manufacturer": "Xiaomi", "model": "M2101K6G", "device": "sweet", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2400"},
    {"manufacturer": "Xiaomi", "model": "M2007J3SG", "device": "apollo", "board": "kona", "android": 11, "dpi": 440, "res": "1080x2340"},
    {"manufacturer": "OPPO", "model": "CPH2207", "device": "OP4F7C", "board": "mt6893", "android": 12, "dpi": 480, "res": "1080x2400"},
    {"manufacturer": "OPPO", "model": "CPH2083", "device": "OP4C2F", "board": "mt6765", "android": 11, "dpi": 450, "res": "1080x2400"},
    {"manufacturer": "vivo", "model": "V2111", "device": "PD2111", "board": "mt6853", "android": 12, "dpi": 480, "res": "1080x2376"},
    {"manufacturer": "realme", "model": "RMX3085", "device": "RE54E4L1", "board": "mt6785", "android": 11, "dpi": 450, "res": "1080x2400"},
    {"manufacturer": "HUAWEI", "model": "VOG-L29", "device": "HWVOG", "board": "kirin980", "android": 10, "dpi": 480, "res": "1080x2340"},
    {"manufacturer": "HONOR", "model": "ANY-LX2", "device": "HNANY-Q1", "board": "qcom", "android": 11, "dpi": 480, "res": "1080x2298"},
]

# Instagram app versions (real versions)
INSTAGRAM_VERSIONS: List[str] = [
    "269.0.0.18.75", "268.0.0.23.118", "267.0.0.19.93", "266.0.0.22.105",
    "265.0.0.19.301", "264.0.0.22.106", "263.0.0.22.103", "262.0.0.27.101",
    "261.0.0.21.111", "260.0.0.29.95", "259.0.0.21.100", "258.0.0.26.100",
    "257.0.0.21.115", "256.0.0.21.109", "255.0.0.17.102", "254.0.0.19.109",
]


# ==========================================
#       DEVICE FINGERPRINT GENERATOR
# ==========================================
@dataclass
class DeviceIdentity:
    """Complete Android device identity for Instagram API requests."""
    user_agent: str
    device_id: str
    phone_id: str
    guid: str
    adid: str
    google_adid: str
    family_device_id: str
    headers: Dict[str, str]
    
    def get_request_data(self, username: str, email: str) -> Dict[str, str]:
        """Generate request data with this identity."""
        return {
            "email": email,
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": self.device_id,
            "phone_id": self.phone_id,
            "guid": self.guid,
            "adid": self.adid,
            "google_adid": self.google_adid,
            "family_device_id": self.family_device_id,
        }


class FingerprintGenerator:
    """Generates realistic Android device fingerprints."""
    
    @staticmethod
    def generate_device_id() -> str:
        """Generate android device ID."""
        return f"android-{uuid4().hex[:16]}"
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate standard UUID."""
        return str(uuid4())
    
    @staticmethod
    def generate_advertising_id() -> str:
        """Generate Google Advertising ID format."""
        return str(uuid4())
    
    @staticmethod
    def generate_family_device_id() -> str:
        """Generate family device ID."""
        return str(uuid4())
    
    def generate_identity(self) -> DeviceIdentity:
        """Generate a complete device identity."""
        device = random.choice(ANDROID_DEVICES)
        ig_version = random.choice(INSTAGRAM_VERSIONS)
        
        # Build User-Agent
        user_agent = (
            f"Instagram {ig_version} Android "
            f"({device['android']}/{device['android']}.0; "
            f"{device['dpi']}dpi; {device['res']}; "
            f"{device['manufacturer']}; {device['model']}; "
            f"{device['device']}; {device['board']}; en_US)"
        )
        
        # Generate all device IDs
        device_id = self.generate_device_id()
        phone_id = self.generate_uuid()
        guid = self.generate_uuid()
        adid = self.generate_advertising_id()
        google_adid = self.generate_advertising_id()
        family_device_id = self.generate_family_device_id()
        
        # Build headers
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept-Language': random.choice(['en-US', 'en-GB', 'en-CA', 'en-AU']),
            'X-IG-Capabilities': random.choice(['AQ==', 'Aw==', '36oD']),
            'Accept-Encoding': 'gzip, deflate',
            'User-Agent': user_agent,
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G']),
            'X-IG-Bandwidth-Speed-KBPS': str(random.randint(2000, 10000)),
            'X-IG-Bandwidth-TotalBytes-B': str(random.randint(1000000, 8000000)),
            'X-IG-Bandwidth-TotalTime-MS': str(random.randint(50, 300)),
            'X-IG-App-ID': '567067343352427',
            'X-IG-Device-ID': guid,
            'X-IG-Android-ID': device_id,
        }
        
        return DeviceIdentity(
            user_agent=user_agent,
            device_id=device_id,
            phone_id=phone_id,
            guid=guid,
            adid=adid,
            google_adid=google_adid,
            family_device_id=family_device_id,
            headers=headers,
        )
    
    def generate_batch(self, count: int) -> List[DeviceIdentity]:
        """Generate multiple unique identities."""
        return [self.generate_identity() for _ in range(count)]


# ==========================================
#       PROXY IDENTITY MANAGER
# ==========================================
@dataclass
class ProxyWithIdentities:
    """A proxy with its two assigned identities."""
    proxy_url: str
    identity_a: DeviceIdentity
    identity_b: DeviceIdentity
    current_identity: int = 0  # 0 = A, 1 = B
    request_count: int = 0
    
    def get_identity(self) -> DeviceIdentity:
        """Get current identity and alternate for next call."""
        if self.current_identity == 0:
            identity = self.identity_a
        else:
            identity = self.identity_b
        
        # Alternate for next request
        self.current_identity = 1 - self.current_identity
        self.request_count += 1
        
        return identity


class IdentityPool:
    """Manages proxy-identity assignments for a search session."""
    
    def __init__(self, proxies: List[str]):
        self.proxies = proxies
        self.proxy_identities: List[ProxyWithIdentities] = []
        self._initialize()
    
    def _initialize(self) -> None:
        """Generate identities and assign to proxies."""
        generator = FingerprintGenerator()
        
        # Generate 2 identities per proxy
        total_identities = len(self.proxies) * CONFIG["IDENTITIES_PER_PROXY"]
        identities = generator.generate_batch(total_identities)
        
        logger.info(f"Generated {total_identities} device identities for {len(self.proxies)} proxies")
        
        # Assign 2 identities to each proxy
        for i, proxy in enumerate(self.proxies):
            identity_a = identities[i * 2]
            identity_b = identities[i * 2 + 1]
            
            self.proxy_identities.append(ProxyWithIdentities(
                proxy_url=proxy,
                identity_a=identity_a,
                identity_b=identity_b,
            ))
    
    def get_random_proxy_identity(self) -> ProxyWithIdentities:
        """Get a random proxy with its identity."""
        return random.choice(self.proxy_identities)
    
    def get_stats(self) -> Dict[str, int]:
        """Get usage statistics."""
        total_requests = sum(p.request_count for p in self.proxy_identities)
        return {
            "total_proxies": len(self.proxy_identities),
            "total_identities": len(self.proxy_identities) * 2,
            "total_requests": total_requests,
        }


# ==========================================
#              HELPER FUNCTIONS
# ==========================================
def load_proxies_from_file(filepath: str) -> List[str]:
    """Load proxies from an external file."""
    proxies: List[str] = []
    file_path = Path(__file__).parent / filepath
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies from {filepath}")
    except FileNotFoundError:
        logger.error(f"Proxies file not found: {filepath}")
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")
    
    return proxies


PROXIES_LIST: List[str] = load_proxies_from_file(CONFIG["PROXIES_FILE"])


# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)


# ==========================================
#              CORE LOGIC
# ==========================================
class AutoUsernameGenerator:
    """Generates valid 5-character Instagram usernames."""
    
    def __init__(self) -> None:
        self.generated_usernames: set[str] = set()
    
    def is_valid_instagram_username(self, username: str) -> bool:
        """Validates username against Instagram's rules."""
        if len(username) != 5:
            return False
        
        allowed_chars = set(CHARS["ALL_VALID"] + CHARS["SYMBOLS"])
        if not all(char in allowed_chars for char in username):
            return False
        
        if username.startswith('.') or username.endswith('.'):
            return False
        
        invalid_patterns = ['..', '._', '_.', '__']
        if any(pattern in username for pattern in invalid_patterns):
            return False
        
        if username[0] in CHARS["DIGITS"]:
            return False
        
        return True
    
    def generate(self) -> str:
        """Generates a unique, compliant 5-char username."""
        max_attempts = 10
        
        for _ in range(max_attempts):
            username = random.choice(CHARS["LETTERS"])
            username += ''.join(random.choices(CHARS["ALL_VALID"], k=4))
            
            if username not in self.generated_usernames and self.is_valid_instagram_username(username):
                self.generated_usernames.add(username)
                return username
        
        timestamp = int(time.time() * 1000) % 10000
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:04d}"[:5]
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    """Handles Instagram API communication with identity rotation."""
    
    def __init__(self, identity_pool: IdentityPool):
        self.identity_pool = identity_pool
        self.clients: Dict[str, httpx.AsyncClient] = {}
    
    async def _get_client(self, proxy_url: str) -> httpx.AsyncClient:
        """Get or create async client for proxy."""
        if proxy_url not in self.clients:
            self.clients[proxy_url] = httpx.AsyncClient(
                proxy=proxy_url,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
        return self.clients[proxy_url]
    
    async def check_username_availability(self, username: str) -> Tuple[bool, str, Optional[str]]:
        """Check username availability using smart identity rotation."""
        proxy_identity = self.identity_pool.get_random_proxy_identity()
        identity = proxy_identity.get_identity()
        
        try:
            client = await self._get_client(proxy_identity.proxy_url)
            
            data = identity.get_request_data(username, CONFIG["FIXED_EMAIL"])
            
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"],
                headers=identity.headers,
                data=data
            )
            response_text = response.text
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                logger.warning(f"Rate limit on proxy: {proxy_identity.proxy_url[:30]}...")
                return False, response_text, "rate_limit"
            
            is_available = '"email_is_taken"' in response_text
            
            if is_available:
                logger.info(f"✅ Found available username: {username}")
            
            return is_available, response_text, None
            
        except httpx.TimeoutException:
            return False, "", "timeout"
        except httpx.RequestError:
            return False, "", "connection_error"
    
    async def close_all(self) -> None:
        """Close all HTTP clients."""
        for client in self.clients.values():
            try:
                await client.aclose()
            except Exception:
                pass
        self.clients.clear()


class SearchSession:
    """Orchestrates a single on-demand search request."""
    
    def __init__(self) -> None:
        self.generator = AutoUsernameGenerator()
        self.found_username: Optional[str] = None
        self.result_reason: str = "timeout"
        self.should_stop: bool = False
        self.max_concurrency: int = CONFIG["MAX_CONCURRENCY"]
        self.start_time: float = 0

    async def _worker(self, checker: AutoInstagramChecker) -> None:
        """Async worker for checking usernames."""
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                return

            username = self.generator.generate()
            is_available, _, error = await checker.check_username_availability(username)
            
            if self.should_stop:
                return

            if error == "rate_limit":
                await asyncio.sleep(0.5)
                continue
            
            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.should_stop = True
                return
            
            await asyncio.sleep(0.01)

    async def run(self) -> Dict[str, Any]:
        """Start the search session."""
        self.start_time = time.time()
        logger.info("=" * 50)
        logger.info("Starting new search session...")
        
        if not PROXIES_LIST:
            logger.error("No proxies available")
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }
        
        # Create fresh identity pool for this request
        identity_pool = IdentityPool(PROXIES_LIST)
        checker = AutoInstagramChecker(identity_pool)
        
        try:
            tasks = [
                asyncio.create_task(self._worker(checker))
                for _ in range(self.max_concurrency)
            ]
            
            while not self.should_stop:
                if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                    self.should_stop = True
                    logger.info("Search timed out")
                    break
                
                if self.found_username:
                    break
                    
                await asyncio.sleep(0.1)

            self.should_stop = True
            await asyncio.gather(*tasks, return_exceptions=True)
            
        finally:
            await checker.close_all()
        
        duration = round(time.time() - self.start_time, 2)
        stats = identity_pool.get_stats()
        
        result = {
            "status": "success" if self.found_username else "failed",
            "username": self.found_username,
            "reason": self.result_reason if not self.found_username else None,
            "duration": duration,
            "stats": stats
        }
        
        logger.info(f"Search completed: {result}")
        logger.info("=" * 50)
        return result


# ==========================================
#              API ROUTES
# ==========================================
@app.route('/')
def home() -> Dict[str, Any]:
    """Root endpoint for health checks."""
    return jsonify({
        "status": "online",
        "message": "Instagram Checker API with Smart Identity Rotation",
        "usage": "GET /search to find available username",
        "proxies_loaded": len(PROXIES_LIST),
        "identities_per_request": len(PROXIES_LIST) * CONFIG["IDENTITIES_PER_PROXY"],
    })


@app.route('/search')
async def search() -> Dict[str, Any]:
    """Trigger a search session with fresh identities."""
    session = SearchSession()
    result = await session.run()
    return jsonify(result)


# ==========================================
#              MAIN ENTRY POINT
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting server on port {port}")
    logger.info(f"Loaded {len(PROXIES_LIST)} proxies")
    logger.info(f"Each request will generate {len(PROXIES_LIST) * 2} unique device identities")
    app.run(host='0.0.0.0', port=port)