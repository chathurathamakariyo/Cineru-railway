from fastapi import FastAPI, Query
from scraper import search_cineru, scrape_movie_details, extract_download_links

app = FastAPI()

@app.get("/")
def home(
    q: str = None,
    info: str = None,
    dl: str = None
):

    # 🔍 Search
    if q:
        return {
            "status": "success",
            "results": search_cineru(q)
        }

    # 🎬 Movie info
    if info:
        return {
            "status": "success",
            "data": scrape_movie_details(info)
        }

    # ⬇️ Download links
    if dl:
        return {
            "status": "success",
            "links": extract_download_links(dl)
        }

    return {
        "status": "running",
        "message": "Use ?q=, ?info=, ?dl="
    }