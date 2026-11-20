# ClipNest — TikTok video downloader

An original, responsive TikTok downloader starter built with FastAPI, yt-dlp, and plain HTML/CSS/JavaScript.

## Features
- Responsive ClipNest interface
- TikTok URL validation (TikTok hosts only)
- Server-side video retrieval for public, accessible TikTok posts
- MP4 file response
- Friendly error messages and basic request cooldown
- Docker deployment support

## Run locally

Requires Python 3.10+ and FFmpeg (recommended for merging media formats).

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows PowerShell:
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app:app --reload
```

Open http://localhost:8000.

## Docker

```bash
docker build -t clipnest .
docker run --rm -p 8000:8000 clipnest
```

## Before public launch — important

This is a working starter, not a hardened high-traffic service. Before deploying publicly:

1. Confirm that your use complies with TikTok's current Terms, applicable copyright law, and the rights of the video owner. Only download content you own or have permission to save. Do not use this service to access private, restricted, or login-gated content.
2. Review yt-dlp's current support and licensing, and keep it updated. Platform changes can temporarily break extraction.
3. Replace the demo shared cooldown in `app.py` with a real per-IP rate limiter backed by Redis or your hosting provider. Add abuse monitoring and request quotas.
4. Add a background cleanup job for temporary files. Use object storage and expiring signed URLs for production.
5. Configure HTTPS, resource limits, concurrency limits, logging, and an explicit privacy policy.
6. The default size cap is 100 MB. Set `MAX_FILE_MB` to change it.

## Limitations
- Only public, directly accessible TikTok links are supported. Private, removed, age-restricted, region-restricted, or otherwise unavailable videos may fail.
- Extraction depends on third-party platform behavior and may stop working when TikTok changes its site.
- This project does not remove watermarks, bypass access controls, or use TikTok credentials.
- The backend currently returns the downloaded file directly. For production, move large downloads to background jobs and object storage.

## Project structure

```text
clipnest/
  app.py
  requirements.txt
  Dockerfile
  static/
    index.html
    styles.css
    app.js
```
