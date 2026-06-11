"""
3D Photo Generator - Backend (Tripo API via curl)
Uses curl subprocess for reliable proxy connections
"""
import os, uuid, time, json, subprocess, tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

os.environ.pop("no_proxy", None)
os.environ.pop("NO_PROXY", None)

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

def curl(method, url, headers=None, files=None, data=None, timeout=60):
    """Run curl with proxy and return JSON response"""
    cmd = ["curl.exe", "-s", "-k", "-x", "http://127.0.0.1:7897",
           "-X", method, url, "--connect-timeout", "15", "-m", str(timeout)]
    if headers:
        for k, v in headers.items():
            cmd += ["-H", f"{k}: {v}"]
    if files:
        for k, v in files.items():
            cmd += ["-F", f"{k}=@{v}"]
    if data:
        cmd += ["-d", data]

    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout+10)
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
            err = result.stderr[:200] or result.stdout[:200] or 'empty response'
            if attempt < 2:
                print(f"  curl retry {attempt+1}: {err}")
                time.sleep(2)
                continue
            raise Exception(f"curl failed (rc={result.returncode}): {err}")
        except subprocess.TimeoutExpired:
            if attempt < 2:
                print(f"  curl timeout retry {attempt+1}")
                time.sleep(2)
                continue
            raise Exception("curl timeout")

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
        r = curl("POST", f"{BASE}/upload",
                 headers={"Authorization": f"Bearer {KEY}"},
                 files={"file": str(tmp)})
        if r.get("code") != 0:
            raise Exception(f"Upload: {r.get('message')}")
        token = r["data"]["image_token"]

        # 2. Create task
        print(f"[{mid}] Creating task...")
        body = json.dumps({"type": "image_to_model", "file": {"type": "png", "file_token": token}})
        r2 = curl("POST", f"{BASE}/task",
                  headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
                  data=body)
        if r2.get("code") != 0:
            raise Exception(f"Task: {r2.get('message')}")
        tid = r2["data"]["task_id"]

        # 3. Poll
        print(f"[{mid}] Generating...")
        for i in range(60):
            time.sleep(3)
            r3 = curl("GET", f"{BASE}/task/{tid}",
                     headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
            d = r3["data"]
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
                dl_cmd = ["curl.exe", "-s", "-k", "-x", "http://127.0.0.1:7897",
                          "-L", "-o", str(OUTPUT_DIR / f"{mid}.glb"),
                          model_url, "--connect-timeout", "15", "-m", "60"]
                subprocess.run(dl_cmd, check=True, timeout=70)

                out = OUTPUT_DIR / f"{mid}.glb"
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
