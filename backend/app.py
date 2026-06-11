"""
3D Photo Generator - Backend
"""
import os, uuid, time, json
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx

BASE_DIR = Path(__file__).parent.parent
OUTPUT_DIR = BASE_DIR / "outputs"
FRONTEND_DIR = BASE_DIR / "frontend"
OUTPUT_DIR.mkdir(exist_ok=True)

KEY = os.environ.get("TRIPO_API_KEY", "tsk_LYTWnjBgzlleIXbZ8gniN-f25yqiRjUxssOxo2ZJMY4")
BASE = "https://api.tripo3d.ai/v2/openapi"

app = FastAPI(title="3D Photo Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
from fastapi.staticfiles import StaticFiles
app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")

def tripo_request(method, url, headers=None, files=None, data=None, json_data=None, timeout=60):
    """Make HTTP request to Tripo API"""
    client = httpx.Client(timeout=timeout, verify=False)
    try:
        if method == "GET":
            r = client.get(url, headers=headers)
        elif method == "POST":
            if files:
                r = client.post(url, headers=headers, files=files)
            elif json_data:
                r = client.post(url, headers=headers, json=json_data)
            else:
                r = client.post(url, headers=headers, content=data)
        r.raise_for_status()
        return r.json()
    finally:
        client.close()

@app.get("/")
async def index():
    return HTMLResponse((FRONTEND_DIR / "index.html").read_text(encoding="utf-8"))

@app.get("/shop")
async def shop():
    return HTMLResponse((FRONTEND_DIR / "shop.html").read_text(encoding="utf-8"))

@app.post("/api/generate")
async def generate_3d(file: UploadFile = File(...)):
    mid = str(uuid.uuid4())[:8]
    tmp = OUTPUT_DIR / f"{mid}_input.png"

    try:
        content = await file.read()
        with open(str(tmp), "wb") as f:
            f.write(content)

        # 1. Upload
        print(f"[{mid}] Uploading...")
        with open(str(tmp), "rb") as f:
            r = tripo_request("POST", f"{BASE}/upload",
                            headers={"Authorization": f"Bearer {KEY}"},
                            files={"file": (tmp.name, f, "image/png")})
        if r.get("code") != 0:
            raise Exception(f"Upload: {r.get('message')}")
        token = r["data"]["image_token"]

        # 2. Create task
        print(f"[{mid}] Creating task...")
        r2 = tripo_request("POST", f"{BASE}/task",
                          headers={"Authorization": f"Bearer {KEY}"},
                          json_data={"type": "image_to_model", "file": {"type": "png", "file_token": token}})
        if r2.get("code") != 0:
            raise Exception(f"Task: {r2.get('message')}")
        tid = r2["data"]["task_id"]

        # 3. Poll
        print(f"[{mid}] Generating...")
        client = httpx.Client(timeout=30, verify=False)
        try:
            for i in range(60):
                time.sleep(3)
                r3 = client.get(f"{BASE}/task/{tid}",
                               headers={"Authorization": f"Bearer {KEY}"})
                d = r3.json()["data"]
                st = d["status"]
                prog = d.get("progress", 0)
                if i % 5 == 0:
                    print(f"  {st} {prog}%")

                if st == "success":
                    output = d.get("output", {})
                    model_url = output.get("pbr_model") or output.get("model") or output.get("glb")
                    if not model_url:
                        raise Exception(f"No model URL. Keys: {list(output.keys())}")

                    # Download model
                    print(f"[{mid}] Downloading...")
                    dl = httpx.Client(timeout=60, verify=False, follow_redirects=True)
                    try:
                        resp = dl.get(model_url)
                        out = OUTPUT_DIR / f"{mid}.glb"
                        out.write_bytes(resp.content)
                    finally:
                        dl.close()

                    if not out.exists() or out.stat().st_size < 100:
                        raise Exception("Download failed or file too small")

                    kb = round(out.stat().st_size / 1024)
                    print(f"[{mid}] Done! {kb}KB")
                    return {
                        "success": True,
                        "model_id": mid,
                        "download_url": f"/api/download/{mid}",
                        "view_url": f"/api/model/{mid}",
                        "size_kb": kb
                    }

                if st == "failed":
                    raise Exception(f"Generation failed: {d}")
        finally:
            client.close()

        raise Exception("Timeout: generation took >3min")

    except Exception as e:
        print(f"[{mid}] FAIL: {e}")
        raise HTTPException(500, f"Failed: {str(e)[:300]}")
    finally:
        if tmp.exists():
            tmp.unlink()

@app.get("/api/model/{model_id}")
async def get_model(model_id: str):
    p = OUTPUT_DIR / f"{model_id}.glb"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="model/gltf-binary")

@app.get("/api/download/{model_id}")
async def download_model(model_id: str):
    p = OUTPUT_DIR / f"{model_id}.glb"
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p, media_type="model/gltf-binary", filename=f"3d_{model_id}.glb")

@app.get("/api/health")
async def health():
    return {"status": "ok"}
