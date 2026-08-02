import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

BASE_LATEST_URL = "https://fibwatch.art/videos/latest"
scraper = cloudscraper.create_scraper()

def extract_cdn_links_from_html(html_text):
    """HTML বা Escaped JavaScript কোড থেকে সব ভিডিও লিংক বের করা"""
    links = set(re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', html_text))
    
    # Escaped URL (\/) হ্যান্ডেল করা
    escaped_links = re.findall(r'https?:\\/\\/[^\s"\']+\.b-cdn\.net\\/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', html_text)
    for el in escaped_links:
        links.add(el.replace('\\/', '/'))
        
    return links

def scrape_all_latest_videos():
    print("Starting scraping for ALL Latest videos...")
    
    video_post_urls = set()
    pages_to_visit = set()
    
    # ১. Latest-এর প্রথম কয়েক পেজের ইউআরএল স্ট্রাকচার রেডি করা (যেমন: page=1, page=2...)
    pages_to_visit.add(BASE_LATEST_URL)
    for page_num in range(1, 15): # প্রয়োজন অনুযায়ী কত পেজ পর্যন্ত যাবেন তা সেট করা আছে
        pages_to_visit.add(f"{BASE_LATEST_URL}?page={page_num}")

    # ২. Latest-এর প্রতিটি পেজ থেকে ভিডিও পোস্টের মূল ইউআরএলগুলো সংগ্রহ করা
    for page_url in sorted(pages_to_visit):
        try:
            print(f"Fetching Latest Catalog Page: {page_url}")
            res = scraper.get(page_url, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                
                for a in soup.find_all('a', href=True):
                    href = a['href']
                    full_url = urljoin(BASE_LATEST_URL, href)
                    
                    # ভিডিও পেজের প্যাটার্ন ফিল্টার
                    if "/video/" in full_url or "/watch/" in full_url or "/embed/" in full_url:
                        video_post_urls.add(full_url)
        except Exception as e:
            print(f"Error reading catalog page {page_url}: {e}")

    print(f"\nTotal Unique Video Posts Found in Latest: {len(video_post_urls)}")

    all_cdn_links = set()

    # ৩. প্রতিটি ভিডিও পোস্টের ভেতরে ঢুকে আসল CDN লিংক বের করা
    for idx, post_url in enumerate(list(video_post_urls), 1):
        try:
            print(f"Extracting [{idx}/{len(video_post_urls)}]: {post_url}")
            page_res = scraper.get(post_url, timeout=15)
            
            # মেইন পেজ থেকে লিংক ফিল্টার
            found_links = extract_cdn_links_from_html(page_res.text)
            
            # পেজে লিংক না থাকলে iFrame/Player থেকে লিংক ফিল্টার করা
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
                all_cdn_links.add(link)
        except Exception:
            continue

    print(f"\n==========================================")
    print(f"SUCCESS: Total Latest Direct Video Links: {len(all_cdn_links)}")
    print(f"==========================================")

    # ৪. M3U প্লেলিস্ট তৈরি
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")
        
        for idx, link in enumerate(sorted(all_cdn_links), 1):
            file_name = link.split('/')[-1]
            
            f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
            f.write(f'#EXTINF:-1 tvg-id="latest_{idx}" group-title="Latest Content", {file_name}\n')
            f.write(f"{link}\n\n")

    print("Latest Playlist generated successfully!")

if __name__ == "__main__":
    scrape_all_latest_videos()
