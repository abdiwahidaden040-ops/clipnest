import os
import re
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from starlette.background import BackgroundTask
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
import yt_dlp

APP_DIR = Path(__file__).parent
DOWNLOAD_DIR = Path(tempfile.gettempdir()) / "clipnest-downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_MB = int(os.getenv("MAX_FILE_MB", "100"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "8"))
_last_request = {}
_lock = threading.Lock()

app = FastAPI(title="ClipNest", version="1.0.0")
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")

ALLOWED_HOSTS = {"tiktok.com", "www.tiktok.com", "m.tiktok.com", "vm.tiktok.com", "vt.tiktok.com"}

class DownloadRequest(BaseModel):
    url: HttpUrl

def validate_tiktok_url(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or not any(
        host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS
    ):
        raise HTTPException(status_code=400, detail="Please enter a valid TikTok video link.")
    if not parsed.path or parsed.path == "/":
        raise HTTPException(status_code=400, detail="That link does not look like a video link.")
    return value

def rate_limit(client: str):
    now = time.time()
    with _lock:
        previous = _last_request.get(client, 0)
        if now - previous < RATE_LIMIT_SECONDS:
            raise HTTPException(status_code=429, detail="Please wait a few seconds before trying again.")
        _last_request[client] = now

@app.get("/", response_class=HTMLResponse)
def home():
    return (APP_DIR / "static" / "index.html").read_text(encoding="utf-8")

@app.get("/api/health")
def health():
    return {"ok": True, "service": "ClipNest"}

@app.post("/api/download")
def download_video(payload: DownloadRequest, request: Request):
    url = validate_tiktok_url(str(payload.url))
    # In-memory per-IP cooldown for a single-process starter deployment.
    # Use Redis or a hosting-provider rate limiter when running multiple workers.
    client_ip = request.client.host if request.client else "unknown"
    rate_limit(client_ip)

    job_id = os.urandom(12).hex()
    output_template = str(DOWNLOAD_DIR / f"{job_id}.%(ext)s")
    options = {
        "outtmpl": output_template,
        "format": "mp4/best",
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 20,
        "retries": 1,
        "max_filesize": MAX_FILE_MB * 1024 * 1024,
        "restrictfilenames": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filepath = Path(ydl.prepare_filename(info))
            if not filepath.exists():
                candidate = DOWNLOAD_DIR / f"{job_id}.mp4"
                if candidate.exists():
                    filepath = candidate
            if not filepath.exists():
                raise RuntimeError("The video file was not produced.")
            if filepath.stat().st_size > MAX_FILE_MB * 1024 * 1024:
                filepath.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="The video is larger than the allowed size.")
            title = re.sub(r"[^a-zA-Z0-9 _-]", "", info.get("title") or "tiktok-video").strip()[:70]
            filename = (title or "tiktok-video") + ".mp4"
            return FileResponse(
                filepath,
                media_type="video/mp4",
                filename=filename,
                background=BackgroundTask(filepath.unlink, missing_ok=True),
            )
    except HTTPException:
        raise
    except Exception:
        # Do not expose extractor internals or remote page content to visitors.
        raise HTTPException(
            status_code=422,
            detail="We couldn't retrieve this video. It may be private, unavailable, region-restricted, or unsupported. Try a public TikTok video link."
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=True)
