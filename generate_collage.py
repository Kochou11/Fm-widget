import os
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Get Last.fm secrets from GitHub environment
API_KEY = os.environ['LASTFM_API_KEY']
USERNAME = os.environ['LASTFM_USERNAME']

def get_monthly_artist_names():
    # Only fetch the names from Last.fm (ignore Last.fm images entirely)
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={USERNAME}&period=1month&api_key={API_KEY}&format=json&limit=9"
    response = requests.get(url).json()
    
    names = [artist['name'] for artist in response['topartists']['artist']]
    return names[:9]

def get_artist_image_from_deezer(artist_name):
    # Use Deezer API to get the artist image (No API key needed!)
    try:
        # Safely encode the artist name for the URL (handles spaces & special characters)
        safe_name = requests.utils.quote(artist_name)
        search_url = f"https://api.deezer.com/search/artist?q={safe_name}&limit=1"
        
        response = requests.get(search_url, timeout=10).json()
        
        # If Deezer found the artist, grab their high-quality square picture
        if response.get('data') and len(response['data']) > 0:
            return response['data'][0].get('picture_big')
    except Exception as e:
        print(f"Deezer lookup failed for {artist_name}: {e}")
        
    return None

def create_collage(artist_names):
    # Create a blank 3x3 canvas (300x300 pixels)
    collage = Image.new('RGB', (300, 300), (30, 30, 30)) 
    size = 100
    
    # Try to load a nice font, fallback to default if not available on the server
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    for i, artist_name in enumerate(artist_names):
        x = (i % 3) * size
        y = (i // 3) * size
        
        print(f"Processing {i+1}/9: {artist_name}")
        img_url = get_artist_image_from_deezer(artist_name)
        
        if img_url:
            try:
                print(f"  -> Downloading image from Deezer...")
                img_response = requests.get(img_url, timeout=10)
                img = Image.open(BytesIO(img_response.content))
                img = img.resize((size, size), Image.LANCZOS)
                collage.paste(img, (x, y))
                print(f"  -> Success!")
            except Exception as e:
                print(f"  -> Failed to download image. Falling back to text.")
                draw = ImageDraw.Draw(collage)
                draw.text((10, 40), artist_name, fill='white', font=font)
        else:
            print(f"  -> Not found on Deezer. Falling back to text.")
            # If no image is found anywhere, draw the artist name instead
            draw = ImageDraw.Draw(collage)
            draw.text((10, 40), artist_name, fill='white', font=font)

    collage.save('lastfm_monthly.png')
    print("\nCollage saved successfully!")

if __name__ == "__main__":
    artist_names = get_monthly_artist_names()
    if len(artist_names) > 0:
        print(f"--- Found {len(artist_names)} artists from Last.fm ---")
        create_collage(artist_names)
    else:
        print("No artists found for this month.")
