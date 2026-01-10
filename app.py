#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API
==========================================

Uses Instagram Web API for reliable username checking.
Fetches proxies dynamically from Firebase Realtime Database.
Prioritizes stable_proxies over regular proxies.
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

sys.dont_write_bytecode = True

# ==========================================
#              CONFIGURATION
# ==========================================
CONFIG = {
    "CHECK_USERNAME_URL": "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
    "TIMEOUT_SECONDS": 30,
    "MAX_CONCURRENCY": 30,
    
    # Firebase Database URLs
    "FIREBASE_STABLE_PROXIES": "https://clous-proxys-qpi-default-rtdb.firebaseio.com/stable_proxies.json",
    "FIREBASE_PROXIES": "https://clous-proxys-qpi-default-rtdb.firebaseio.com/proxies.json",
    
    # Proxy cache settings
    "PROXY_CACHE_TTL": 60,  # Refresh proxies every 60 seconds
}

CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

# Web User Agents
WEB_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


# ==========================================
#         FIREBASE PROXY MANAGER
# ==========================================

class FirebaseProxyManager:
    """
    Manages proxy fetching from Firebase Realtime Database.
    Prioritizes stable_proxies over regular proxies.
    """
    
    def __init__(self):
        self.proxies = []
        self.stable_proxies = []
        self.last_fetch = 0
        self.fetch_lock = asyncio.Lock()
    
    async def fetch_proxies(self):
        """Fetch proxies from Firebase, with caching."""
        current_time = time.time()
        
        # Check if cache is still valid
        if self.proxies and (current_time - self.last_fetch) < CONFIG["PROXY_CACHE_TTL"]:
            return self._get_prioritized_list()
        
        async with self.fetch_lock:
            # Double-check after acquiring lock
            if self.proxies and (current_time - self.last_fetch) < CONFIG["PROXY_CACHE_TTL"]:
                return self._get_prioritized_list()
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    # Fetch stable_proxies first (priority)
                    stable_response = await client.get(CONFIG["FIREBASE_STABLE_PROXIES"])
                    stable_data = stable_response.json() if stable_response.status_code == 200 else None
                    
                    # Fetch regular proxies
                    proxies_response = await client.get(CONFIG["FIREBASE_PROXIES"])
                    proxies_data = proxies_response.json() if proxies_response.status_code == 200 else None
                    
                    # Extract addresses
                    self.stable_proxies = []
                    self.proxies = []
                    
                    if stable_data:
                        for key, value in stable_data.items():
                            if isinstance(value, dict) and 'address' in value:
                                self.stable_proxies.append(value['address'])
                    
                    if proxies_data:
                        for key, value in proxies_data.items():
                            if isinstance(value, dict) and 'address' in value:
                                # Don't add duplicates that are already in stable
                                if value['address'] not in self.stable_proxies:
                                    self.proxies.append(value['address'])
                    
                    self.last_fetch = current_time
                    
                    print(f"[Firebase] Loaded {len(self.stable_proxies)} stable + {len(self.proxies)} regular proxies")
                    
            except Exception as e:
                print(f"[Firebase] Error fetching proxies: {e}")
                # Keep using old proxies if fetch fails
        
        return self._get_prioritized_list()
    
    def _get_prioritized_list(self):
        """
        Returns a prioritized list of proxies.
        stable_proxies appear 3x more often to increase their usage.
        """
        prioritized = []
        
        # Add stable proxies 3 times (3x priority)
        prioritized.extend(self.stable_proxies * 3)
        
        # Add regular proxies once
        prioritized.extend(self.proxies)
        
        return prioritized
    
    def get_stats(self):
        """Get current proxy stats."""
        return {
            "stable_count": len(self.stable_proxies),
            "regular_count": len(self.proxies),
            "total_unique": len(self.stable_proxies) + len(self.proxies),
            "last_fetch": self.last_fetch,
        }


# Global proxy manager
proxy_manager = FirebaseProxyManager()


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


class WebInstagramChecker:
    """Uses Instagram Web API for checking usernames."""
    
    def __init__(self, proxy_clients: list, stats: dict):
        self.proxy_clients = proxy_clients
        self.stats = stats
        self.csrf_tokens = {}
    
    def _get_headers(self, csrf_token: str = None) -> dict:
        headers = {
            'User-Agent': random.choice(WEB_USER_AGENTS),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://www.instagram.com',
            'Referer': 'https://www.instagram.com/accounts/emailsignup/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'X-Requested-With': 'XMLHttpRequest',
            'X-IG-App-ID': '936619743392459',
            'X-ASBD-ID': '129477',
            'X-IG-WWW-Claim': '0',
        }
        if csrf_token:
            headers['X-CSRFToken'] = csrf_token
        return headers
    
    async def _get_csrf_token(self, client) -> str:
        """Get CSRF token from Instagram."""
        try:
            response = await client.get(
                'https://www.instagram.com/accounts/emailsignup/',
                headers={
                    'User-Agent': random.choice(WEB_USER_AGENTS),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                }
            )
            
            cookies = response.cookies
            csrf = cookies.get('csrftoken', '')
            if csrf:
                return csrf
            
            text = response.text
            if 'csrf_token' in text:
                import re
                match = re.search(r'"csrf_token":"([^"]+)"', text)
                if match:
                    return match.group(1)
            
            return hashlib.md5(str(uuid4()).encode()).hexdigest()[:32]
            
        except Exception:
            return hashlib.md5(str(uuid4()).encode()).hexdigest()[:32]
    
    async def check_username_availability(self, username: str):
        """Check if username is available using Web API."""
        client, proxy_url, is_stable = random.choice(self.proxy_clients)
        
        try:
            if proxy_url not in self.csrf_tokens:
                self.csrf_tokens[proxy_url] = await self._get_csrf_token(client)
            
            csrf_token = self.csrf_tokens[proxy_url]
            
            headers = self._get_headers(csrf_token)
            headers['Cookie'] = f'csrftoken={csrf_token}; ig_did={uuid4()}; mid={hashlib.md5(str(uuid4()).encode()).hexdigest()[:26]}'
            
            data = {
                'email': f'{username}_{random.randint(1000,9999)}@gmail.com',
                'username': username,
                'first_name': '',
                'opt_into_one_tap': 'false',
            }
            
            response = await client.post(
                CONFIG["CHECK_USERNAME_URL"],
                headers=headers,
                data=data
            )
            
            response_text = response.text
            self.stats["total_requests"] += 1
            
            if is_stable:
                self.stats["stable_proxy_requests"] += 1
            
            if self.stats["total_requests"] <= 3:
                self.stats["sample_response"] = response_text[:500]
            
            if 'username_is_taken' in response_text or '"username":' in response_text:
                self.stats["username_taken"] += 1
                return False, response_text, "taken"
            
            if '"errors"' in response_text and 'username' not in response_text.lower():
                self.stats["available_found"] += 1
                return True, response_text, None
            
            if 'email_is_taken' in response_text:
                self.stats["available_found"] += 1
                return True, response_text, None
            
            if '"spam"' in response_text or 'spam' in response_text.lower():
                self.stats["spam_errors"] += 1
                if proxy_url in self.csrf_tokens:
                    del self.csrf_tokens[proxy_url]
                return False, response_text, "spam"
            
            if 'rate' in response_text.lower() or 'limit' in response_text.lower():
                self.stats["rate_limits"] += 1
                if proxy_url in self.csrf_tokens:
                    del self.csrf_tokens[proxy_url]
                return False, response_text, "rate_limit"
            
            if 'challenge' in response_text.lower():
                self.stats["challenges"] += 1
                return False, response_text, "challenge"
            
            if 'dryrun_passed' in response_text or '"status":"ok"' in response_text:
                self.stats["available_found"] += 1
                return True, response_text, None
            
            self.stats["other_responses"] += 1
            return False, response_text, "other"
            
        except httpx.TimeoutException:
            self.stats["timeouts"] += 1
            return False, "", "timeout"
        except httpx.RequestError as e:
            self.stats["connection_errors"] += 1
            self.stats["last_error"] = str(e)[:200]
            return False, "", "connection_error"
        except Exception as e:
            self.stats["other_errors"] += 1
            self.stats["last_error"] = str(e)[:200]
            return False, "", "error"


class SearchSession:
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        
        self.found_username = None
        self.result_reason = "timeout" 
        
        self.should_stop = False
        self.max_concurrency = CONFIG["MAX_CONCURRENCY"]
        self.start_time = 0
        
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
            "stable_proxy_requests": 0,
            "proxies_from_firebase": 0,
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
            
            await asyncio.sleep(0.02)

    async def run(self):
        self.start_time = time.time()
        
        # Fetch proxies from Firebase
        proxy_addresses = await proxy_manager.fetch_proxies()
        
        if not proxy_addresses:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_in_database",
                "duration": 0,
                "stats": self.stats
            }
        
        # Get proxy stats
        proxy_stats = proxy_manager.get_stats()
        self.stats["proxies_from_firebase"] = proxy_stats["total_unique"]
        self.stats["stable_proxies_count"] = proxy_stats["stable_count"]
        self.stats["regular_proxies_count"] = proxy_stats["regular_count"]
        
        # Create clients for unique proxies
        unique_proxies = list(set(proxy_addresses))
        proxy_clients = []
        
        for proxy_addr in unique_proxies:
            try:
                # Format: IP:PORT -> http://IP:PORT
                proxy_url = f"http://{proxy_addr}"
                is_stable = proxy_addr in proxy_manager.stable_proxies
                
                client = httpx.AsyncClient(
                    proxy=proxy_url, 
                    timeout=8.0,
                    follow_redirects=True
                )
                proxy_clients.append((client, proxy_url, is_stable))
            except Exception:
                pass
        
        if not proxy_clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_working_proxies",
                "duration": 0,
                "stats": self.stats
            }

        checker = WebInstagramChecker(proxy_clients, self.stats)
        
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
    stats = proxy_manager.get_stats()
    return jsonify({
        "status": "online",
        "message": "Instagram Checker API - Firebase Proxies Edition",
        "usage": "Send GET request to /search to find a user.",
        "proxy_source": "Firebase Realtime Database",
        "proxies": {
            "stable": stats["stable_count"],
            "regular": stats["regular_count"],
            "total": stats["total_unique"],
        }
    })

@app.route('/search')
async def search():
    session = SearchSession()
    result = await session.run()
    return jsonify(result)

@app.route('/proxies')
async def get_proxies():
    """Endpoint to check current proxies from Firebase."""
    await proxy_manager.fetch_proxies()
    return jsonify({
        "stable_proxies": proxy_manager.stable_proxies,
        "regular_proxies": proxy_manager.proxies,
        "stats": proxy_manager.get_stats()
    })


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)