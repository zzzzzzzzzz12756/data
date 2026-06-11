import os, httpx, time, json
os.environ.pop("no_proxy", None)
os.environ.pop("NO_PROXY", None)

KEY = 'tsk_LYTWnjBgzlleIXbZ8gniN-f25yqiRjUxssOxo2ZJMY4'
BASE = 'https://api.tripo3d.ai/v2/openapi'

client = httpx.Client(proxy='http://127.0.0.1:7897', verify=False, timeout=60.0)

# Upload
print('1. Upload...')
with open(r'D:\3d-photo\outputs\test_input.png', 'rb') as f:
    r = client.post(f'{BASE}/upload', headers={'Authorization': f'Bearer {KEY}'}, files={'file': ('test.png', f, 'image/png')})
token = r.json()['data']['image_token']
print(f'   Token: {token}')

# Create task
print('2. Task...')
r2 = client.post(f'{BASE}/task', headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
    json={'type': 'image_to_model', 'file': {'type': 'png', 'file_token': token}})
d2 = r2.json()
print(f'   Response: {json.dumps(d2, indent=2)}')
tid = d2['data']['task_id']

# Poll
print('3. Poll...')
for i in range(40):
    time.sleep(3)
    r3 = client.get(f'{BASE}/task/{tid}', headers={'Authorization': f'Bearer {KEY}'})
    d = r3.json()['data']
    st = d['status']
    print(f'   [{i*3}s] {st} {d.get("progress",0)}%')
    if st == 'success':
        print(f'   Full output: {json.dumps(d, indent=2)}')
        break
    if st == 'failed':
        print(f'   FAILED: {json.dumps(d, indent=2)}')
        break

client.close()
