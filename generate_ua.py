import json
import random

# Components for generating valid legacy User-Agents
# Format: Instagram {app_ver} Android ({android_ver}/{sdk_ver}; {dpi}dpi; {res}; {brand}; {model}; {device}; {cpu}; {locale})

INSTAGRAM_VERSIONS = [
    f"{major}.{minor}.{patch}" 
    for major in range(10, 120, 2)  # Versions 10.x to 120.x (Safe Legacy)
    for minor in range(0, 5) 
    for patch in range(0, 5)
]

ANDROID_VERSIONS = [
    ("19", "4.4.2"), ("21", "5.0"), ("22", "5.1"), ("23", "6.0"), 
    ("24", "7.0"), ("25", "7.1.1"), ("26", "8.0.0"), ("27", "8.1.0"), 
    ("28", "9"), ("29", "10")
]

DEVICES = [
    # Samsung
    {"brand": "Samsung", "model": "SM-G930F", "device": "herolte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-G950F", "device": "dreamlte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-G960F", "device": "starlte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-J530F", "device": "j5y17lte", "cpu": "exynos7870"},
    {"brand": "Samsung", "model": "SM-A520F", "device": "a5y17lte", "cpu": "samsung"},
    {"brand": "Samsung", "model": "SM-N950F", "device": "greatlte", "cpu": "samsung"},
    
    # Xiaomi
    {"brand": "Xiaomi", "model": "Redmi Note 7", "device": "lavender", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "Redmi Note 5", "device": "whyred", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "MI 8", "device": "dipper", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "POCO F1", "device": "beryllium", "cpu": "qcom"},
    {"brand": "Xiaomi", "model": "Redmi 4X", "device": "santoni", "cpu": "qcom"},
    
    # Huawei
    {"brand": "Huawei", "model": "ANE-LX1", "device": "HWANE", "cpu": "hisilicon"},
    {"brand": "Huawei", "model": "POT-LX1", "device": "HWPOT-H", "cpu": "hisilicon"},
    {"brand": "Huawei", "model": "VOG-L29", "device": "VOG", "cpu": "hisilicon"},
    
    # OnePlus
    {"brand": "OnePlus", "model": "ONEPLUS A6003", "device": "OnePlus6", "cpu": "qcom"},
    {"brand": "OnePlus", "model": "ONEPLUS A5000", "device": "OnePlus5", "cpu": "qcom"},
    
    # Sony
    {"brand": "Sony", "model": "G8341", "device": "G8341", "cpu": "qcom"},
    {"brand": "Sony", "model": "F5121", "device": "F5121", "cpu": "qcom"},
    
    # LG
    {"brand": "LG", "model": "LG-H870", "device": "lucye", "cpu": "qcom"},
    {"brand": "LG", "model": "LG-H930", "device": "joan", "cpu": "qcom"},
]

RESOLUTIONS = [
    "1080x1920", "1080x2160", "1080x2240", "1080x2280", "1080x2340",
    "720x1280", "720x1440", "720x1520",
    "1440x2560", "1440x2880", "1440x2960"
]

DPIS = ["320", "420", "440", "480", "560", "640"]

LOCALES = ["en_US", "en_GB", "es_ES", "fr_FR", "de_DE", "it_IT", "ru_RU", "pt_BR"]

def generate_agents(count=1000):
    agents = []
    seen = set()
    
    while len(agents) < count:
        app_ver = random.choice(INSTAGRAM_VERSIONS)
        sdk, android_ver = random.choice(ANDROID_VERSIONS)
        device = random.choice(DEVICES)
        res = random.choice(RESOLUTIONS)
        dpi = random.choice(DPIS)
        # 10% chance of random locale, else en_US
        locale = random.choice(LOCALES) if random.random() < 0.1 else "en_US"
        
        # Format: Instagram {app} Android ({sdk}/{android}; {dpi}dpi; {res}; {brand}; {model}; {device}; {cpu}; {locale})
        ua_string = (
            f"Instagram {app_ver} Android "
            f"({sdk}/{android_ver}; {dpi}dpi; {res}; {device['brand']}; "
            f"{device['model']}; {device['device']}; {device['cpu']}; {locale})"
        )
        
        if ua_string not in seen:
            seen.add(ua_string)
            agents.append(ua_string)
            
    return agents

if __name__ == "__main__":
    agents = generate_agents(1000)
    with open("user_agents.json", "w") as f:
        json.dump(agents, f, indent=4)
    print(f"Generated {len(agents)} User-Agents in user_agents.json")
