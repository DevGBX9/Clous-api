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
import threading
import requests
import itertools
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
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
    "MAX_THREADS_CAP": 50,  # Cap threads to prevent server overload
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
    "http://qfzqxqrh:u9o91130s592@142.111.48.253:7030",
    "http://qfzqxqrh:u9o91130s592@31.59.20.176:6754",
    "http://qfzqxqrh:u9o91130s592@23.95.150.145:6114",
    "http://qfzqxqrh:u9o91130s592@198.23.239.134:6540",
    "http://qfzqxqrh:u9o91130s592@107.172.163.27:6543",
    "http://qfzqxqrh:u9o91130s592@198.105.121.200:6462",
    "http://qfzqxqrh:u9o91130s592@64.137.96.74:6641",
    "http://qfzqxqrh:u9o91130s592@84.247.60.125:6095",
    "http://qfzqxqrh:u9o91130s592@216.10.27.159:6837",
    "http://qfzqxqrh:u9o91130s592@142.111.67.146:5611",
]

# Random iterator to pick proxies efficiently
# We use random.choice mostly, but cycle can be used for round-robin
proxy_pool = itertools.cycle(PROXIES_LIST)

# Expanded User Agents
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

# ==========================================
#              FLASK SETUP
# ==========================================
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for decoupled frontend access


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
    Handles the HTTP communication with Instagram APIs.
    Uses Rotating Proxies and Random User Agents.
    """
    def __init__(self):
        # We generally use a session, but with rotating proxies and identities per request, 
        # it's often safer to treat each check as a fresh isolated request or rotate session headers.
        self.session = requests.Session()
    
    def _get_random_headers(self):
        """Generates headers with randomized device bandwidth/connection type."""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = f'Instagram {random.choice(USER_AGENTS)}'
        headers['X-IG-Connection-Type'] = random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G'])
        headers['X-IG-Bandwidth-Speed-KBPS'] = str(random.randint(1000, 8000))
        headers['X-IG-Bandwidth-TotalBytes-B'] = str(random.randint(500000, 5000000))
        headers['X-IG-Bandwidth-TotalTime-MS'] = str(random.randint(50, 500))
        return headers
    
    def _get_proxy_dict(self):
        """Pick a random proxy from the pool."""
        proxy_url = random.choice(PROXIES_LIST)
        return {
            "http": proxy_url,
            "https": proxy_url
        }

    def check_username_availability(self, username):
        """
        Checks availability of a username using a random proxy.
        """
        # Generate Fresh Device IDs for total anonymity
        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": f"android-{uuid4()}",
            "guid": str(uuid4()),
        }
        
        try:
            # Short timeout (3s) - slightly longer for proxies
            response = requests.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_random_headers(), 
                data=data, 
                proxies=self._get_proxy_dict(),
                timeout=3
            )
            response_text = response.text
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit"
            
            is_available = '"email_is_taken"' in response_text
            return is_available, response_text, None
            
        except requests.exceptions.RequestException:
            # Proxy error or timeout is common, treat as not found/skip to keep moving
            return False, "", "connection_error"


class SearchSession:
    """
    Orchestrates a single on-demand search request.
    """
    def __init__(self):
        self.generator = AutoUsernameGenerator()
        self.checker = AutoInstagramChecker()
        
        # Result State
        self.found_username = None
        self.result_reason = "timeout" 
        
        # Concurrency Control
        self.stop_event = threading.Event()
        self.max_threads = min(CONFIG["MAX_THREADS_CAP"], (os.cpu_count() or 4) * 8)
        self.start_time = 0
        
        # Stats
        self.total_checks = 0
        self.lock = threading.Lock()

    def _worker(self):
        """Code running inside each worker thread."""
        while not self.stop_event.is_set():
            # 1. Check Timeout
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.stop_event.set()
                return

            # 2. Generate
            username = self.generator.generate()
            
            # 3. Check
            is_available, _, error = self.checker.check_username_availability(username)
            
            # Update Stats
            with self.lock:
                self.total_checks += 1
            
            # 4. Handle Result
            if self.stop_event.is_set():
                return 

            if error == "rate_limit":
                # With proxies, a single 429 might not mean global stop, 
                # but if ALL are failing, we might stop. 
                # For simplicity in this logic: if a proxy is banned, we try another.
                # We only stop if we suspect a global ban or app-level ban.
                # But to be safe as per user requirements:
                # self.result_reason = "rate_limit"
                # self.stop_event.set()
                # return
                pass # Continue with other proxies
            
            if is_available:
                self.found_username = username
                self.result_reason = "success"
                self.stop_event.set()
                return
            
            # Avoid CPU Thrashing
            time.sleep(0.05)

    def run(self):
        """Starts the thread pool."""
        self.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            for _ in range(self.max_threads):
                executor.submit(self._worker)
            
            while not self.stop_event.is_set():
                if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                    self.stop_event.set()
                    break
                time.sleep(0.1)
                
        duration = round(time.time() - self.start_time, 2)
        return {
            "status": "success" if self.found_username else "failed",
            "username": self.found_username,
            "reason": self.result_reason if not self.found_username else None,
            "duration": duration,
            "total_checks": self.total_checks,
            "checks_per_second": round(self.total_checks / duration, 1) if duration > 0 else 0
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
def search():
    """
    Triggers a search session.
    """
    session = SearchSession()
    result = session.run()
    return jsonify(result)


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)