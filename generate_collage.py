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
                img_url = img_url.replace('\\/', '/')
                img_url = img_url.replace('-80-', '-100-')
                return img_url
    except Exception as e:
        print(f"Deezer error for {artist_name}: {e}")
        
    return None

def create_collage(artist_names):
    # 1200x1200 canvas (400px per square)
    collage = Image.new('RGB', (1200, 1200), (30, 30, 30)) 
    size = 400

    # --- BULLETPROOF FONT LOADING FOR GITHUB SERVERS ---
    font = None
    # Try common Linux fonts found on GitHub Actions (Ubuntu)
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    
    for path in font_paths:
        try:
            # Size 28 is big, bold, and very readable on a 400px square
            font = ImageFont.truetype(path, 28)
            break
        except:
            continue
            
    if not font:
        # Ultimate fallback if Linux fonts are missing (rare)
        try:
            font = ImageFont.load_default(size=28)
        except TypeError:
            font = ImageFont.load_default()
    # ---------------------------------------------------

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
                
                # Add Text Overlay
                draw = ImageDraw.Draw(img)
                text_position = (15, 355) 
                
                # Draw text with a thick black outline for perfect readability
                draw.text(
                    text_position, 
                    artist_name, 
                    fill="white", 
                    font=font, 
                    stroke_width=3, 
                    stroke_fill="black"
                )
                
                collage.paste(img, (x, y))
                print(f"  -> Success with bold text!")
            except Exception as e:
                print(f"  -> Error: {e}")
        else:
            print(f"  -> Not found on Deezer.")

    collage.save('lastfm_monthly.png')
    print("\nHD Collage with bold names saved!")

if __name__ == "__main__":
    artist_names = get_monthly_artist_names()
    if len(artist_names) > 0:
        print(f"--- Found {len(artist_names)} artists from Last.fm ---")
        create_collage(artist_names)
    else:
        print("No artists found for this month.")
