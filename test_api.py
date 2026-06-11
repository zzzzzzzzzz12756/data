import requests, json, base64, sys
from pathlib import Path

proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
SPACE = "https://stabilityai-triposr.hf.space"

# Read test image
img_path = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\dell\AppData\Local\Temp\test_bus.png"
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

# Try direct predict with base64
print("Testing /api/predict with base64...")
resp = requests.post(
    f"{SPACE}/api/predict",
    json={"data": [
        f"data:image/png;base64,{img_b64}",
        True,
        0.85
    ]},
    proxies=proxies,
    timeout=120
)
print(f"Status: {resp.status_code}")
print(f"Response: {resp.text[:500]}")
