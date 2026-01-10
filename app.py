#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - On-Demand API
==========================================

Uses Instagram Web API for reliable username checking.
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
    # Web API endpoint - more reliable
    "CHECK_USERNAME_URL": "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/",
    "TIMEOUT_SECONDS": 30,
    "MAX_CONCURRENCY": 30,
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

# Web User Agents (Chrome on Android)
WEB_USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


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
            
            # Extract csrf token from cookies
            cookies = response.cookies
            csrf = cookies.get('csrftoken', '')
            if csrf:
                return csrf
            
            # Try to extract from response
            text = response.text
            if 'csrf_token' in text:
                import re
                match = re.search(r'"csrf_token":"([^"]+)"', text)
                if match:
                    return match.group(1)
            
            # Generate a random one as fallback
            return hashlib.md5(str(uuid4()).encode()).hexdigest()[:32]
            
        except Exception:
            return hashlib.md5(str(uuid4()).encode()).hexdigest()[:32]
    
    async def check_username_availability(self, username: str):
        """Check if username is available using Web API."""
        client, proxy_url = random.choice(self.proxy_clients)
        
        try:
            # Get or reuse CSRF token
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
            
            if self.stats["total_requests"] <= 3:
                self.stats["sample_response"] = response_text[:500]
            
            # Check responses
            if 'username_is_taken' in response_text or '"username":' in response_text:
                self.stats["username_taken"] += 1
                return False, response_text, "taken"
            
            if '"errors"' in response_text and 'username' not in response_text.lower():
                # Error but not about username = username is available!
                self.stats["available_found"] += 1
                return True, response_text, None
            
            if 'email_is_taken' in response_text:
                # Email error means username was accepted
                self.stats["available_found"] += 1
                return True, response_text, None
            
            if '"spam"' in response_text or 'spam' in response_text.lower():
                self.stats["spam_errors"] += 1
                # Refresh CSRF token
                del self.csrf_tokens[proxy_url]
                return False, response_text, "spam"
            
            if 'rate' in response_text.lower() or 'limit' in response_text.lower():
                self.stats["rate_limits"] += 1
                del self.csrf_tokens[proxy_url]
                return False, response_text, "rate_limit"
            
            if 'challenge' in response_text.lower():
                self.stats["challenges"] += 1
                return False, response_text, "challenge"
            
            # Check for successful account creation attempt blocked only by email
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
        
        proxy_clients = []
        for proxy_url in PROXIES_LIST:
            try:
                client = httpx.AsyncClient(
                    proxy=proxy_url, 
                    timeout=8.0,
                    follow_redirects=True
                )
                proxy_clients.append((client, proxy_url))
            except Exception:
                pass
        
        if not proxy_clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
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
        
        for client, _ in proxy_clients:
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
        "message": "Instagram Checker API - Web Edition",
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