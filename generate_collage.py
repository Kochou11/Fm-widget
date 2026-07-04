import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Get Last.fm secrets
API_KEY = os.environ['LASTFM_API_KEY']
USERNAME = os.environ['LASTFM_USERNAME']

# User-Agent prevents Deezer from blocking the download
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

def get_monthly_artist_names():
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={USERNAME}&period=1month&api_key={API_KEY}&format=json&limit=9"
    response = requests.get(url).json()
    return [artist['name'] for artist in response['topartists']['artist']][:9]

def get_artist_image_from_deezer(artist_name):
    try:
        safe_name = requests.utils.quote(artist_name)
        search_url = f"https://api.deezer.com/search/artist?q={safe_name}&limit=1"
        
        response = requests.get(search_url, headers=HEADERS, timeout=10).json()
        
        if response.get('data') and len(response['data']) > 0:
            img_url = response['data'][0].get('picture_xl')
            
            if img_url:
                # Filter out the escaped slashes
                img_url = img_url.replace('\\/', '/')
                # Force 100% lossless quality
                img_url = img_url.replace('-80-', '-100-')
                return img_url
    except Exception as e:
        print(f"Deezer error for {artist_name}: {e}")
        
    return None

def create_collage(artist_names):
    # 1200x1200 canvas (400px per square) for ultra-crisp phone screens
    collage = Image.new('RGB', (1200, 1200), (30, 30, 30)) 
    size = 400

    # Try to load a clean font. Size 24 is small but very readable at 400px scale.
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()

    for i, artist_name in enumerate(artist_names):
        x = (i % 3) * size
        y = (i // 3) * size
        
        print(f"Processing {i+1}/9: {artist_name}")
        img_url = get_artist_image_from_deezer(artist_name)
        
        if img_url:
            try:
                img_response = requests.get(img_url, headers=HEADERS, timeout=10)
                img = Image.open(BytesIO(img_response.content))
                img = img.resize((size, size), Image.LANCZOS)
                
                # --- NEW: ADD TEXT OVERLAY ---
                draw = ImageDraw.Draw(img)
                # Position: 15px from left, 360px from top (places it nicely at the bottom)
                text_position = (15, 360) 
                
                # Draw the text: White fill with a 2px black outline for perfect readability
                draw.text(
                    text_position, 
                    artist_name, 
                    fill="white", 
                    font=font, 
                    stroke_width=2, 
                    stroke_fill="black"
                )
                # ------------------------------
                
                collage.paste(img, (x, y))
                print(f"  -> Ultra-HD Success with text!")
            except Exception as e:
                print(f"  -> Failed to download.")
        else:
            print(f"  -> Not found on Deezer.")

    # Save the final image
    collage.save('lastfm_monthly.png')
    print("\nUltra-HD Collage with names saved successfully!")

if __name__ == "__main__":
    artist_names = get_monthly_artist_names()
    if len(artist_names) > 0:
        print(f"--- Found {len(artist_names)} artists from Last.fm ---")
        create_collage(artist_names)
    else:
        print("No artists found for this month.")
