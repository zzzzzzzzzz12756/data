import httpx, time

KEY = 'tsk_LYTWnjBgzlleIXbZ8gniN-f25yqiRjUxssOxo2ZJMY4'
BASE = 'https://api.tripo3d.ai/v2/openapi'
PX = 'http://127.0.0.1:7897'

client = httpx.Client(proxy=PX, verify=False, timeout=60.0)

print('1. Uploading...')
with open(r'D:\3d-photo\test.png', 'rb') as f:
    r = client.post(
        f'{BASE}/upload',
        headers={'Authorization': f'Bearer {KEY}'},
        files={'file': ('test.png', f, 'image/png')}
    )
print(f'   Status: {r.status_code}')
data = r.json()
token = data['data']['image_token']
print(f'   Token: {token}')

print('2. Creating task...')
r2 = client.post(
    f'{BASE}/task',
    headers={'Authorization': f'Bearer {KEY}', 'Content-Type': 'application/json'},
    json={'type': 'image_to_model', 'file': {'type': 'png', 'file_token': token}}
)
print(f'   Status: {r2.status_code}')
print(f'   Response: {r2.json()}')
tid = r2.json()['data']['task_id']

print('3. Polling...')
for i in range(40):
    time.sleep(3)
    r3 = client.get(f'{BASE}/task/{tid}', headers={'Authorization': f'Bearer {KEY}'})
    d = r3.json()['data']
    st = d['status']
    prog = d.get('progress', 0)
    print(f'   [{i*3}s] {st} {prog}%')
    if st == 'success':
        url = d.get('output', {}).get('model')
        print(f'   DOWNLOAD: {url}')
        break
    if st == 'failed':
        print(f'   FAILED')
        break

client.close()
