# ==========================================
#     UNIFIED SEARCH SYSTEM (REFACTORED)
# ==========================================
"""
This module contains the refactored unified search function.
It replaces the 4 duplicate search functions:
- stealth_search()
- semi_quad_stealth_search()
- detailed_stealth_search()
- detailed_semi_quad_stealth_search()

All are now handled by a single unified_search() function with parameters.
"""

from enum import Enum
from typing import Dict, Any
import asyncio
import time
import random
import logging

logger = logging.getLogger(__name__)


class SearchMode(Enum):
    """Search modes for the unified search function."""
    SIMPLE = "simple"           # 5-char usernames, normal speed with delays
    SEMI_QUAD = "semi_quad"     # 5-char with _ or ., fast mode no delays


async def unified_search(
    mode: SearchMode,
    detailed_logging: bool,
    # Dependencies (injected from app.py)
    proxies: list,
    config: dict,
    session_manager_class,
    username_generator_simple,
    username_generator_semi_quad,
    check_username_func,
    is_proxy_available_func,
    get_rate_limited_count_func,
    get_warm_count_func,
) -> Dict[str, Any]:
    """
    UNIFIED Search Function - Replaces all 4 previous search functions.
    
    Args:
        mode: SearchMode.SIMPLE (5-char) or SearchMode.SEMI_QUAD (with _ or .)
        detailed_logging: If True, includes extensive debug information
        + dependency injection parameters
    
    Returns:
        Search result dict with status, username (if found), stats, etc.
    """
    start_time = time.time()
    
    # Mode-specific configuration
    if mode == SearchMode.SEMI_QUAD:
        username_generator = username_generator_semi_quad
        max_concurrent = 50          # More aggressive for semi-quad
        timeout = 30                 # Shorter timeout
        apply_delays = False         # No delays for speed
        search_type = "semi-quad"
    else:  # SIMPLE mode
        username_generator = username_generator_simple
        max_concurrent = config["MAX_CONCURRENT"]
        timeout = config["TIMEOUT"]
        apply_delays = True          # Human-like delays
        search_type = "simple"
    
    # Initialize stats
    stats = {"checked": 0, "taken": 0, "errors": 0, "rate_limits": 0}
    if detailed_logging:
        stats["timeouts"] = 0
    
    # Detailed logging structure (only if enabled)
    detailed_log = None
    if detailed_logging:
        detailed_log = {
            "timeline": [],
            "identities_created": [],
            "requests_made": [],
            "delays_applied": [],
            "rate_limits_detected": [],
            "usernames_checked": [],
            "responses_received": [],
        }
        
        def log_event(event_type: str, data: Dict[str, Any]):
            elapsed = round(time.time() - start_time, 4)
            detailed_log["timeline"].append({
                "time": elapsed,
                "event": event_type,
                "data": data
            })
    else:
        def log_event(event_type: str, data: Dict[str, Any]):
            pass  # No-op when detailed logging is disabled
    
    # Check proxies
    if not proxies:
        result = {"status": "failed", "reason": "no_proxies", "duration": 0}
        if detailed_logging:
            result["detailed_log"] = detailed_log
        return result
    
    log_event("INIT", {
        "proxies_count": len(proxies),
        "warm_sessions": get_warm_count_func(),
        "search_type": search_type,
        "mode": mode.value,
        "detailed_logging": detailed_logging
    })
    
    # Create FRESH session manager with NEW identities
    manager = session_manager_class(proxies)
    available_proxies = manager.get_available_proxies()
    
    if not available_proxies:
        result = {
            "status": "failed",
            "reason": "all_proxies_rate_limited",
            "duration": 0,
            "rate_limited_proxies": f"{get_rate_limited_count_func()}/{len(proxies)}"
        }
        if detailed_logging:
            result["detailed_log"] = detailed_log
        return result
    
    # Log identities (only for detailed mode)
    if detailed_logging:
        for proxy_with_id in available_proxies:
            identity1 = proxy_with_id.identity1
            identity2 = proxy_with_id.identity2
            identity_info = {
                "proxy": proxy_with_id.proxy_url[:50] + "...",
                "identity1": {
                    "device": identity1["device"]["model"],
                    "device_id": identity1["device_id"],
                    "guid": identity1["guid"][:12] + "...",
                },
                "identity2": {
                    "device": identity2["device"]["model"],
                    "device_id": identity2["device_id"],
                    "guid": identity2["guid"][:12] + "...",
                },
            }
            detailed_log["identities_created"].append(identity_info)
        
        log_event("IDENTITIES_CREATED", {
            "count": len(available_proxies),
            "total_identities": len(available_proxies) * 2,
        })
    
    logger.info(f"🔍 Starting {search_type.upper()} search with {len(available_proxies)} proxies")
    
    batch_number = 0
    
    while time.time() - start_time < timeout:
        batch_number += 1
        batch_start = time.time()
        
        # Get currently available proxies
        current_available = [p for p in available_proxies if is_proxy_available_func(p.proxy_url)]
        
        log_event("BATCH_START", {
            "batch": batch_number,
            "available_proxies": len(current_available),
            "rate_limited_proxies": get_rate_limited_count_func(),
        })
        
        if not current_available:
            wait_time = 2 if mode == SearchMode.SEMI_QUAD else 5
            log_event("ALL_RATE_LIMITED", {"waiting": wait_time})
            logger.warning("No available proxies! Waiting...")
            await asyncio.sleep(wait_time)
            continue
        
        # Limit concurrent requests
        proxies_to_use = current_available[:max_concurrent]
        
        # Generate usernames
        usernames = [username_generator() for _ in range(len(proxies_to_use))]
        
        log_event("USERNAMES_GENERATED", {
            "count": len(usernames),
            "samples": usernames[:5],
            "type": search_type
        })
        
        # Create tasks
        tasks = []
        for i, (proxy_with_id, username) in enumerate(zip(proxies_to_use, usernames)):
            client = await manager.get_client(proxy_with_id.proxy_url)
            
            # Log request details (only for detailed mode)
            if detailed_logging:
                identity = proxy_with_id.get_current_identity()
                request_info = {
                    "index": i,
                    "username": username,
                    "proxy": proxy_with_id.proxy_url[:40] + "...",
                    "device": identity["device"]["model"],
                    "identity_num": proxy_with_id.current_identity + 1,
                    "headers_sample": {
                        "User-Agent": identity["headers"]["User-Agent"][:60] + "...",
                        "X-IG-Device-ID": identity["headers"]["X-IG-Device-ID"][:20] + "...",
                    }
                }
                detailed_log["requests_made"].append(request_info)
            
            tasks.append(asyncio.create_task(check_username_func(client, proxy_with_id, username)))
        
        log_event("REQUESTS_SENT", {"count": len(tasks)})
        
        # Process results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            stats["checked"] += 1
            
            if detailed_logging:
                response_info = {
                    "username": result.get("username"),
                    "status": result["status"],
                    "response_preview": (result.get("response", result.get("error", ""))[:100] 
                                         if result.get("response") or result.get("error") else None),
                }
                detailed_log["responses_received"].append(response_info)
                detailed_log["usernames_checked"].append(result.get("username"))
            
            if result["status"] == "available":
                # Found! Cancel remaining tasks
                for t in tasks:
                    t.cancel()
                
                duration = round(time.time() - start_time, 2 if not detailed_logging else 4)
                
                log_event("FOUND_AVAILABLE", {
                    "username": result["username"],
                    "total_checked": stats["checked"],
                    "duration": duration,
                    "type": search_type
                })
                
                logger.info(f"✅ FOUND {search_type.upper()}: {result['username']} in {duration}s")
                
                # Cleanup
                log_event("CLEANUP", {"closing_clients": len(manager.clients)})
                asyncio.create_task(manager.close_all())
                
                response = {
                    "status": "success",
                    "username": result["username"],
                    "duration": duration,
                    "stats": stats,
                    "rate_limited_proxies": f"{get_rate_limited_count_func()}/{len(proxies)}",
                    "warm_sessions": f"{get_warm_count_func()}/{len(proxies)}"
                }
                
                if mode == SearchMode.SEMI_QUAD:
                    response["type"] = "semi-quad"
                
                if detailed_logging:
                    response["batches_processed"] = batch_number
                    response["detailed_log"] = detailed_log
                
                return response
            
            elif result["status"] == "taken":
                stats["taken"] += 1
            elif result["status"] in ["rate_limit", "challenge"]:
                stats["rate_limits"] += 1
                if detailed_logging:
                    detailed_log["rate_limits_detected"].append(result.get("username"))
            elif result["status"] == "timeout":
                if detailed_logging:
                    stats["timeouts"] += 1
                else:
                    stats["errors"] += 1
            else:
                stats["errors"] += 1
        
        # Apply delays (only in SIMPLE mode)
        if apply_delays:
            if random.random() < 0.1:
                delay = random.uniform(2.0, 4.0)
            else:
                delay = random.uniform(config["MIN_DELAY"], config["MAX_DELAY"])
            
            await asyncio.sleep(delay)
            
            if detailed_logging:
                delay_info = {
                    "batch": batch_number,
                    "delay_seconds": round(delay, 3),
                    "batch_duration": round(time.time() - batch_start, 3),
                }
                detailed_log["delays_applied"].append(delay_info)
                log_event("BATCH_END", delay_info)
    
    # Timeout - cleanup
    log_event("CLEANUP", {"closing_clients": len(manager.clients)})
    asyncio.create_task(manager.close_all())
    
    response = {
        "status": "failed",
        "reason": "timeout",
        "duration": round(time.time() - start_time, 2),
        "stats": stats,
        "rate_limited_proxies": f"{get_rate_limited_count_func()}/{len(proxies)}",
        "warm_sessions": f"{get_warm_count_func()}/{len(proxies)}"
    }
    
    if mode == SearchMode.SEMI_QUAD:
        response["type"] = "semi-quad"
    
    if detailed_logging:
        response["batches_processed"] = batch_number
        response["detailed_log"] = detailed_log
    
    return response
