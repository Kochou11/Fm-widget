import requests
from PIL import Image
from io import BytesIO

# Headers to prevent CDN blocking
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_random_image_url():
    # API 1: Waifu.pics
    try:
        print("Trying Waifu.pics API...")
        response = requests.get("https://api.waifu.pics/sfw/waifu", headers=HEADERS, timeout=10).json()
        return response.get('url')
    except Exception as e:
        print(f"Waifu.pics failed: {e}")

    # API 2: Nekos.best (Fallback)
    try:
        print("Trying Nekos.best API as fallback...")
        response = requests.get("https://api.nekos.best/api/v2/neko?amount=1", headers=HEADERS, timeout=10).json()
        if response.get('results'):
            return response['results'][0].get('url')
    except Exception as e:
        print(f"Nekos.best failed: {e}")

    return None

def create_card(img_url):
    if not img_url:
        print("ERROR: Could not fetch image URL from any API.")
        return False

    print(f"Downloading image from: {img_url}")
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=15)
        img = Image.open(BytesIO(response.content)).convert("RGBA")
    except Exception as e:
        print(f"ERROR: Failed to download image file: {e}")
        return False
        
    # Target card dimensions (Portrait)
    target_w, target_h = 400, 600
    w, h = img.size

    # --- SMART CROP LOGIC ---
    # Crops the center of the image to perfectly fill the canvas without stretching
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
    print("Waifu card generated successfully!")
    return True

if __name__ == "__main__":
    url = get_random_image_url()
    success = create_card(url)
    
    if not success:
        print("Exiting without updating image to prevent breaking current card.")
