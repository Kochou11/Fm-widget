import requests
from PIL import Image, ImageDraw
from io import BytesIO

# API Endpoint for SFW anime portraits
API_URL = "https://api.waifu.pics/sfw/waifu"

# Standard headers to prevent CDN blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_random_waifu_url():
    response = requests.get(API_URL, headers=HEADERS).json()
    return response.get('url')

def create_card(img_url):
    print(f"Downloading image from: {img_url}")
    response = requests.get(img_url, headers=HEADERS, timeout=15)
    img = Image.open(BytesIO(response.content)).convert("RGBA")
    
    # Target card dimensions (Portrait)
    target_w, target_h = 400, 600
    w, h = img.size

    # --- SMART CROP LOGIC ---
    # This ensures the image is never stretched or skewed. 
    # It crops the center of the image to perfectly fill our 400x600 canvas.
    ratio = max(target_w / w, target_h / h)
    new_w, new_h = int(w * ratio), int(h * ratio)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    
    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    img = img.crop((left, top, left + target_w, top + target_h))

    # --- ADD AESTHETIC BORDER ---
    # Creates a sleek, dark border to make it look like a physical card
    border_size = 6
    border_color = (30, 30, 40, 255) # Dark AniList theme color
    
    final_canvas = Image.new('RGBA', (target_w + (border_size*2), target_h + (border_size*2)), border_color)
    final_canvas.paste(img, (border_size, border_size))

    # Save the final image
    final_canvas.save('waifu_card.png')
    print("Waifu card generated successfully!")

if __name__ == "__main__":
    url = get_random_waifu_url()
    if url:
        create_card(url)
    else:
        print("Failed to fetch URL from API.")
