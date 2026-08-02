import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

# আপনার নির্দিষ্ট ক্যাটাগরি ইউআরএলগুলোর তালিকা
TARGET_CATEGORIES = [
    "https://fibwatch.art/videos/category/1",
    "https://fibwatch.art/videos/category/855",
    "https://fibwatch.art/videos/category/852",
    "https://fibwatch.art/videos/category/3/sub__845"
]

scraper = cloudscraper.create_scraper()

def get_category_title(url):
    """ইউআরএল আইডি অনুযায়ী প্লেলিস্টে ক্যাটাগরির নাম দেওয়া"""
    if "/category/1" in url:
        return "Category 1"
    elif "/category/855" in url:
        return "Category 855"
    elif "/category/852" in url:
        return "Category 852"
    elif "/sub__845" in url:
        return "Category 3 - Sub 845"
    else:
        return "Custom Category"

def scrape_specific_categories():
    print("Starting targeted scan for specified categories...")
    
    # (link, category_name)
    all_cdn_links = set()
    pages_to_scan = set()

    # ১. প্রতিটি নির্দিষ্ট ক্যাটাগরি পেজের প্রথম কয়েক পেজ ও সাব-লিংক বের করা
    for cat_url in TARGET_CATEGORIES:
        cat_name = get_category_title(cat_url)
        pages_to_scan.add((cat_url, cat_name))
        
        # পেজিনেশন সাপোর্ট (যেমন: ?page=1, ?page=2 ইত্যাদি ফিল্টার করার জন্য)
        try:
            res = scraper.get(cat_url, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(cat_url, href)
                    # শুধুমাত্র ওই ক্যাটাগরির ভেতরের পোস্ট/ভিডিও বা পেজের লিংক নেয়া
                    if cat_url in full_url or ("page=" in full_url and "/category/" in full_url):
                        pages_to_scan.add((full_url, cat_name))
        except Exception:
            continue

    print(f"Total target pages to scan: {len(pages_to_scan)}")

    # ২. পেজগুলো স্ক্যান করে Bunny CDN ভিডিও লিংক বের করা
    for idx, (page_url, cat_name) in enumerate(pages_to_scan, 1):
        try:
            print(f"Scanning [{idx}/{len(pages_to_scan)}]: {page_url}")
            page_res = scraper.get(page_url, timeout=15)
            
            # .b-cdn.net ভিডিও ফাইলের লিংক খোঁজা (.mp3 ছাড়া)
            found_links = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', page_res.text)
            
            for link in found_links:
                all_cdn_links.add((link, cat_name))
        except Exception:
            continue

    print(f"\n==========================================")
    print(f"SUCCESS: Total Video Links Found: {len(all_cdn_links)}")
    print(f"==========================================")

    # ৩. M3U প্লেলিস্ট তৈরি করা
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        
        for idx, (link, cat_name) in enumerate(sorted(all_cdn_links, key=lambda x: x[1]), 1):
            file_name = link.split('/')[-1]
            
            f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
            f.write(f'#EXTINF:-1 tvg-id="fib_{idx}" group-title="{cat_name}", {file_name}\n')
            f.write(f"{link}\n\n")

    print("Targeted Playlist created successfully!")

if __name__ == "__main__":
    scrape_specific_categories()
