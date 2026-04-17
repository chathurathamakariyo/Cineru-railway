from fastapi import FastAPI
from scraper import search_cineru, scrape_movie, get_download_links

app = FastAPI()

@app.get("/")
def root(q: str = None, info: str = None, dl: str = None):

    # 🔍 SEARCH
    if q:
        return {
            "status": True,
            "query": q,
            "results": search_cineru(q)
        }

    # 🎬 INFO
    if info:
        return {
            "status": True,
            "data": scrape_movie(info)
        }

    # ⬇️ DOWNLOAD
    if dl:
        return {
            "status": True,
            "links": get_download_links(dl)
        }

    return {
        "status": True,
        "message": "API running",
        "usage": {
            "search": "/?q=2026",
            "info": "/?info=url",
            "download": "/?dl=url"
        }
    }