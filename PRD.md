# Clousx API - Instagram Username Checker
## Product Requirements Document (PRD)

---

## 📋 Overview

**Product Name:** Clousx API  
**Version:** 2.0 (Ultimate Stealth Edition)  
**Type:** RESTful API Service  
**Platform:** Railway Cloud  
**Language:** Python 3.11+ (Flask + Async)

### Mission Statement
توفير خدمة سريعة وموثوقة للبحث عن usernames متاحة على Instagram مع أقصى درجات التخفي لتجنب الحظر.

---

## 🎯 Core Features

### 1. Username Search Modes

| Mode | Endpoint | Username Type | Speed | Stealth |
|------|----------|---------------|-------|---------|
| **Simple** | `/search` | 5 أحرف عشوائية | عادي | ✅ High |
| **Semi-Quad** | `/prosearch` | 5 أحرف مع `_` أو `.` | سريع جداً | ⚡ Fast |
| **Smart Mix** | `/search` (70/30) | تلقائي | متوازن | ✅✅ Best |

### 2. Debugging Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/infosearch` | Simple search + detailed logging |
| `/infoprosearch` | Semi-quad search + detailed logging |

### 3. Monitoring Endpoints

| Endpoint | Returns |
|----------|---------|
| `/` | System status, features, endpoints list |
| `/status` | Detailed metrics (proxies, performance, config) |
| `/warm` | Trigger manual session warming |
| `/dashboard` | HTML admin interface |

---

## 🔐 Stealth System

### Dynamic Identity Engine
كل طلب يولّد هوية جهاز أندرويد كاملة ومختلفة:

```
┌─────────────────────────────────────────┐
│  IDENTITY COMPONENTS                    │
├─────────────────────────────────────────┤
│  • Device Model (25+ devices)           │
│  • Android Version (8.0 - 14.0)         │
│  • IG App Version (12 versions)         │
│  • Device ID (UUID)                     │
│  • Phone ID (UUID)                      │
│  • GUID (UUID)                          │
│  • Advertising ID (ADID)                │
│  • Family Device ID                     │
│  • Waterfall ID                         │
│  • Full HTTP Headers Set                │
└─────────────────────────────────────────┘
```

### Dual Identity per Proxy
كل بروكسي يحصل على هويتين مختلفتين تتبادلان:
```
Proxy A ─→ Identity 1 (Samsung S23)
        └→ Identity 2 (Pixel 7 Pro)  ← Rotation
```

### Human Behavior Simulation
- **Random Delays:** 0.5 - 2.0 ثانية بين الطلبات
- **Occasional Long Pauses:** 10% احتمال توقف 2-4 ثواني
- **Session Warming:** تسخين الجلسات قبل الاستخدام

---

## ⚙️ Configuration

### Default Settings
```python
CONFIG = {
    "TIMEOUT": 90,              # Max search time (seconds)
    "MAX_CONCURRENT": 20,       # Parallel requests limit
    "MIN_DELAY": 0.5,           # Min delay between batches
    "MAX_DELAY": 2.0,           # Max delay between batches
    "PROXY_REST_TIME": 120,     # Proxy cooldown (seconds)
    "MAX_REQUESTS_PER_PROXY": 5 # Before rotation
}
```

### Semi-Quad Mode (Fast)
```python
FAST_MODE = {
    "MAX_CONCURRENT": 50,       # More aggressive
    "TIMEOUT": 30,              # Shorter timeout
    "DELAYS": False             # No delays for speed
}
```

---

## 📊 API Response Formats

### Success Response
```json
{
    "status": "success",
    "username": "abc12",
    "duration": 2.45,
    "stats": {
        "checked": 15,
        "taken": 14,
        "errors": 0,
        "rate_limits": 0
    },
    "rate_limited_proxies": "0/10",
    "warm_sessions": "10/10"
}
```

### Failed Response
```json
{
    "status": "failed",
    "reason": "timeout",
    "duration": 90.0,
    "stats": {...}
}
```

### Status Response (`/status`)
```json
{
    "proxies": {
        "total": 10,
        "available": 8,
        "warm": 10,
        "cold": 0,
        "rate_limited": 2,
        "resting": 0
    },
    "performance": {
        "total_requests": 1250,
        "success_rate": "87.5%"
    },
    "warming": {
        "warm_duration_seconds": 300,
        "warmed_sessions_count": 10
    },
    "config": {...}
}
```

---

## 🌐 Proxy Management

### Smart Rotation System
```
┌─────────────────────────────────────────┐
│           PROXY LIFECYCLE               │
├─────────────────────────────────────────┤
│                                         │
│   FRESH ──→ IN USE ──→ RESTING          │
│     ↑                      │            │
│     └──────────────────────┘            │
│                                         │
│   Rate Limited? → Quarantine 120s       │
│                                         │
└─────────────────────────────────────────┘
```

### Proxy Health Tracking
- **Usage Counter:** عدد الطلبات لكل بروكسي
- **Success Rate:** نسبة النجاح
- **Last Used:** آخر استخدام
- **Rate Limit Status:** حالة الحظر

---

## 📁 Project Structure

```
Clousx api/
├── app.py              # Main application (997 lines)
├── requirements.txt    # Dependencies
├── Procfile           # Railway start command
├── runtime.txt        # Python version
├── proxies.txt        # Proxy list (private)
└── admin_dashboard.html # Local monitoring UI
```

### Dependencies
```
flask
flask-cors
httpx
```

---

## 🚀 Deployment

### Railway Configuration
- **Build:** Auto-detected (Python)
- **Start Command:** `gunicorn app:app` (from Procfile)
- **Port:** Environment variable `$PORT`

### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5000 | Server port |

---

## 📈 Performance Metrics

### Target KPIs
| Metric | Target |
|--------|--------|
| Success Rate | > 80% |
| Avg Response Time | < 5s |
| Rate Limit Rate | < 10% |
| Uptime | 99%+ |

### Bottlenecks & Mitigations
| Issue | Solution |
|-------|----------|
| Rate Limiting | Proxy rotation + Rest periods |
| Slow Proxies | Timeout + Skip mechanism |
| IP Blocks | Residential/Mobile proxies |

---

## 🔮 Future Roadmap

### v2.1 (Planned)
- [ ] Auto Proxy Fetcher من مصادر مجانية
- [ ] Webhook Notifications عند إيجاد username
- [ ] API Key Authentication
- [ ] Username Save to File

### v3.0 (Vision)
- [ ] WebSocket Live Updates
- [ ] Custom Username Patterns
- [ ] Bulk Search Mode
- [ ] Rate Limit Prediction AI

---

## 📞 Support

**Developer:** Clousx  
**Platform:** Railway  
**API Base:** `https://web-production-0fd33.up.railway.app`

---

*Last Updated: January 2026*
