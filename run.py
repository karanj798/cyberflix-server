import os

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.gzip import GZipMiddleware
from lib import env
from lib.web_worker import WebWorker
from typing import Optional

SERVER_VERSION = "2.0.0"

worker = WebWorker()
app = FastAPI()
app.add_middleware(GZipMiddleware, minimum_size=1000)

project_dir = os.path.join(app.root_path, "web/")
app.mount("/static", StaticFiles(directory=project_dir), name="static")
templates = Jinja2Templates(directory=project_dir)

# Add a new constant for cache durations
CACHE_DURATIONS = {
    "SHORT": 60 * 15,       # 15 minutes
    "MEDIUM": 60 * 60 * 4,  # 4 hours
    "LONG": 60 * 60 * 24,   # 24 hours
    "VERY_LONG": 60 * 60 * 24 * 7  # 7 days
}


def add_cache_headers(max_age: int) -> dict:
    """Add cache control headers with improved caching strategy."""
    return {
        "Cache-Control": (
            f"public, "
            f"max-age={max_age}, "
            f"stale-while-revalidate={max_age // 2}, "
            f"stale-if-error={max_age * 2}"
        ),
        "Vary": "Accept-Encoding"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Check server health."""
    catalogs = worker.get_web_config().get("config", {}).get("catalogs", [])
    if catalogs == []:
        return JSONResponse({"status": "error"}, status_code=500)
    return JSONResponse({"status": "ok"}, status_code=200)


def __json_response(data: dict, extra_headers: dict[str, str] = {}, status_code: int = 200):
    response = JSONResponse(data, status_code=status_code)
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "*",
    }
    headers.update(extra_headers)
    response.headers.update(headers)
    return response


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    cache_age = 60 * 60 * 2  # 2 hours
    headers = add_cache_headers(cache_age)
    response = templates.TemplateResponse("index.html", {"request": request}, headers=headers)
    return response


@app.get("/configure")
@app.get("/c/{configs}/configure")
async def configure(configs: Optional[str] = None):
    return RedirectResponse(url="/", status_code=302)


@app.get("/last_update.txt")
async def last_update():
    last_update = worker.last_update.strftime("%m/%d/%Y, %H:%M:%S")
    return last_update

@app.get("/recent_changes.json")
async def recent_changes():
    changes = worker.get_recent_changes()
    return __json_response(changes)


def get_image_asset(image_path: str):
    cache_age = 60 * 60 * 12  # 12 hours
    headers = add_cache_headers(cache_age)
    media_type = "image/jpeg"
    if image_path.endswith(".ico"):
        media_type = "image/vnd.microsoft.icon"
    elif image_path.endswith(".png"):
        media_type = "image/png"

    return FileResponse(image_path, media_type=media_type, headers=headers)


@app.get("/favicon.ico")
async def favicon():
    return get_image_asset("./web/favicon.png")


@app.get("/logo.png")
async def logo():
    return get_image_asset("./web/assets/assets/logo.png")


@app.get("/background.png")
async def background():
    return get_image_asset("./web/assets/assets/bg_image.jpeg")


@app.get("/manifest.json")
@app.get("/c/{configs}/manifest.json")
async def manifest(
    request: Request,
    configs: Optional[str] = None,
):
    referer = str(request.base_url)
    manifest = worker.get_configured_manifest(referer, configs)
    manifest.update({"server_version": SERVER_VERSION})
    headers = add_cache_headers(CACHE_DURATIONS["SHORT"])
    return __json_response(manifest, extra_headers=headers)


@app.get("/web_config.json")
async def web_config():
    config = worker.get_web_config()
    headers = add_cache_headers(CACHE_DURATIONS["MEDIUM"])
    return __json_response(config, extra_headers=headers)


@app.get("/meta/{type}/{id}.json")
@app.get("/c/{configs}/meta/{type}/{id}.json")
async def meta(type: Optional[str], id: Optional[str], configs: Optional[str] = None):
    if id is None or type is None:
        return HTTPException(status_code=404, detail="Not found")
    meta = worker.get_meta(id=id, s_type=type, config=configs)
    headers = add_cache_headers(CACHE_DURATIONS["VERY_LONG"])
    return __json_response(meta, extra_headers=headers)


@app.get("/catalog/{type}/{id}.json")
@app.get("/catalog/{type}/{id}/{extras}.json")
async def catalog(type: Optional[str], id: Optional[str], extras: Optional[str] = None):
    return await catalog_with_configs(configs=None, type=type, id=id, extras=extras)


@app.get("/c/{configs}/catalog/{type}/{id}.json")
@app.get("/c/{configs}/catalog/{type}/{id}/{extras}.json")
async def catalog_with_configs(
    configs: Optional[str], type: Optional[str], id: Optional[str], extras: Optional[str] = None
):
    if id is None:
        return HTTPException(status_code=404, detail="Not found")

    metas = await worker.get_configured_catalog(id=id, extras=extras, config=configs)
    headers = add_cache_headers(CACHE_DURATIONS["MEDIUM"])
    return __json_response(metas, extra_headers=headers)

if __name__ == "__main__":
    uvicorn.run(
        app,
        loop="uvloop",
        reload=False,
        host=env.APP_URL,
        port=env.APP_PORT,
        log_level=env.APP_LOG_LEVEL,
        timeout_keep_alive=env.APP_TIMEOUT,
    )
