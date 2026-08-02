import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

TARGET_URL = "https://fibwatch.art"
scraper = cloudscraper.create_scraper()

# স্ক্রিনশট অনুযায়ী ওয়েবসাইটের মূল সেকশন বা ক্যাটাগরি লিংকগুলো
SECTIONS = [
    "https://fibwatch.art/videos/latest",
    "https://fibwatch.art/videos/trending",
    "https://fibwatch.art/videos/top",
    "https://fibwatch.art/categories"
]

def get_category_name(link):
    """লিংকের নাম দেখে M3U ফোল্ডার বা ক্যাটাগরি নির্ধারণ"""
    link_lower = link.lower()
    if "s0" in link_lower or "e0" in link_lower or "season" in link_lower or "episode" in link_lower:
        return "Web Series & Shows"
    elif "1080p" in link_lower or "720p" in link_lower or "bluray" in link_lower:
        return "Movies"
    else:
        return "General Content"

def scrape_fibwatch():
    print("Starting deep scan for ALL videos...")
    all_pages_to_scan = set()

    # ১. হোমপেজ এবং সাইডবারের প্রধান সেকশনগুলো থেকে লিংক যোগ করা
    all_pages_to_scan.add(TARGET_URL)
    for section in SECTIONS:
        all_pages_to_scan.add(section)

    try:
        # ২. প্রধান পেজগুলো থেকে ক্যাটাগরি ও ভিডিও পোস্টের পেজ ইউআরএল সংগ্রহ করা
        for url in list(all_pages_to_scan):
            try:
                res = scraper.get(url, timeout=15)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if not href.startswith(('javascript:', 'mailto:', '#')):
                            full_url = urljoin(TARGET_URL, href)
                            if "fibwatch.art" in full_url:
                                all_pages_to_scan.add(full_url)
            except Exception:
                continue

        print(f"Total target pages found to scan: {len(all_pages_to_scan)}")

        cdn_links = set()

        # ৩. সংগ্রহ করা প্রতিটি পেজ ভিজিট করে Bunny CDN ভিডিও লিংক ফিল্টার করা
        for idx, page_url in enumerate(all_pages_to_scan, 1):
            try:
                print(f"Scanning [{idx}/{len(all_pages_to_scan)}]: {page_url}")
                page_res = scraper.get(page_url, timeout=15)
                
                # Regex দিয়ে .b-cdn.net ফাইল লিংক (.mkv, .mp4, .m3u8) খোঁজা
                found = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', page_res.text)
                for link in found:
                    cdn_links.add(link)
            except Exception:
                continue

        print(f"\n==========================================")
        print(f"SUCCESS: Total Unique Video Links Found: {len(cdn_links)}")
        print(f"==========================================")

        # ৪. ক্যাটাগরিসহ M3U প্লেলিস্ট ফাইলে সেভ করা
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            
            for idx, link in enumerate(sorted(cdn_links), 1):
                file_name = link.split('/')[-1]
                category = get_category_name(file_name)
                
                f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
                f.write(f'#EXTINF:-1 tvg-id="fib_{idx}" group-title="{category}", {file_name}\n')
                f.write(f"{link}\n\n")

        print("Playlist created successfully with ALL video links!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_fibwatch()
