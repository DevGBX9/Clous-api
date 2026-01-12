#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instagram Username Checker - ULTIMATE STEALTH Edition
======================================================

Maximum stealth with all protection levels:
- Level 1: Simple usernames, random delays
- Level 2: Session persistence, human-like timing
- Level 3: Smart proxy rotation, enhanced fingerprints

Author: @GBX_9
"""

import os
import sys
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Set
from uuid import uuid4
from dataclasses import dataclass, field

import httpx
from flask import Flask, jsonify
from flask_cors import CORS

sys.dont_write_bytecode = True

# ==========================================
#              LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# ==========================================
#              CONFIG
# ==========================================
CONFIG = {
    "API_URL": 'https://i.instagram.com/api/v1/users/check_username/',
    "TIMEOUT": 60,  # Increased for slower, safer requests
    "REQUEST_TIMEOUT": 8.0,
    "PROXIES_FILE": "proxies.txt",
    
    # Stealth settings
    "MIN_DELAY": 0.8,       # Minimum delay between requests (seconds)
    "MAX_DELAY": 2.5,       # Maximum delay between requests (seconds)
    "MAX_CONCURRENT": 15,   # Maximum concurrent requests (reduced for stealth)
    "COOLDOWN_TIME": 30,    # Seconds to wait before reusing rate-limited proxy
    "TYPING_SIMULATION": True,  # Simulate human typing patterns
}

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789'
LETTERS = 'abcdefghijklmnopqrstuvwxyz'

# Extended Android devices database
DEVICES = [
    {"manufacturer": "Samsung", "model": "SM-G998B", "device": "p3s", "board": "exynos2100", "android": 13, "dpi": 640, "res": "1440x3200", "country": "US"},
    {"manufacturer": "Samsung", "model": "SM-S908B", "device": "b0q", "board": "exynos2200", "android": 14, "dpi": 600, "res": "1440x3088", "country": "GB"},
    {"manufacturer": "Samsung", "model": "SM-A536B", "device": "a53x", "board": "exynos1280", "android": 13, "dpi": 450, "res": "1080x2400", "country": "DE"},
    {"manufacturer": "Samsung", "model": "SM-A525F", "device": "a52q", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2340", "country": "FR"},
    {"manufacturer": "Google", "model": "Pixel 8 Pro", "device": "husky", "board": "google", "android": 14, "dpi": 560, "res": "1344x2992", "country": "US"},
    {"manufacturer": "Google", "model": "Pixel 7 Pro", "device": "cheetah", "board": "google", "android": 14, "dpi": 560, "res": "1440x3120", "country": "US"},
    {"manufacturer": "Google", "model": "Pixel 6a", "device": "bluejay", "board": "google", "android": 13, "dpi": 420, "res": "1080x2400", "country": "CA"},
    {"manufacturer": "OnePlus", "model": "CPH2451", "device": "OP5958L1", "board": "taro", "android": 14, "dpi": 560, "res": "1440x3216", "country": "IN"},
    {"manufacturer": "OnePlus", "model": "LE2123", "device": "lemonadep", "board": "lahaina", "android": 13, "dpi": 560, "res": "1440x3216", "country": "US"},
    {"manufacturer": "Xiaomi", "model": "2201116SG", "device": "ingres", "board": "mt6895", "android": 13, "dpi": 480, "res": "1220x2712", "country": "IN"},
    {"manufacturer": "Xiaomi", "model": "M2101K6G", "device": "sweet", "board": "qcom", "android": 12, "dpi": 440, "res": "1080x2400", "country": "RU"},
    {"manufacturer": "OPPO", "model": "CPH2449", "device": "OP5961L1", "board": "mt6895", "android": 13, "dpi": 480, "res": "1080x2400", "country": "ID"},
]

IG_VERSIONS = [
    "315.0.0.26.109", "314.0.0.24.110", "313.0.0.28.109", "312.0.0.32.118",
    "311.0.0.32.119", "310.0.0.28.117", "309.0.0.40.113", "308.0.0.38.108",
]

# ==========================================
#              LOAD PROXIES
# ==========================================
def load_proxies() -> List[str]:
    proxies = []
    path = Path(__file__).parent / CONFIG["PROXIES_FILE"]
    try:
        with open(path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        logger.info(f"Loaded {len(proxies)} proxies")
    except Exception as e:
        logger.error(f"Error loading proxies: {e}")
    return proxies

PROXIES = load_proxies()

# ==========================================
#              FLASK APP
# ==========================================
app = Flask(__name__)
CORS(app)

# ==========================================
#     PERSISTENT PROXY SESSION (Level 2)
# ==========================================
@dataclass
class ProxySession:
    """Persistent session for each proxy - simulates a real device."""
    proxy_url: str
    device: Dict[str, Any]
    ig_version: str
    device_id: str
    phone_id: str
    guid: str
    adid: str
    mid: str
    session_id: str
    last_request_time: float = 0
    request_count: int = 0
    is_rate_limited: bool = False
    rate_limit_until: float = 0
    
    def get_headers(self) -> Dict[str, str]:
        """Get consistent headers for this session."""
        user_agent = (
            f"Instagram {self.ig_version} Android "
            f"({self.device['android']}/{self.device['android']}.0; "
            f"{self.device['dpi']}dpi; {self.device['res']}; "
            f"{self.device['manufacturer']}; {self.device['model']}; "
            f"{self.device['device']}; {self.device['board']}; en_{self.device['country']})"
        )
        
        return {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Accept': '*/*',
            'Accept-Language': f"en-{self.device['country']},en;q=0.9",
            'Accept-Encoding': 'gzip, deflate, br',
            'User-Agent': user_agent,
            'X-IG-App-ID': '567067343352427',
            'X-IG-App-Locale': f"en_{self.device['country']}",
            'X-IG-Device-Locale': f"en_{self.device['country']}",
            'X-IG-Mapped-Locale': f"en_{self.device['country']}",
            'X-IG-Device-ID': self.guid,
            'X-IG-Family-Device-ID': self.phone_id,
            'X-IG-Android-ID': self.device_id,
            'X-IG-Timezone-Offset': str(random.choice([-18000, -14400, 0, 3600, 7200, 19800])),
            'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G']),
            'X-IG-Connection-Speed': f'{random.randint(1500, 4000)}kbps',
            'X-IG-Bandwidth-Speed-KBPS': str(random.randint(3000, 12000)),
            'X-IG-Bandwidth-TotalBytes-B': str(random.randint(2000000, 10000000)),
            'X-IG-Bandwidth-TotalTime-MS': str(random.randint(100, 400)),
            'X-IG-Capabilities': random.choice(['3brTvx0=', '3brTv58=', '3brTv50=']),
            'X-IG-WWW-Claim': '0',
            'X-Bloks-Version-Id': 'e538d4591f238824118bfcb9528c8d005f2ea3becd947a3973c030ac971bb88e',
            'X-Bloks-Is-Layout-RTL': 'false',
            'X-Bloks-Is-Panorama-Enabled': 'true',
            'X-Pigeon-Session-Id': self.session_id,
            'X-Pigeon-Rawclienttime': str(time.time()),
            'X-MID': self.mid,
            'X-FB-HTTP-Engine': 'Liger',
            'X-FB-Client-IP': 'True',
            'X-FB-Server-Cluster': 'True',
        }
    
    def can_make_request(self) -> bool:
        """Check if this proxy can make a request now."""
        if self.is_rate_limited:
            if time.time() > self.rate_limit_until:
                self.is_rate_limited = False
            else:
                return False
        return True
    
    def mark_rate_limited(self):
        """Mark this proxy as rate-limited."""
        self.is_rate_limited = True
        self.rate_limit_until = time.time() + CONFIG["COOLDOWN_TIME"]


class ProxySessionManager:
    """Manages persistent sessions for all proxies."""
    
    def __init__(self, proxies: List[str]):
        self.sessions: Dict[str, ProxySession] = {}
        self.clients: Dict[str, httpx.AsyncClient] = {}
        self._create_sessions(proxies)
    
    def _create_sessions(self, proxies: List[str]):
        """Create persistent sessions for each proxy."""
        for proxy in proxies:
            device = random.choice(DEVICES)
            self.sessions[proxy] = ProxySession(
                proxy_url=proxy,
                device=device,
                ig_version=random.choice(IG_VERSIONS),
                device_id=f"android-{uuid4().hex[:16]}",
                phone_id=str(uuid4()),
                guid=str(uuid4()),
                adid=str(uuid4()),
                mid=''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-', k=28)),
                session_id=f"UFS-{uuid4()}-0",
            )
        logger.info(f"Created {len(self.sessions)} persistent proxy sessions")
    
    def get_available_sessions(self) -> List[ProxySession]:
        """Get all sessions that are not rate-limited."""
        return [s for s in self.sessions.values() if s.can_make_request()]
    
    def get_rate_limited_count(self) -> int:
        """Get count of rate-limited proxies."""
        return sum(1 for s in self.sessions.values() if s.is_rate_limited)
    
    async def get_client(self, session: ProxySession) -> httpx.AsyncClient:
        """Get or create client for a session."""
        if session.proxy_url not in self.clients:
            self.clients[session.proxy_url] = httpx.AsyncClient(
                proxy=session.proxy_url,
                timeout=CONFIG["REQUEST_TIMEOUT"]
            )
        return self.clients[session.proxy_url]
    
    async def close_all(self):
        """Close all clients."""
        for client in self.clients.values():
            try:
                await client.aclose()
            except:
                pass
        self.clients.clear()


# ==========================================
#     HUMAN-LIKE TIMING (Level 2)
# ==========================================
async def human_delay():
    """Simulate human-like delay between actions."""
    # Variable delay with occasional longer pauses
    if random.random() < 0.1:  # 10% chance of longer pause
        delay = random.uniform(2.0, 4.0)
    else:
        delay = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
    
    await asyncio.sleep(delay)


async def simulate_typing_delay(username: str):
    """Simulate the delay of typing a username."""
    if CONFIG["TYPING_SIMULATION"]:
        # Average typing speed: 40-60 WPM = ~200-300ms per character
        typing_time = len(username) * random.uniform(0.05, 0.15)
        await asyncio.sleep(typing_time)


# ==========================================
#     USERNAME GENERATOR (Level 1 - Simple)
# ==========================================
def generate_simple_username() -> str:
    """Generate a simple 5-char username (NO symbols) - higher availability!"""
    return random.choice(LETTERS) + ''.join(random.choices(CHARS, k=4))


# ==========================================
#     CORE: CHECK USERNAME
# ==========================================
async def check_username(
    client: httpx.AsyncClient,
    session: ProxySession,
    username: str
) -> Dict[str, Any]:
    """Check a single username with full stealth."""
    try:
        # Simulate typing the username
        await simulate_typing_delay(username)
        
        data = {
            "username": username,
            "_uuid": session.guid,
        }
        
        response = await client.post(
            CONFIG["API_URL"],
            headers=session.get_headers(),
            data=data
        )
        
        session.request_count += 1
        session.last_request_time = time.time()
        
        text = response.text
        
        if '"available":true' in text or '"available": true' in text:
            return {"status": "available", "username": username}
        elif '"available":false' in text or '"available": false' in text:
            return {"status": "taken", "username": username}
        elif 'wait a few minutes' in text.lower() or 'rate_limit' in text.lower():
            session.mark_rate_limited()
            return {"status": "rate_limit", "username": username}
        elif 'challenge_required' in text.lower():
            session.mark_rate_limited()
            return {"status": "challenge", "username": username}
        else:
            return {"status": "error", "username": username, "response": text[:100]}
            
    except httpx.TimeoutException:
        return {"status": "timeout", "username": username}
    except Exception as e:
        return {"status": "error", "username": username, "error": str(e)[:50]}


# ==========================================
#     SMART SEARCH WITH ALL STEALTH LEVELS
# ==========================================
async def stealth_search() -> Dict[str, Any]:
    """
    Search with MAXIMUM STEALTH:
    - Level 1: Simple usernames, random delays
    - Level 2: Session persistence, human-like timing
    - Level 3: Smart proxy rotation, rate limit handling
    """
    start_time = time.time()
    stats = {"checked": 0, "taken": 0, "errors": 0}
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "duration": 0}
    
    # Create session manager (Level 2: Session Persistence)
    manager = ProxySessionManager(PROXIES)
    
    logger.info(f"🛡️ Starting STEALTH search with {len(PROXIES)} proxy sessions...")
    
    try:
        while time.time() - start_time < CONFIG["TIMEOUT"]:
            # Get available (non-rate-limited) sessions
            available_sessions = manager.get_available_sessions()
            
            if not available_sessions:
                logger.warning("All proxies rate-limited! Waiting for cooldown...")
                await asyncio.sleep(5)
                continue
            
            # Limit concurrent requests (Level 1)
            sessions_to_use = available_sessions[:CONFIG["MAX_CONCURRENT"]]
            
            # Generate usernames
            usernames = [generate_simple_username() for _ in range(len(sessions_to_use))]
            
            # Create tasks
            tasks = []
            for session, username in zip(sessions_to_use, usernames):
                client = await manager.get_client(session)
                tasks.append(asyncio.create_task(check_username(client, session, username)))
            
            # Process results as they come in
            for coro in asyncio.as_completed(tasks):
                result = await coro
                stats["checked"] += 1
                
                if result["status"] == "available":
                    # Found! Cancel remaining and return
                    for t in tasks:
                        t.cancel()
                    
                    duration = round(time.time() - start_time, 2)
                    rate_limited = manager.get_rate_limited_count()
                    
                    logger.info(f"✅ FOUND: {result['username']} in {duration}s")
                    
                    return {
                        "status": "success",
                        "username": result["username"],
                        "duration": duration,
                        "stats": stats,
                        "rate_limited_proxies": f"{rate_limited}/{len(PROXIES)}"
                    }
                    
                elif result["status"] == "taken":
                    stats["taken"] += 1
                elif result["status"] in ["rate_limit", "challenge"]:
                    pass  # Already handled in check_username
                else:
                    stats["errors"] += 1
            
            # Human-like delay between batches (Level 2)
            await human_delay()
        
        # Timeout
        rate_limited = manager.get_rate_limited_count()
        return {
            "status": "failed",
            "reason": "timeout",
            "duration": round(time.time() - start_time, 2),
            "stats": stats,
            "rate_limited_proxies": f"{rate_limited}/{len(PROXIES)}"
        }
        
    finally:
        await manager.close_all()


# ==========================================
#     DETAILED SEARCH (FOR DEBUGGING)
# ==========================================
async def detailed_stealth_search() -> Dict[str, Any]:
    """
    Same as stealth_search but with EXTREMELY DETAILED logging.
    Records every single step for debugging purposes.
    """
    start_time = time.time()
    
    # Detailed log for everything
    detailed_log = {
        "timeline": [],
        "sessions_created": [],
        "requests_made": [],
        "delays_applied": [],
        "rate_limits_detected": [],
        "usernames_checked": [],
        "responses_received": [],
    }
    
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0, "timeouts": 0}
    
    def log_event(event_type: str, data: Dict[str, Any]):
        """Log an event with timestamp."""
        elapsed = round(time.time() - start_time, 4)
        detailed_log["timeline"].append({
            "time": elapsed,
            "event": event_type,
            "data": data
        })
    
    if not PROXIES:
        return {"status": "failed", "reason": "no_proxies", "detailed_log": detailed_log}
    
    log_event("INIT", {"proxies_count": len(PROXIES), "config": CONFIG})
    
    # Create session manager
    manager = ProxySessionManager(PROXIES)
    
    # Log all created sessions
    for proxy_url, session in manager.sessions.items():
        session_info = {
            "proxy": proxy_url[:50] + "...",
            "device": session.device["model"],
            "ig_version": session.ig_version,
            "device_id": session.device_id,
            "guid": session.guid[:8] + "...",
        }
        detailed_log["sessions_created"].append(session_info)
    
    log_event("SESSIONS_CREATED", {"count": len(manager.sessions)})
    
    batch_number = 0
    
    try:
        while time.time() - start_time < CONFIG["TIMEOUT"]:
            batch_number += 1
            batch_start = time.time()
            
            # Get available sessions
            available_sessions = manager.get_available_sessions()
            rate_limited_count = manager.get_rate_limited_count()
            
            log_event("BATCH_START", {
                "batch": batch_number,
                "available_proxies": len(available_sessions),
                "rate_limited_proxies": rate_limited_count,
            })
            
            if not available_sessions:
                log_event("ALL_RATE_LIMITED", {"waiting": 5})
                await asyncio.sleep(5)
                continue
            
            # Limit concurrent
            sessions_to_use = available_sessions[:CONFIG["MAX_CONCURRENT"]]
            
            # Generate usernames
            usernames = [generate_simple_username() for _ in range(len(sessions_to_use))]
            
            log_event("USERNAMES_GENERATED", {
                "count": len(usernames),
                "samples": usernames[:5],
            })
            
            # Create and track tasks
            tasks = []
            task_details = []
            
            for i, (session, username) in enumerate(zip(sessions_to_use, usernames)):
                client = await manager.get_client(session)
                
                # Log request details
                request_info = {
                    "index": i,
                    "username": username,
                    "proxy": session.proxy_url[:40] + "...",
                    "device": session.device["model"],
                    "headers_sample": {
                        "User-Agent": session.get_headers()["User-Agent"][:60] + "...",
                        "X-IG-Device-ID": session.get_headers()["X-IG-Device-ID"][:20] + "...",
                    }
                }
                task_details.append(request_info)
                detailed_log["requests_made"].append(request_info)
                
                tasks.append(asyncio.create_task(check_username(client, session, username)))
            
            log_event("REQUESTS_SENT", {"count": len(tasks)})
            
            # Process results
            for coro in asyncio.as_completed(tasks):
                result = await coro
                stats["checked"] += 1
                
                response_info = {
                    "username": result.get("username"),
                    "status": result["status"],
                    "response_preview": result.get("response", result.get("error", ""))[:100] if result.get("response") or result.get("error") else None,
                }
                detailed_log["responses_received"].append(response_info)
                detailed_log["usernames_checked"].append(result.get("username"))
                
                if result["status"] == "available":
                    for t in tasks:
                        t.cancel()
                    
                    duration = round(time.time() - start_time, 4)
                    
                    log_event("FOUND_AVAILABLE", {
                        "username": result["username"],
                        "total_checked": stats["checked"],
                        "duration": duration,
                    })
                    
                    return {
                        "status": "success",
                        "username": result["username"],
                        "duration": duration,
                        "stats": stats,
                        "rate_limited_proxies": f"{manager.get_rate_limited_count()}/{len(PROXIES)}",
                        "batches_processed": batch_number,
                        "detailed_log": detailed_log,
                    }
                    
                elif result["status"] == "taken":
                    stats["taken"] += 1
                elif result["status"] == "rate_limit":
                    stats["rate_limits"] += 1
                    detailed_log["rate_limits_detected"].append(result.get("username"))
                elif result["status"] == "timeout":
                    stats["timeouts"] += 1
                else:
                    stats["errors"] += 1
            
            # Apply human delay
            delay_start = time.time()
            if random.random() < 0.1:
                delay = random.uniform(2.0, 4.0)
            else:
                delay = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
            
            await asyncio.sleep(delay)
            
            delay_info = {
                "batch": batch_number,
                "delay_seconds": round(delay, 3),
                "batch_duration": round(time.time() - batch_start, 3),
            }
            detailed_log["delays_applied"].append(delay_info)
            
            log_event("BATCH_END", delay_info)
        
        # Timeout
        return {
            "status": "failed",
            "reason": "timeout",
            "duration": round(time.time() - start_time, 2),
            "stats": stats,
            "rate_limited_proxies": f"{manager.get_rate_limited_count()}/{len(PROXIES)}",
            "batches_processed": batch_number,
            "detailed_log": detailed_log,
        }
        
    finally:
        log_event("CLEANUP", {"closing_clients": len(manager.clients)})
        await manager.close_all()


# ==========================================
#              API ROUTES
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "message": "Instagram Username Checker - ULTIMATE STEALTH Edition",
        "endpoints": {
            "/search": "Quick search - returns username only",
            "/infosearch": "Detailed search - returns EVERYTHING"
        },
        "features": [
            "Simple usernames (high availability)",
            "Session persistence per proxy",
            "Human-like timing patterns",
            "Smart proxy rotation",
            "Rate limit handling with cooldown"
        ],
        "proxies": len(PROXIES),
        "stealth_level": "MAXIMUM"
    })

@app.route('/search')
async def search():
    """Find one available username with maximum stealth."""
    result = await stealth_search()
    return jsonify(result)

@app.route('/infosearch')
async def info_search():
    """Find one available username with EXTREMELY DETAILED logging."""
    result = await detailed_stealth_search()
    return jsonify(result)

# ==========================================
#              MAIN
# ==========================================
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Starting ULTIMATE STEALTH server on port {port}")
    logger.info(f"🛡️ Stealth features: Session persistence, Human timing, Smart rotation")
    app.run(host='0.0.0.0', port=port)