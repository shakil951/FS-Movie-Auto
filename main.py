import cloudscraper
from bs4 import BeautifulSoup
import re

TARGET_URL = "https://fibwatch.art"

# Cloudflare বাইপাস করার জন্য cloudscraper ব্যবহার
scraper = cloudscraper.create_scraper()

def scrape_fibwatch():
    print("Fetching home page from Fibwatch...")
    try:
        response = scraper.get(TARGET_URL, timeout=30)
        if response.status_code != 200:
            print(f"Failed to access site, status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ১. হোমপেজে থাকা সব পোস্টের/মুভির লিংক খুঁজে বের করা
        post_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # Fibwatch-এর পোস্টের ইউআরএল স্ট্রাকচার ফিল্টার করা
            if TARGET_URL in href or href.startswith('/'):
                full_url = href if href.startswith('http') else f"{TARGET_URL}{href}"
                post_links.add(full_url)

        print(f"Found {len(post_links)} pages/posts to scan.")

        cdn_links = set()

        # ২. প্রথম ১৫-২০টি পোস্টের ভেতরে ঢুকে .b-cdn.net ভিডিও লিংক বের করা
        for idx, page_url in enumerate(list(post_links)[:20], 1):
            try:
                print(f"Scanning [{idx}]: {page_url}")
                page_res = scraper.get(page_url, timeout=15)
                
                # Regex দিয়ে .b-cdn.net ভিডিও লিংক (.mkv/.mp4) খোঁজা
                found = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4)', page_res.text)
                for link in found:
                    cdn_links.add(link)
            except Exception as ex:
                continue

        print(f"Total Unique Video Streams Found: {len(cdn_links)}")

        # ৩. M3U ফাইল তৈরি করা
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            
            for idx, link in enumerate(cdn_links, 1):
                # ফাইল নাম বের করা
                file_name = link.split('/')[-1]
                
                f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
                f.write(f'#EXTINF:-1 tvg-id="fib_{idx}", {file_name}\n')
                f.write(f"{link}\n\n")

        print("Playlist created successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_fibwatch()
