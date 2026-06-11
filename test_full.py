import requests, time
PX = {'http': 'http://127.0.0.1:7897', 'https': 'http://127.0.0.1:7897'}
KEY = 'tsk_LYTWnjBgzlleIXbZ8gniN-f25yqiRjUxssOxo2ZJMY4'
BASE = 'https://api.tripo3d.ai/v2/openapi'
auth = {'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'}

print('1. Uploading...')
with open(r'D:\3d-photo\test.png', 'rb') as f:
    r = requests.post(f'{BASE}/upload', headers={'Authorization': f'Bearer {KEY}'}, files={'file': ('test.png', f, 'image/png')}, proxies=PX, timeout=30)
token = r.json()['data']['image_token']
print(f'   Token: {token}')

print('2. Creating task...')
r2 = requests.post(f'{BASE}/task', headers=auth, json={'type': 'image_to_model', 'file': {'type': 'png', 'file_token': token}}, proxies=PX, timeout=30)
print(f'   Response: {r2.text[:500]}')
tid = r2.json()['data']['task_id']
print(f'   Task ID: {tid}')

print('3. Waiting...')
for i in range(30):
    time.sleep(3)
    r3 = requests.get(f'{BASE}/task/{tid}', headers=auth, proxies=PX, timeout=15)
    d = r3.json()['data']
    st = d['status']
    prog = d.get('progress', 0)
    print(f'   [{i*3}s] {st} {prog}%')
    if st == 'success':
        url = d.get('output', {}).get('model')
        print(f'   Model URL: {url}')
        break
    if st == 'failed':
        print(f'   FAILED: {d}')
        break
