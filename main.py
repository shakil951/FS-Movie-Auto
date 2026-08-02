import requests
import re

TARGET_URL = "https://fibwatch.art"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://fibwatch.art/"
}

def scrape_fibwatch():
    print("Fetching page from Fibwatch...")
    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"Failed to access site, status code: {response.status_code}")
            return

        # Regex দিয়ে Bunny CDN লিংকগুলো খুঁজে বের করা (.mkv / .mp4)
        cdn_links = re.findall(r'https?://[^\s"\']+\.b-cdn\.net/[^\s"\']+\.(?:mkv|mp4)', response.text)
        unique_links = list(set(cdn_links))
        print(f"Found {len(unique_links)} video streams!")

        # M3U প্লেলিস্ট ফাইলে সেভ করা
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n\n")
            
            for idx, link in enumerate(unique_links, 1):
                file_name = link.split('/')[-1]
                
                # আপনার স্ক্রিনশটের নিয়ম অনুযায়ী Referrer যোগ করা
                f.write("#EXTVLCOPT:http-referrer=https://fibwatch.art/\n")
                f.write(f'#EXTINF:-1 tvg-id="fib_{idx}", {file_name}\n')
                f.write(f"{link}\n\n")

        print("Playlist created successfully as 'playlist.m3u'!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    scrape_fibwatch()
