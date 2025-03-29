import json
import requests
from bs4 import BeautifulSoup
import re
import time

# ✅ 网站主页
BASE_URL = "https://jino-lan.site/"
ALL_URLS = set()  # 存储所有文章 URL
media_entries = []  # 存储所有媒体资源
id_counter = 1  # 资源 ID 计数器

# ✅ 获取所有文章链接
def get_all_article_links():
    global ALL_URLS
    next_page = BASE_URL
    while next_page:
        print(f"🔍 Crawling: {next_page}")
        response = requests.get(next_page)
        soup = BeautifulSoup(response.text, 'html.parser')

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if "/?p=" in href and href.startswith(BASE_URL):
                ALL_URLS.add(href)

        next_btn = soup.find("a", string=re.compile("下一页|Next", re.IGNORECASE))
        next_page = next_btn["href"] if next_btn else None

        if next_page and not next_page.startswith("http"):
            next_page = BASE_URL + next_page

    print(f"✅ Found {len(ALL_URLS)} article URLs!")

# ✅ 爬取文章页面中的多媒体资源
def scrape_media_from_page(url):
    global id_counter
    print(f"📄 Scraping: {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    for media_block in soup.find_all("div", class_="wp-block-media-text"):
        text_elements = media_block.find_all(["figcaption"])
        text_lines = [el.get_text(strip=True) for el in text_elements if el.get_text(strip=True)]
        text_content = " ".join(text_lines) if text_lines else ""

        for figure in media_block.find_all("figure", class_="wp-block-audio"):
            audio_tag = figure.find("audio")
            if audio_tag and audio_tag.get("src"):
                audio_src = audio_tag["src"]
                print(f"[🎵 Audio] {audio_src} → {text_content}")
                media_entries.append({
                    "id": id_counter,
                    "type": "audio",
                    "file": audio_src,
                    "text": text_content,
                    "page": url
                })
                id_counter += 1

        for img_tag in media_block.find_all("img"):
            img_src = img_tag.get("src") or img_tag.get("data-src")
            if img_src:
                print(f"[✅ Image] {img_src} → {text_content}")
                media_entries.append({
                    "id": id_counter,
                    "type": "image",
                    "file": img_src,
                    "text": text_content,
                    "page": url
                })
                id_counter += 1

    for link in soup.find_all('a', href=True):
        href = link["href"]
        if re.search(r'\.(mp3|wav|ogg|m4a)$', href, re.IGNORECASE):
            desc = link.get_text(strip=True) or f"Audio {id_counter}"
            print(f"[🔗 Audio Link] {href} → {desc}")
            media_entries.append({
                "id": id_counter,
                "type": "audio",
                "file": href,
                "text": desc,
                "page": url
            })
            id_counter += 1

# ✅ 执行完整爬取任务
def crawl_all_pages(output_path="data/jino_all_media.json"):
    get_all_article_links()
    for article_url in ALL_URLS:
        scrape_media_from_page(article_url)
        time.sleep(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(media_entries, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Extracted {len(media_entries)} media entries across {len(ALL_URLS)} pages!")

# ✅ 独立运行入口
if __name__ == "__main__":
    crawl_all_pages()
