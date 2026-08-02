import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# আপনার নির্দিষ্ট ক্যাটাগরি ইউআরএলগুলো
TARGET_CATEGORIES = {
    "https://fibwatch.art/videos/category/1": "Category 1",
    "https://fibwatch.art/videos/category/855": "Category 855",
    "https://fibwatch.art/videos/category/852": "Category 852",
    "https://fibwatch.art/videos/category/3/sub__845": "Category 3 - Sub 845"
}

scraper = cloudscraper.create_scraper()

def scrape_categories():
    print("Starting category-specific video extraction...")
    
    # (video_link, category_name)
    all_cdn_links = set()

    for cat_url, cat_name in TARGET_CATEGORIES.items():
        print(f"\n--- Processing Category: {cat_name} ({cat_url}) ---")
        post_urls = set()

        # ১. ক্যাটাগরি পেজে গিয়ে সব ভিডিও পোস্টের ইউআরএল বের করা
        try:
            res = scraper.get(cat_url, timeout=20)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                # ক্যাটাগরি পেজের প্রতিটি ভিডিও কার্ডের লিংক খোঁজা
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(cat_url, href)
                    
                    # Fibwatch-এর মূল ভিডিও পেজের প্যাটার্ন ফিল্টার করা
                    if "fibwatch.art/video/" in full_url or "fibwatch.art/watch/" in full_url:
                        post_urls.add(full_url)
                        
            print(f"Found {len(post_urls)} video posts in {cat_name}")
        except Exception as e:
            print(f"Error fetching category page {cat_url}: {e}")
            continue

        # ২. প্রতিটি ভিডিও পোস্টের ভেতরে ঢুকে আসল CDN লিংক বের করা
        for idx, post_url in enumerate(post_urls, 1):
            try:
                print(f"[{cat_name}] Extracting [{idx}/{len(post_urls)}]: {post_url}")
                page_res = scraper.get(post_url, timeout=15)
                
                # .b-cdn.net ভিডিও ফাইলের আসল স্ট্রিম লিংক খোঁজা (.mp3 ছাড়া)
                found = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', page_res.text)
                
                for link in found:
                    all_cdn_links.add((link, cat_name))
            except Exception:
                continue

    print(f"\n==========================================")
    print(f"SUCCESS: Total CDN Video Links Found: {len(all_cdn_links)}")
    print(f"==========================================")

    # ৩. M3U প্লেলিস্ট ফাইলে সেভ করা
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
