from __future__ import annotations

import html
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import FastAPI, HTTPException, Path as ApiPath
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_METADATA = "https://archive.org/metadata/{identifier}"
BLOCKED = re.compile(
    r"\b(torrent|camrip|webrip|cracked|pirated?|stolen|leaked|bypass|drm|"
    r"latest movie free|watch paid content free)\b",
    re.IGNORECASE,
)
SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9._-]{1,160}$")
VIDEO_EXTENSIONS = (".mp4", ".webm", ".ogv")
VIDEO_FORMAT = re.compile(r"MPEG4|h\.264|WebM|Ogg Video", re.IGNORECASE)

app = FastAPI(
    title="OPENREELpy",
    description="Public-domain and open-access video discovery API",
    version="1.1.0",
    docs_url="/api/docs",
    redoc_url=None,
)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)


def validate_query(raw: str) -> str:
    query = " ".join(raw.strip().split())
    if not query:
        raise HTTPException(422, "Enter a video topic before searching.")
    if len(query) > 300:
        raise HTTPException(422, "Keep the video search under 300 characters.")
    if BLOCKED.search(query):
        raise HTTPException(
            422,
            "OPENREELpy only searches lawful public-domain and open-access media. "
            "Remove piracy, DRM-bypass or unauthorised-copy terms.",
        )
    return query


def build_dork(query: str) -> str:
    clean = re.sub(r'["<>]', " ", query)
    clean = " ".join(clean.split())
    return (
        'site:archive.org/details (filetype:mp4 OR filetype:webm OR filetype:ogv) '
        f'"{clean}" ("public domain" OR "creative commons" OR "open access")'
    )


def build_archive_query(query: str) -> str:
    words = [re.sub(r"[^\w'-]", "", word) for word in query.split()]
    words = [word for word in words if word][:10]
    return "mediatype:movies AND (" + (" AND ".join(words) or "open media") + ")"


def as_text(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return "" if value is None else str(value)


def media_item(document: dict[str, Any]) -> dict[str, Any]:
    identifier = as_text(document.get("identifier"))
    return {
        "id": identifier,
        "title": as_text(document.get("title")) or identifier,
        "description": html.unescape(as_text(document.get("description"))),
        "year": as_text(document.get("year")),
        "creator": as_text(document.get("creator")),
        "downloads": int(document.get("downloads") or 0),
        "thumbnail": f"https://archive.org/services/img/{quote(identifier, safe='')}",
        "details_url": f"https://archive.org/details/{quote(identifier, safe='')}",
    }


def playable_files(metadata: dict[str, Any]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for item in metadata.get("files", []):
        name = as_text(item.get("name"))
        file_format = as_text(item.get("format"))
        if not name or item.get("private") is True:
            continue
        if re.search(r"thumb|sample|trailer", name, re.IGNORECASE):
            continue
        if not (name.lower().endswith(VIDEO_EXTENSIONS) or VIDEO_FORMAT.search(file_format)):
            continue
        selected.append(item)
    return sorted(selected, key=lambda item: int(item.get("size") or 0), reverse=True)


def media_url(identifier: str, name: str) -> str:
    safe_path = "/".join(quote(part, safe="") for part in name.split("/"))
    return f"https://archive.org/download/{quote(identifier, safe='')}/{safe_path}"


def media_mime(name: str) -> str:
    lower = name.lower()
    if lower.endswith(".webm"):
        return "video/webm"
    if lower.endswith(".ogv"):
        return "video/ogg"
    return "video/mp4"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def home() -> HTMLResponse:
    page = ROOT / "templates" / "index.html"
    if not page.is_file():
        raise HTTPException(503, "The application interface is unavailable.")
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "application": "OPENREELpy",
        "version": app.version,
        "runtime": "FastAPI",
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
    }


@app.post("/api/search")
async def search(request: SearchRequest) -> dict[str, Any]:
    query = validate_query(request.query)
    params: list[tuple[str, str]] = [
        ("q", build_archive_query(query)),
        ("rows", "24"),
        ("page", "1"),
        ("output", "json"),
        ("sort[]", "downloads desc"),
    ]
    params.extend(("fl[]", field) for field in (
        "identifier", "title", "description", "year", "creator", "downloads"
    ))
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0), follow_redirects=False) as client:
            response = await client.get(ARCHIVE_SEARCH, params=params)
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "The open-media index is temporarily unavailable.") from exc
    documents = payload.get("response", {}).get("docs", [])
    results = [media_item(document) for document in documents if document.get("identifier")]
    return {
        "query": query,
        "dork": build_dork(query),
        "google_url": "https://www.google.com/search?q=" + quote(build_dork(query), safe=""),
        "source": "Internet Archive",
        "count": len(results),
        "results": results,
    }


@app.get("/api/media/{identifier}")
async def resolve_media(
    identifier: str = ApiPath(min_length=1, max_length=160)
) -> dict[str, Any]:
    if not SAFE_IDENTIFIER.fullmatch(identifier):
        raise HTTPException(422, "Invalid media identifier.")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(12.0), follow_redirects=False) as client:
            response = await client.get(ARCHIVE_METADATA.format(identifier=identifier))
            response.raise_for_status()
            metadata = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Media metadata is temporarily unavailable.") from exc
    files = playable_files(metadata)
    if not files:
        raise HTTPException(404, "No directly playable open video file was verified.")
    selected = files[0]
    item_metadata = metadata.get("metadata", {})
    title = as_text(item_metadata.get("title")) or identifier
    return {
        "id": identifier,
        "title": title,
        "description": as_text(item_metadata.get("description")),
        "creator": as_text(item_metadata.get("creator")),
        "year": as_text(item_metadata.get("date"))[:4],
        "src": media_url(identifier, as_text(selected.get("name"))),
        "mime": media_mime(as_text(selected.get("name"))),
        "poster": f"https://archive.org/services/img/{quote(identifier, safe='')}",
        "details_url": f"https://archive.org/details/{quote(identifier, safe='')}",
        "file_name": as_text(selected.get("name")),
    }


@app.get("/docs/{document}", include_in_schema=False)
async def documentation(document: str) -> FileResponse:
    allowed = {
        "README.md", "README.pdf", "USER-GUIDE.md", "USER-GUIDE.pdf",
        "FUNCT-GUIDE.md", "FUNCT-GUIDE.pdf", "TESTS.md", "TESTS.pdf",
    }
    if document not in allowed:
        raise HTTPException(404, "Document not found.")
    path = ROOT / "docs" / document
    if not path.is_file():
        raise HTTPException(404, "Document not found.")
    return FileResponse(path)


# Avoid a cold-start import failure if a deployment bundle is incomplete. The
# deployment smoke test still verifies that these assets are actually present.
app.mount("/static", StaticFiles(directory=ROOT / "static", check_dir=False), name="static")
