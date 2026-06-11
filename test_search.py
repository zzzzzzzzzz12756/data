import requests, json
proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}
r = requests.get("https://huggingface.co/api/spaces?search=triposr&limit=5&sort=likes", proxies=proxies, timeout=15)
data = r.json()
for s in data[:5]:
    print(f"{s['id']} | likes:{s.get('likes',0)} | sdk:{s.get('sdk','')} | status:{s.get('status','')}")
