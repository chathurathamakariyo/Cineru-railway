from fastapi import FastAPI, Query
import scraper as scr

app = FastAPI(title="Chathura API")

# 🔎 SEARCH
@app.get("/")
def root(q: str = Query(None), info: str = Query(None), dl: str = Query(None)):

    if q:
        return {
            "status": True,
            "query": q,
            "results": scr.search(q)
        }

    if info:
        return {
            "status": True,
            "data": scr.info(info)
        }

    if dl:
        return scr.download(dl)

    return {
        "status": True,
        "message": "Use ?q=search OR ?info=url OR ?dl=url"
    }