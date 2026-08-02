import cloudscraper
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

TARGET_URL = "https://fibwatch.art"

scraper = cloudscraper.create_scraper()

def scrape_fibwatch():
    print("Fetching home page from Fibwatch...")
    try:
        response = scraper.get(TARGET_URL, timeout=30)
        if response.status_code != 200:
            print(f"Failed to access site, status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ১. ওয়েবসাইটের সব অভ্যন্তরীণ লিঙ্ক (Posts & Pages) সংগ্রহ করা
        post_links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            # শুধুমাত্র Fibwatch-এর নিজস্ব লিংকে ফিল্টার করা
            if not href.startswith('mailto:') and not href.startswith('javascript:'):
                full_url = urljoin(TARGET_URL, href)
                if "fibwatch.art" in full_url:
                    post_links.add(full_url)

        print(f"Found {len(post_links)} links/pages to scan.")

        cdn_links = set()

        # ২. সাইটের সব পেজ ভিজিট করে ভিডিও লিংক খোঁজা
        for idx, page_url in enumerate(post_links, 1):
            try:
                print(f"Scanning [{idx}/{len(post_links)}]: {page_url}")
                page_res = scraper.get(page_url, timeout=15)
                
                # Regex আপডেট করা হয়েছে (.mkv, .mp4, .m3u8 সহ অন্যান্য স্ট্রিম ফরম্যাট খোঁজার জন্য)
                found = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4|m3u8|avi|mov|webm)', page_res.text)
                
                for link in found:
                    cdn_links.add(link)
            except Exception as ex:
                continue

        print(f"\nTotal Unique Video Streams Found: {len(cdn_links)}")

        # ৩. M3U প্লেলিস্ট ফাইলে সেভ করা
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            
            for idx, link in enumerate(sorted(cdn_links), 1):
                # ইউআরএল থেকে ক্লিন নাম বের করা
                file_name = link.split('/')[-1]
                
                f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
                f.write(f'#EXTINF:-1 tvg-id="fib_{idx}", {file_name}\n')
                f.write(f"{link}\n\n")

        print("Playlist updated with ALL found links successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_fibwatch()
