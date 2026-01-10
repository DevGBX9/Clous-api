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
- Semi-Quad Only: Generates usernames with at least one underscore or dot.

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
    "MAX_CONCURRENCY": 50,  # Increased for async
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

# Expanded User Agents
# Massive List of 100+ Legacy User Agents (Versions that work without signing)
USER_AGENTS = [
    # Series 100.x - 120.x
    'Instagram 100.0.0.17.129 Android (28/9.0; 480dpi; 1080x2240; Xiaomi; MI 8; dipper; qcom; en_US)',
    'Instagram 100.0.0.17.129 Android (28/9.0; 420dpi; 1080x2160; Sony; G8341; G8341; qcom; en_US)',
    'Instagram 100.0.0.17.129 Android (27/8.1; 320dpi; 720x1280; Samsung; SM-J530F; j5y17lte; exynos7870; en_US)',
    'Instagram 101.0.0.15.120 Android (26/8.0; 480dpi; 1080x1920; Samsung; SM-G935F; hero2lte; samsung; en_US)',
    'Instagram 102.0.0.20.121 Android (29/10; 420dpi; 1080x2340; Huawei; LYA-L29; LYA; hisilicon; en_US)',
    'Instagram 103.1.0.15.119 Android (28/9; 320dpi; 720x1520; Vivo; 1820; 1820; mt6762; en_US)',
    'Instagram 104.0.0.21.118 Android (25/7.1.2; 240dpi; 480x854; Motorola; XT1750; convoy; mt6580; en_US)',
    'Instagram 105.0.0.18.119 Android (27/8.1.0; 480dpi; 1080x2160; HTC; U12+; htc_ime; qcom; en_US)',
    'Instagram 106.0.0.26.121 Android (28/9.0; 640dpi; 1440x2560; Google; Pixel XL; marlin; qcom; en_US)',
    'Instagram 107.0.0.27.121 Android (28/9.0; 480dpi; 1080x2160; OnePlus; ONEPLUS A6003; OnePlus6; qcom; en_US)',
    
    # Series 80.x - 99.x
    'Instagram 80.0.0.21.109 Android (25/7.1.1; 320dpi; 720x1280; Oppo; A71; A71; mt6750; en_US)',
    'Instagram 83.0.0.20.106 Android (27/8.1; 480dpi; 1080x2280; Huawei; ANE-LX1; HWANE; hisilicon; en_GB)',
    'Instagram 85.0.0.21.100 Android (24/7.0; 320dpi; 720x1280; Samsung; SM-G570F; on5xelte; samsung; en_US)',
    'Instagram 90.0.0.22.115 Android (26/8.0.0; 480dpi; 1080x1920; LG; LG-H870; lucye; qcom; en_US)',
    'Instagram 92.0.0.11.114 Android (23/6.0.1; 320dpi; 720x1280; Xiaomi; Redmi 4X; santoni; qcom; en_US)',
    'Instagram 95.0.0.31.121 Android (28/9.0; 560dpi; 1440x2880; LG; LM-V405; judypn; qcom; en_US)',
    'Instagram 97.0.0.32.119 Android (28/9.0; 420dpi; 1080x2248; Xiaomi; MI 8 Explorer Edition; ursa; qcom; en_US)',
    'Instagram 98.0.0.20.120 Android (27/8.1; 320dpi; 1080x2160; Oppo; CPH1819; CPH1819; mt6771; en_US)',
    'Instagram 99.0.0.29.123 Android (29/10; 480dpi; 1080x2400; Samsung; SM-A515F; a51; samsung; en_US)',

    # Series 10.x - 70.x (Very Reliable)
    'Instagram 10.20.0 Android (23/6.0.1; 640dpi; 1440x2560; Samsung; SM-G935F; hero2lte; samsung; en_US)',
    'Instagram 10.26.0 Android (19/4.4.2; 320dpi; 720x1280; Samsung; SM-G7102; ms013g; qcom; en_US)',
    'Instagram 10.3.2 Android (18/4.3; 320dpi; 720x1280; Sony; C1905; C1905; qcom; en_US)',
    'Instagram 12.0.0.7.64 Android (24/7.0; 640dpi; 1440x2560; Samsung; SM-G920F; zeroflte; samsung; en_US)',
    'Instagram 19.0.0.27.91 Android (22/5.1.1; 320dpi; 720x1280; Oppo; A33f; A33f; qcom; en_US)',
    'Instagram 27.0.0.11.97 Android (23/6.0.1; 480dpi; 1080x1920; OnePlus; ONE A2003; OnePlus2; qcom; en_US)',
    'Instagram 30.0.0.11.96 Android (25/7.1.1; 480dpi; 1080x1920; Lenovo; Lenovo P2a42; P2a42; qcom; en_US)',
    'Instagram 35.0.0.20.96 Android (24/7.0; 480dpi; 1080x1920; Huawei; EVA-L09; HWEVA; hisilicon; en_US)',
    'Instagram 40.0.0.10.95 Android (26/8.0.0; 320dpi; 720x1440; Xiaomi; Redmi 5; rosy; qcom; en_US)',
    'Instagram 50.1.0.35.118 Android (25/7.1.2; 320dpi; 720x1280; Vivo; 1606; 1606; qcom; en_US)',
    'Instagram 60.0.0.25.115 Android (28/9.0; 480dpi; 1080x2160; Nokia; Nokia 7 plus; B2N_sprout; qcom; en_US)',
    'Instagram 70.0.0.22.98 Android (27/8.1.0; 400dpi; 1080x2160; Xiaomi; Redmi Note 5; whyred; qcom; en_US)',

    # Series 121.x - 199.x (Mid-range validity)
    'Instagram 121.0.0.29.119 Android (28/9; 440dpi; 1080x2280; Huawei; MAR-LX1A; HWMAR; hisilicon; en_US)',
    'Instagram 123.0.0.21.114 Android (28/9; 320dpi; 720x1520; Samsung; SM-A105F; a10; samsung; en_US)',
    'Instagram 125.0.0.16.126 Android (29/10; 560dpi; 1440x3120; OnePlus; GM1913; OnePlus7Pro; qcom; en_US)',
    'Instagram 128.0.0.26.128 Android (28/9; 480dpi; 1080x2340; Xiaomi; Redmi Note 7; lavender; qcom; en_US)',
    'Instagram 130.0.0.31.121 Android (29/10; 420dpi; 1080x2400; Samsung; SM-A515F; a51; samsung; en_US)',
    'Instagram 135.0.0.28.119 Android (29/10; 450dpi; 1080x2400; Oppo; CPH1907; CPH1907; qcom; en_US)',
    'Instagram 140.0.0.27.123 Android (29/10; 403dpi; 1080x2160; Google; Pixel 3; blueline; qcom; en_US)',
    'Instagram 150.0.0.33.120 Android (30/11; 420dpi; 1080x2400; Samsung; SM-S901B; r0q; samsung; en_US)',
    'Instagram 160.1.0.25.120 Android (30/11; 480dpi; 1080x2400; Xiaomi; M2007J20CG; surya; qcom; en_US)',
    'Instagram 170.2.0.30.122 Android (31/12; 560dpi; 1440x3200; Samsung; SM-G998B; p3s; samsung; en_US)',
    'Instagram 180.0.0.34.123 Android (31/12; 420dpi; 1080x2400; Realme; RMX3031; RMX3031; mt6891; en_US)',
    'Instagram 190.0.0.25.121 Android (32/12.1; 480dpi; 1080x2400; Google; Pixel 6; oriole; google; en_US)',
    'Instagram 199.1.0.34.119 Android (31/12; 440dpi; 1080x2400; Vivo; V2101; V2101; mt6853; en_US)',

    # Tablet & Unusual Resolutions
    'Instagram 110.0.0.16.119 Android (28/9; 320dpi; 1200x1920; Samsung; SM-T510; gta3xlwifi; samsung; en_US)',
    'Instagram 115.0.0.25.120 Android (27/8.1; 240dpi; 800x1280; Amazon; KFDOWI; KFDOWI; mt8163; en_US)',
    'Instagram 120.0.0.18.118 Android (25/7.1; 213dpi; 800x1280; Asus; P027; P027; qcom; en_US)',
    'Instagram 96.0.0.31.120 Android (24/7.0; 320dpi; 1600x2560; Huawei; BTV-DL09; HWBTV; hisilicon; en_US)',
    'Instagram 75.0.0.23.99 Android (22/5.1; 240dpi; 1024x600; Lenovo; Lenovo TB3-710F; TB3-710F; mt8127; en_US)',

    # Re-adding some reliable legacy ones for weight
    'Instagram 6.12.1 Android (19/4.4.2; 480dpi; 1080x1920; Samsung; SM-G900F; klte; qcom; en_US)',
    'Instagram 8.0.0 Android (21/5.0; 320dpi; 720x1280; Motorola; MotoG3; osprey; qcom; en_US)',
    'Instagram 9.1.5 Android (22/5.1; 320dpi; 720x1280; Oppo; A37f; A37f; qcom; en_US)',
    'Instagram 10.0.0 Android (23/6.0; 480dpi; 1080x1920; Xiaomi; MI 4LTE; cancro; qcom; en_US)',
    'Instagram 11.0.0 Android (24/7.0; 640dpi; 1440x2560; LG; LG-G6; lucye; qcom; en_US)',
    'Instagram 13.0.0 Android (25/7.1; 320dpi; 720x1280; Samsung; SM-J700F; j7elte; samsung; en_US)',
    'Instagram 14.0.0 Android (26/8.0; 420dpi; 1080x2160; Sony; G8441; G8441; qcom; en_US)',
    'Instagram 15.0.0 Android (26/8.0; 480dpi; 1080x1920; Huawei; WAS-LX1; HWWAS-H; hisilicon; en_US)',
    'Instagram 16.0.0 Android (27/8.1; 480dpi; 1080x2280; OnePlus; ONEPLUS A6000; OnePlus6; qcom; en_US)',
    'Instagram 17.0.0 Android (27/8.1; 440dpi; 1080x2160; Xiaomi; Redmi Note 5; whyred; qcom; en_US)',
    'Instagram 18.0.0 Android (28/9; 560dpi; 1440x2960; Samsung; SM-G950F; dreamlte; samsung; en_US)',
    'Instagram 20.0.0 Android (28/9; 420dpi; 1080x2248; Xiaomi; MI 8; dipper; qcom; en_US)',
    'Instagram 21.0.0 Android (29/10; 403dpi; 1080x2160; Google; Pixel 2 XL; taimen; qcom; en_US)',
    'Instagram 22.0.0 Android (23/6.0; 480dpi; 1080x1920; HTC; HTC One M9; htc_himauhl; qcom; en_US)',
    'Instagram 23.0.0 Android (22/5.1; 240dpi; 540x960; Samsung; SM-J200F; j2lte; samsung; en_US)',
    'Instagram 24.0.0 Android (24/7.0; 320dpi; 720x1280; Motorola; Moto G (4); athene; qcom; en_US)',
    'Instagram 25.0.0 Android (25/7.1; 640dpi; 1440x2560; ZTE; ZTE A2017G; axon7; qcom; en_US)',
    'Instagram 26.0.0 Android (26/8.0; 480dpi; 1080x2160; Asus; ASUS_X00QD; ASUS_X00QD; qcom; en_US)',
    'Instagram 28.0.0 Android (27/8.1; 480dpi; 1080x2340; Vivo; 1804; 1804; mt6771; en_US)',
    'Instagram 29.0.0 Android (28/9; 440dpi; 1080x2340; Oppo; CPH1917; CPH1917; qcom; en_US)',
    'Instagram 31.0.0 Android (24/7.0; 320dpi; 800x1280; Panasonic; FZ-A2; FZ-A2; intel; en_US)',
    'Instagram 32.0.0 Android (22/5.1; 240dpi; 480x854; Alcatel; 5045D; 5045D; mt6735; en_US)',
    'Instagram 33.0.0 Android (23/6.0; 480dpi; 1920x1080; Meizu; PRO 6 Plus; PRO6Plus; exynos8890; en_US)',
    'Instagram 34.0.0 Android (21/5.0; 320dpi; 720x1280; Lenovo; Lenovo A6000; A6000; qcom; en_US)',
    'Instagram 36.0.0 Android (25/7.1; 420dpi; 1080x1920; Google; Pixel; sailfish; qcom; en_US)',
    'Instagram 37.0.0 Android (26/8.0; 560dpi; 1440x2560; Samsung; SM-G930F; herolte; samsung; en_US)',
    'Instagram 38.0.0 Android (27/8.1; 480dpi; 1080x2248; Xiaomi; POCO F1; beryllium; qcom; en_US)',
    'Instagram 39.0.0 Android (28/9; 440dpi; 1080x2160; Sony; H8216; H8216; qcom; en_US)',
    'Instagram 41.0.0 Android (29/10; 450dpi; 1080x2400; Realme; RMX1931; RMX1931; qcom; en_US)',
    'Instagram 42.0.0 Android (23/6.0; 320dpi; 720x1280; Wiko; U PULSE; UPulse; mt6737; en_US)',
    'Instagram 43.0.0 Android (24/7.0; 240dpi; 600x1024; Archos; 101e Neon; 101eNeon; mt8163; en_US)',
    'Instagram 44.0.0 Android (22/5.1; 240dpi; 540x960; Micromax; Q424; Q424; mt6735; en_US)',
    'Instagram 45.0.0 Android (25/7.1; 480dpi; 1080x1920; Sharp; SH-A01; SH-A01; qcom; en_US)',
    'Instagram 46.0.0 Android (26/8.0; 560dpi; 1440x2880; LG; LG-H930; joan; qcom; en_US)',
    'Instagram 47.0.0 Android (27/8.1; 420dpi; 1080x2160; Nokia; Nokia 6.1; PL2_sprout; qcom; en_US)',
    'Instagram 48.0.0 Android (28/9; 403dpi; 1080x2246; Asus; ASUS_Z01RD; ASUS_Z01RD; qcom; en_US)',
    'Instagram 49.0.0 Android (29/10; 480dpi; 1080x2340; Huawei; YAL-L21; YAL; hisilicon; en_US)',
    'Instagram 51.0.0 Android (24/7.0; 320dpi; 1280x800; Samsung; SM-T385; gta2slte; samsung; en_US)',
    'Instagram 52.0.0 Android (23/6.0; 240dpi; 480x854; Acer; Z530; Z530; mt6735; en_US)',
    'Instagram 53.0.0 Android (22/5.1; 320dpi; 720x1280; Tecno; W4; W4; mt6580; en_US)',
    'Instagram 54.0.0 Android (25/7.1; 480dpi; 1920x1080; ZTE; ZTE BLADE V8; P840F10; qcom; en_US)',
    'Instagram 55.0.0 Android (26/8.0; 420dpi; 1080x2160; Moto G (6); ali; qcom; en_US)',
    'Instagram 56.0.0 Android (27/8.1; 320dpi; 720x1520; Redmi; M1803E6G; E6; qcom; en_US)',
    'Instagram 57.0.0 Android (28/9; 560dpi; 1440x3120; OnePlus; OnePlus7Pro; OnePlus7Pro; qcom; en_US)',
    'Instagram 58.0.0 Android (29/10; 440dpi; 1080x2400; Xiaomi; M2004J19C; merlin; mt6769; en_US)',
    'Instagram 59.0.0 Android (24/7.0; 160dpi; 1280x800; Prestigio; PMT3418_3G; PMT3418_3G; mt8321; en_US)',
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
    Now generates ONLY semi-quad usernames (with at least one underscore or dot).
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
            # Start with a letter (Instagram requirement)
            first_char = random.choice(CHARS["LETTERS"])
            
            # Choose a random position (1-3) to insert a symbol (. or _)
            symbol_positions = [1, 2, 3]
            symbol_pos = random.choice(symbol_positions)
            
            # Choose symbol - dot or underscore
            symbol = random.choice(CHARS["SYMBOLS"])
            
            # Build the username
            username_chars = [first_char]
            
            for pos in range(1, 5):
                if pos == symbol_pos:
                    username_chars.append(symbol)
                else:
                    username_chars.append(random.choice(CHARS["ALL_VALID"]))
            
            username = ''.join(username_chars)
            
            # Validate and ensure it's a semi-quad
            if (username not in self.generated_usernames and 
                self.is_valid_instagram_username(username) and
                self.is_semi_quad(username)):
                self.generated_usernames.add(username)
                return username
        
        # Fallback: Generate a guaranteed semi-quad username
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
        
        # Ultimate fallback with timestamp
        timestamp = int(time.time() * 1000) % 100
        username = f"{random.choice(CHARS['LETTERS'])}{timestamp:02d}_x"
        self.generated_usernames.add(username)
        return username


class AutoInstagramChecker:
    """
    Handles the HTTP communication with Instagram APIs.
    Uses Rotating Proxies and Random User Agents.
    """
    def __init__(self, clients):
        self.clients = clients
    
    def _get_random_headers(self):
        """Generates headers with randomized device bandwidth/connection type."""
        headers = HEADERS_TEMPLATE.copy()
        headers['User-Agent'] = f'Instagram {random.choice(USER_AGENTS)}'
        headers['X-IG-Connection-Type'] = random.choice(['WIFI', 'MOBILE.LTE', 'MOBILE.5G'])
        headers['X-IG-Bandwidth-Speed-KBPS'] = str(random.randint(1000, 8000))
        headers['X-IG-Bandwidth-TotalBytes-B'] = str(random.randint(500000, 5000000))
        headers['X-IG-Bandwidth-TotalTime-MS'] = str(random.randint(50, 500))
        return headers

    async def check_username_availability(self, username):
        """
        Checks availability of a username using a random proxy client.
        """
        # Pick a random client from the pool
        client = random.choice(self.clients)

        # Generate Fresh Device IDs for total anonymity
        data = {
            "email": CONFIG["FIXED_EMAIL"],
            "username": username,
            "password": f"Aa123456{username}",
            "device_id": f"android-{uuid4()}",
            "guid": str(uuid4()),
        }
        
        try:
            # Short timeout (3s)
            response = await client.post(
                CONFIG["INSTAGRAM_API_URL"], 
                headers=self._get_random_headers(), 
                data=data
            )
            response_text = response.text
            
            if '"spam"' in response_text or 'rate_limit_error' in response_text:
                return False, response_text, "rate_limit"
            
            is_available = '"email_is_taken"' in response_text
            return is_available, response_text, None
            
        except (httpx.RequestError, httpx.TimeoutException):
            # Proxy error or timeout is common, treat as not found/skip to keep moving
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
        """Starts the async task pool."""
        self.start_time = time.time()
        
        # Initialize clients for each proxy
        # We assume PROXIES_LIST has valid proxy URLs
        clients = []
        for proxy_url in PROXIES_LIST:
            try:
                # httpx.AsyncClient manages the connection pool for this proxy
                client = httpx.AsyncClient(proxy=proxy_url, timeout=3.0)
                clients.append(client)
            except Exception:
                continue
        
        if not clients:
            return {
                "status": "failed",
                "username": None,
                "reason": "no_proxies_available",
                "duration": 0
            }

        checker = AutoInstagramChecker(clients)
        
        # Launch workers
        tasks = [asyncio.create_task(self._worker(checker)) for _ in range(self.max_concurrency)]
        
        # Wait for completion or stop
        while not self.should_stop:
            if time.time() - self.start_time > CONFIG["TIMEOUT_SECONDS"]:
                self.should_stop = True
                break
            
            # Check if all tasks finished (e.g. if we had limited attempts, but here we loop forever)
            # Actually, we should check if we found something
            if self.found_username:
                break
                
            await asyncio.sleep(0.1)

        # Ensure all tasks stop
        self.should_stop = True
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cleanup clients
        for c in clients:
            await c.aclose()
            
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