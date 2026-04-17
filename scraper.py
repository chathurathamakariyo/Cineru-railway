import cloudscraper
from bs4 import BeautifulSoup
import re

scraper = cloudscraper.create_scraper()

def process_title(raw_title):
    title = re.sub(r'\(\d{4}\)', '', raw_title)
    title = re.split(r'\|', title)[0]
    title = title.replace("Sinhala Subtitles", "")
    return title.strip()


def get_thumbnail(url):
    res = scraper.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    og = soup.find("meta", property="og:image")
    return og.get("content") if og else None


def search_cineru(query):
    results = []

    for page in range(1, 3):
        url = f"https://cineru.lk/page/{page}/?s={query}" if page > 1 else f"https://cineru.lk/?s={query}"

        res = scraper.get(url)
        soup = BeautifulSoup(res.text, "html.parser")

        articles = soup.find_all("article")

        for article in articles:
            a = article.find("a")
            if not a:
                continue

            title = process_title(a.text.strip())
            link = a.get("href")
            thumb = get_thumbnail(link)

            results.append({
                "title": title,
                "url": link,
                "thumbnail": thumb
            })

    return results


def scrape_movie_details(url):
    res = scraper.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    h1 = soup.find("h1")
    raw_title = h1.text.strip() if h1 else ""

    title = re.sub(r'\(\d{4}\)', '', raw_title)
    title = re.split(r'\|', title)[0].replace("Sinhala Subtitles", "").strip()

    year = re.search(r'(\d{4})', raw_title)
    year = year.group(1) if year else None

    og = soup.find("meta", property="og:image")
    thumbnail = og["content"] if og else None

    content = soup.select_one("div.entry-content, article")

    description = None
    info = {}

    if content:
        paragraphs = content.find_all(["p", "li"])

        for p in paragraphs:
            text = p.get_text(" ", strip=True)

            if not description and len(text) > 80:
                description = text

            if ":" in text:
                k, v = text.split(":", 1)
                info[k.strip()] = v.strip()

    return {
        "title": title,
        "year": year,
        "thumbnail": thumbnail,
        "description": description,
        "info": info
    }


def extract_download_links(post_id):
    res = scraper.post(
        "https://cineru.lk/wp-admin/admin-ajax.php",
        data={"action": "cs_download_data", "post_id": post_id}
    )

    if res.status_code != 200:
        return []

    result = res.json()
    html = result.get("data", "")

    links = re.findall(r'data-link="(https://dl\.cineru\.lk/dl\.php\?token=[^"]+)"', html)

    return list(dict.fromkeys(links))