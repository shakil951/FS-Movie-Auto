import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

TARGET_CATEGORIES = {
    "https://fibwatch.art/videos/category/1": "Category 1",
    "https://fibwatch.art/videos/category/855": "Category 855",
    "https://fibwatch.art/videos/category/852": "Category 852",
    "https://fibwatch.art/videos/category/3/sub__845": "Bachelor Point"
}

scraper = cloudscraper.create_scraper()

def extract_cdn_links_from_html(html_text):
    """HTML, JavaScript Variable বা Embedded Code থেকে সব ভিডিও লিংক বের করা"""
    # ১. সরাসরি .b-cdn.net লিংক
    links = set(re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', html_text))
    
    # ২. যদি লিংকগুলো Escaped অবস্থায় থাকে (যেমন: https:\/\/...b-cdn.net\/...)
    escaped_links = re.findall(r'https?:\\/\\/[^\s"\']+\.b-cdn\.net\\/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', html_text)
    for el in escaped_links:
        links.add(el.replace('\\/', '/'))
        
    return links

def scrape_categories():
    print("Starting deep extraction for Bachelor Point & target categories...")
    all_cdn_links = set()

    for cat_url, cat_name in TARGET_CATEGORIES.items():
        print(f"\n--- Processing Category: {cat_name} ({cat_url}) ---")
        post_urls = set()

        try:
            res = scraper.get(cat_url, timeout=20)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # ক্যাটাগরি পেজের সব ভিডিও ও পর্বের (Episode) পোস্টের লিংক বের করা
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(cat_url, href)
                    
                    # Fibwatch-এর ভিডিও লিংক ফিল্টার
                    if "/video/" in full_url or "/watch/" in full_url or "/embed/" in full_url:
                        post_urls.add(full_url)
                        
            print(f"Found {len(post_urls)} video posts in {cat_name}")
        except Exception as e:
            print(f"Error fetching category page {cat_url}: {e}")
            continue

        # প্রতিটি ভিডিও পেজে ঢোকা
        for idx, post_url in enumerate(post_urls, 1):
            try:
                print(f"[{cat_name}] Extracting [{idx}/{len(post_urls)}]: {post_url}")
                page_res = scraper.get(post_url, timeout=15)
                
                # ১. মেইন পেজ থেকে লিংক খোঁজা
                found_links = extract_cdn_links_from_html(page_res.text)
                
                # ২. যদি মেইন পেজে লিংক না পাওয়া যায়, তবে iFrame/Player লিংক খুঁজে সেটির ভেতরে ঢোকা
                if not found_links:
                    soup = BeautifulSoup(page_res.text, 'html.parser')
                    for iframe in soup.find_all(['iframe', 'embed'], src=True):
                        iframe_src = urljoin(post_url, iframe['src'])
                        try:
                            iframe_res = scraper.get(iframe_src, timeout=10)
                            found_links.update(extract_cdn_links_from_html(iframe_res.text))
                        except Exception:
                            continue

                for link in found_links:
                    all_cdn_links.add((link, cat_name))
            except Exception:
                continue

    print(f"\n==========================================")
    print(f"SUCCESS: Total CDN Video Links Found: {len(all_cdn_links)}")
    print(f"==========================================")

    # M3U প্লেলিস্ট ফাইল তৈরি
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        
        for idx, (link, cat_name) in enumerate(sorted(all_cdn_links, key=lambda x: x[1]), 1):
            file_name = link.split('/')[-1]
            
            f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
            f.write(f'#EXTINF:-1 tvg-id="fib_{idx}" group-title="{cat_name}", {file_name}\n')
            f.write(f"{link}\n\n")

    print("Targeted Playlist generated successfully!")

if __name__ == "__main__":
    scrape_categories()
