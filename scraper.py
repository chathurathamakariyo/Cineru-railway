import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper(
    browser={
        "browser": "chrome",
        "platform": "windows",
        "mobile": False
    }
)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122 Safari/537.36",
    "Referer": "https://cineru.lk/",
    "Accept-Language": "en-US,en;q=0.9"
}

# 🎬 clean title
def process_title(title):
    title = re.sub(r'\(\d{4}\)', '', title)
    title = title.split("|")[0]
    return title.replace("Sinhala Subtitles", "").strip()


# 🖼️ thumbnail
def get_thumbnail(url):
    try:
        res = scraper.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        og = soup.find("meta", property="og:image")
        return og["content"] if og else None
    except:
        return None


# 🔍 search (PRO FIX)
def search_cineru(query):
    results = []

    for page in range(1, 3):
        url = f"https://cineru.lk/page/{page}/?s={query}"

        try:
            res = scraper.get(url, headers=HEADERS, timeout=20)
            html = res.text

            # ❗ DEBUG fallback (important)
            if "Just a moment" in html or len(html) < 500:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 🔥 multiple selectors fallback
            items = soup.select("article, div.post, div.blog-item")

            for item in items:
                a = item.find("a")
                if not a:
                    continue

                link = a.get("href")
                title = a.get_text(strip=True)

                if not link:
                    continue

                results.append({
                    "title": process_title(title),
                    "url": link,
                    "thumbnail": get_thumbnail(link)
                })

        except Exception as e:
            print("Search error:", e)
            continue

    return results


# 🎬 info scraper
def scrape_movie(url):
    try:
        res = scraper.get(url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(res.text, "html.parser")

        h1 = soup.find("h1")
        raw = h1.text.strip() if h1 else ""

        title = process_title(raw)
        year = re.search(r'(\d{4})', raw)
        year = year.group(1) if year else None

        og = soup.find("meta", property="og:image")
        thumb = og["content"] if og else None

        content = soup.select_one("div.entry-content, article")

        desc = None
        info = {}

        if content:
            for p in content.find_all(["p", "li"]):
                text = p.get_text(" ", strip=True)

                if not desc and len(text) > 80:
                    desc = text

                if ":" in text:
                    k, v = text.split(":", 1)
                    info[k.strip()] = v.strip()

        return {
            "title": title,
            "year": year,
            "thumbnail": thumb,
            "description": desc,
            "info": info
        }

    except Exception as e:
        return {"error": str(e)}


# ⬇️ download extractor
def get_download_links(post_id):
    try:
        res = scraper.post(
            "https://cineru.lk/wp-admin/admin-ajax.php",
            data={"action": "cs_download_data", "post_id": post_id},
            headers=HEADERS,
            timeout=20
        )

        data = res.json()
        html = data.get("data", "")

        links = re.findall(
            r'data-link="(https://dl\.cineru\.lk/dl\.php\?token=[^"]+)"',
            html
        )

        return list(dict.fromkeys(links))

    except:
        return []