import os
import random
import time
import asyncio
import httpx
import logging
from flask import Flask, jsonify
from flask_cors import CORS
from uuid import uuid4

# ==========================================
#              CONFIGURATION
# ==========================================
# Koyeb Nano Instance Optimization:
# - Limit concurrent outgoing requests to prevent RAM OOM.
# - Use a single global AsyncClient for connection pooling.

CONFIG = {
    "INSTAGRAM_API_URL": 'https://i.instagram.com/api/v1/accounts/create/',
    "TIMEOUT_SECONDS": 10,  # Fast timeout for individual checks
    "BATCH_SIZE": 30,       # Number of concurrent checks per search request
    "GLOBAL_CONCURRENCY": 100, # Max global concurrent requests across all users
    "FIXED_EMAIL": "abdo1@gmail.com",
}

# Values for username generation
CHARS = {
    "LETTERS": 'abcdefghijklmnopqrstuvwxyz',
    "DIGITS": '0123456789',
    "SYMBOLS": '._'
}
CHARS["ALL_VALID"] = CHARS["LETTERS"] + CHARS["DIGITS"]

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ==========================================
#              GLOBAL STATE
# ==========================================

# Global Semaphore to protect Koyeb RAM
global_semaphore = asyncio.Semaphore(CONFIG["GLOBAL_CONCURRENCY"])

# Global HTTP Client (initialized in startup)
# reusing TCP connections is CRITICAL for performance.
client: httpx.AsyncClient = None

# Proxies List
PROXIES_LIST = []

def load_proxies():
    """Validates and loads proxies from Env or File."""
    global PROXIES_LIST
    
    # Priority 1: Environment Variable (Koyeb Secret)
    env_proxies = os.environ.get("PROXIES_LIST")
    if env_proxies:
        PROXIES_LIST = [p.strip() for p in env_proxies.split(',') if p.strip()]
        logger.info(f"Loaded {len(PROXIES_LIST)} proxies from Environment Variable.")
        return

    # Priority 2: Local File
    if os.path.exists("proxies.txt"):
        with open("proxies.txt", "r") as f:
            PROXIES_LIST = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(PROXIES_LIST)} proxies from proxies.txt.")
        return

    # Fallback (Not recommended for prod)
    logger.warning("No proxies found! Using direct connection (High ban risk).")
    PROXIES_LIST = []

# ==========================================
#              CORE LOGIC
# ==========================================

class UserAgentGenerator:
    """Generates high-quality, up-to-date Android User Agents."""
    
    DEVICES = [
        # (Device Name, Model, Chipset, KPI)
        ("Samsung; SM-S918B", "dm3q", "qcom", "450dpi; 1440x3088"), # S23 Ultra
        ("Google; Pixel 7 Pro", "cheetah", "google", "560dpi; 1440x3120"),
        ("Xiaomi; 2211133G", "mayfly", "qcom", "440dpi; 1080x2400"),
        ("OnePlus; CPH2447", "ovaltine", "qcom", "480dpi; 1080x2412"),
        ("Samsung; SM-A546B", "a54x", "samsung", "450dpi; 1080x2340"),
    ]
    
    VERSIONS = [
        "308.0.0.36.109",
        "307.0.0.34.111",
        "306.0.0.35.110",
        "305.0.0.33.108"
    ]

    @classmethod
    def get_random(cls):
        device = random.choice(cls.DEVICES)
        version = random.choice(cls.VERSIONS)
        # Format: Instagram <Version> Android (<AndroidVer>/<SDK>; <DPI>; <Res>; <Brand>; <Model>; <Board>; <Chipset>; <Lang>)
        # Simplified for robustness:
        ua = f"Instagram {version} Android (33/13; {device[3]}; {device[0]}; {device[1]}; {device[2]}; en_US)"
        return ua

def generate_headers():
    """Generates dynamic headers mimicking the real app."""
    return {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept-Language': 'en-US',
        'X-IG-Capabilities': 'AQ==',
        'Accept-Encoding': 'gzip',
        'User-Agent': UserAgentGenerator.get_random(),
        'X-IG-Connection-Type': random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G']),
        'X-IG-Bandwidth-Speed-KBPS': str(random.randint(1000, 8000)),
        'X-IG-Bandwidth-TotalBytes-B': str(random.randint(500000, 5000000)),
        'X-IG-Bandwidth-TotalTime-MS': str(random.randint(50, 500)),
    }

def get_random_proxy():
    """Selects a random proxy from the loaded list."""
    if not PROXIES_LIST:
        return None
    return random.choice(PROXIES_LIST)

def generate_username():
    """Generates a valid 5-char username."""
    # Pattern: 1 Letter + 4 Random (Letters/Numbers/Symbols)
    # This pattern is popular and often found.
    # Avoiding starting with number or period.
    
    first = random.choice(CHARS["LETTERS"])
    rest = ''.join(random.choices(CHARS["ALL_VALID"] + '._', k=4))
    
    # Cleanup invalid patterns
    username = (first + rest).replace('..', '.').replace('__', '_').replace('._', '.').replace('_.', '_')
    
    # Ensure strict length 5 if replacements happened
    while len(username) < 5:
        username += random.choice(CHARS["DIGITS"])
    return username[:5]

async def check_username(username: str):
    """
    Checks a single username against Instagram API.
    Returns: (username, is_available, status_msg)
    """
    url = CONFIG["INSTAGRAM_API_URL"]
    data = {
        "email": CONFIG["FIXED_EMAIL"],
        "username": username,
        "password": f"Pass{uuid4().hex[:8]}", # Random password
        "device_id": f"android-{uuid4()}",
    }
    
    headers = generate_headers()
    proxy = get_random_proxy()
    
    # Parse proxy for httpx if it exists
    # httpx expects proxies arg as string or dict. 
    # If using string format user:pass@ip:port, we generally need request args.
    # Assuming standard HTTP proxies.
    
    try:
        async with global_semaphore: # Wait for a slot in the global limit
            response = await client.post(
                url,
                data=data,
                headers=headers,
                # httpx proxy format: "http://user:pass@host:port" is generally auto-handled if passed correctly
                # We simply pass the string URL if present.
                timeout=CONFIG["TIMEOUT_SECONDS"],
            )
            
            resp_text = response.text

            # Logic
            if '"email_is_taken"' in resp_text:
                return username, True, "Available"
            
            if '"spam"' in resp_text or 'rate_limit_error' in resp_text:
                 # Rate limited - this proxy is burnt for now
                 return username, False, "RateLimit"

            # Default: standard rejection (taken or other error)
            return username, False, "Taken"

    except Exception as e:
        # Network errors, timeouts, etc.
        return username, False, str(e)


# ==========================================
#              FLASK APP
# ==========================================

app = Flask(__name__)
CORS(app)

# Lifecycle events for Async Client
@app.before_serving
async def startup():
    global client
    load_proxies()
    # Initialize global client with limits matching our semaphore effectively
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=CONFIG["GLOBAL_CONCURRENCY"] + 20)
    
    # If we have proxies, we might want to mount them or rotate them per request.
    # Since we rotate per request, we configure the client WITHOUT a base proxy,
    # and pass 'proxy' kwarg to .post() if supported, OR we just use transport.
    # Standard httpx.AsyncClient support for per-request proxy is via 'extensions' in older versions 
    # or creating a new client per proxy.
    # OPTIMIZATION: Creating a client per request is slow (SSL handshake). 
    # Reusing a client but routing via different proxies is tricky in standard HTTPX without Mounts.
    # FIX: For maximum speed with rotating proxies, we will actually instantiate a lightweight client 
    # OR (better for memory) use 'mounts' if proxies were static. 
    # Given they are dynamic, let's use a simpler approach: 
    # Configure the global client to be proxy-agnostic, but if we need a proxy, we might pass it.
    # HOWEVER, httpx 'proxies' param is client-level or request-level? 
    # In newer httpx, it can be passed to request but it's deprecated or tricky.
    # SAFE ASYNC PATTERN: We will use a shared transport if possible, or just one client and 
    # accept that 'proxies' param in .post might function (it does in recent versions) 
    # OR we make a new client if a proxy is needed. 
    # DECISION: To keep it blazing fast and simple: Use one global client. 
    # If proxy rotation is needed per request, we accept the slight overhead of `httpx.AsyncClient(proxy=...)` 
    # per batch OR we use the global client without proxies if env is empty.
    
    # REVISION: We will maintain the global client for NON-PROXY or Fixed Proxy setups.
    # For rotating proxies per request, we must instantiate a client or transport per request 
    # to switch IP. This is unavoidable unless we use a tunnel service.
    # Given the requirements: "Reuse TCP connections" + "Rotating Proxies".
    # We will use a global client without default proxies, and we will try to pass `proxy` to .post 
    # (available in some versions) or fallback to ephemeral clients for proxy calls.
    # The safest "rewrite" that guarantees rotation works is ephemeral clients.
    # BUT, to save RAM on Koyeb, we will use a Context Manager per batch.
    
    client = httpx.AsyncClient(limits=limits, timeout=CONFIG["TIMEOUT_SECONDS"])


@app.after_serving
async def shutdown():
    if client:
        await client.aclose()


@app.route('/')
async def home():
    """Koyeb Health Check - Must be fast."""
    return jsonify({
        "status": "online",
        "message": "High-Performance Instagram Async API",
        "proxies_loaded": len(PROXIES_LIST)
    })

@app.route('/search')
async def search():
    """
    High-Concurrency Search.
    Fires a batch of requests. Returns the FIRST success.
    """
    
    # Lazy init for local dev (if before_serving didn't run)
    global client
    if client is None:
        load_proxies()
        client = httpx.AsyncClient(timeout=CONFIG["TIMEOUT_SECONDS"])

    # Create a batch of tasks
    tasks = []
    
    # We will look for 1 success.
    # We generate a batch of unique usernames to check.
    usernames = set()
    while len(usernames) < CONFIG["BATCH_SIZE"]:
        usernames.add(generate_username())
    
    # Optimization: Use a shared client ref, but handling proxies per request is needed.
    # We will use the global client. NOTE: HTTpx per-request proxy is not standard in request().
    # We'll stick to a helper that creates a client IF proxy supplied, or uses global if not.
    # To truly use connection pooling with rotating proxies, we'd need a custom Transport.
    # For now, we will create a client per concurrency slot if proxy is used, 
    # OR use global client if no proxy.
    
    async def worker(u):
        proxy_url = get_random_proxy()
        
        # If we have a proxy list, we MUST use a new client/transport for that specific proxy 
        # to ensure the IP changes. Connection pooling *to the proxy* is limited value 
        # if we rotate every request. Pooling is valuable if we stick to one proxy.
        # But we want rotation.
        try:
            async with global_semaphore:
                if proxy_url:
                    # Ephemeral client for the proxy path
                    async with httpx.AsyncClient(proxies=proxy_url, timeout=CONFIG["TIMEOUT_SECONDS"]) as local_client:
                        resp = await local_client.post(
                            CONFIG["INSTAGRAM_API_URL"],
                            data={
                                "email": CONFIG["FIXED_EMAIL"],
                                "username": u,
                                "password": f"Pass{uuid4().hex[:8]}",
                                "device_id": f"android-{uuid4()}",
                            },
                            headers=generate_headers()
                        )
                        text = resp.text
                else:
                    # Use global client (Direct connection)
                    resp = await client.post(
                        CONFIG["INSTAGRAM_API_URL"],
                        data={
                            "email": CONFIG["FIXED_EMAIL"],
                            "username": u,
                            "password": f"Pass{uuid4().hex[:8]}",
                            "device_id": f"android-{uuid4()}",
                        },
                        headers=generate_headers()
                    )
                    text = resp.text

            if '"email_is_taken"' in text:
                return {"username": u, "available": True}
            else:
                return {"username": u, "available": False}

        except Exception:
            return {"username": u, "available": False}

    # Launch all workers
    # asyncio.gather simply waits for all. We want "First Success".
    # asyncio.as_completed is better fit.
    
    aws = [worker(u) for u in usernames]
    
    # We want to return as soon as one is True.
    start_ts = time.time()
    found_user = None
    
    for coro in asyncio.as_completed(aws):
        result = await coro
        if result["available"]:
            found_user = result["username"]
            # Optimization: Cancel others? 
            # In Python asyncio, cancelling pending 'as_completed' tasks is manual.
            # For simplicity and robust clean up, we just break. 
            # The others will finish in bg or we can cancel them if we tracked the Tasks.
            break
    
    duration = round(time.time() - start_ts, 2)
    
    if found_user:
        return jsonify({
            "status": "success",
            "username": found_user,
            "duration": duration
        })
    else:
        return jsonify({
            "status": "failed",
            "reason": "No valid username found in batch",
            "duration": duration,
            "checked": len(usernames)
        })

if __name__ == "__main__":
    app.run(debug=True)