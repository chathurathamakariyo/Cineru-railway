import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper()

def clean_title(title: str):
    title = re.sub(r'\(\d{4}\)', '', title)
    title = title.split("|")[0]
    return title.replace("Sinhala Subtitles", "").strip()


def search(query: str):
    url = f"https://example.com/?s={query}"  # replace with allowed source
    res = scraper.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    results = []

    for article in soup.find_all("article"):
        a = article.find("a")
        if not a:
            continue

        results.append({
            "title": clean_title(a.text),
            "url": a.get("href")
        })

    return results


def info(url: str):
    res = scraper.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    return {
        "title": soup.find("h1").text.strip() if soup.find("h1") else None,
        "thumbnail": (soup.find("meta", property="og:image") or {}).get("content") if soup.find("meta", property="og:image") else None,
        "description": None
    }


def download(url: str):
    # ⚠️ placeholder only (no direct extraction logic here)
    return {
        "status": False,
        "message": "Download extractor not implemented in this template"
    }