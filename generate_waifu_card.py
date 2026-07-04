import os
import requests
import random
from PIL import Image
from io import BytesIO

# We can reuse your AniList secret if you want, or just leave it blank for general popular anime
USERNAME = os.environ.get('ANILIST_USERNAME', '')
API_URL = 'https://graphql.anilist.co'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_anilist_cover():
    print("Fetching random anime from AniList API...")
    
    # Pick a random page out of the top 1000 most popular anime
    random_page = random.randint(1, 40)
    
    query = '''
    query ($page: Int) {
      Page(page: $page, perPage: 25) {
        media(sort: POPULARITY_DESC, type: ANIME, isAdult: false) {
          coverImage { extraLarge }
          title { romaji }
        }
      }
    }
    '''
    
    try:
        response = requests.post(API_URL, json={'query': query, 'variables': {'page': random_page}}, headers=HEADERS, timeout=10).json()
        media_list = response.get('data', {}).get('Page', {}).get('media', [])
        
        if media_list:
            # Pick a random anime from that page and grab its cover
            random_media = random.choice(media_list)
            title = random_media.get('title', {}).get('romaji', 'Unknown')
            img_url = random_media.get('coverImage', {}).get('extraLarge')
            print(f"Selected anime: {title}")
            return img_url
    except Exception as e:
        print(f"AniList API Error: {e}")
        
    return None

def create_card(img_url):
    if not img_url:
        print("ERROR: Could not fetch image URL.")
        return False

    print(f"Downloading cover art...")
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"ERROR: Failed to download image: {e}")
        return False
        
    # Target card dimensions (Portrait)
    target_w, target_h = 400, 600
    w, h = img.size

    # --- SMART CROP LOGIC ---
    # AniList covers are usually portrait, but this ensures it perfectly fits 400x600
    ratio = max(target_w / w, target_h / h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    # --- ADD AESTHETIC BORDER ---
    border_size = 6
    border_color = (30, 30, 40, 255) # Dark AniList theme color
    
    final_canvas = Image.new('RGBA', (target_w + (border_size*2), target_h + (border_size*2)), border_color)
    final_canvas.paste(img, (border_size, border_size))

    # Save the final image
    final_canvas.save('waifu_card.png')
    print("Anime cover card generated successfully!")
    return True

if __name__ == "__main__":
    url = get_anilist_cover()
    success = create_card(url)
    
    if not success:
        print("Exiting without updating image to prevent breaking current card.")
