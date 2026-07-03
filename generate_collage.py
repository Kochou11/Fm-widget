import os
import requests
from PIL import Image
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
            # CHANGED: Use 'picture_xl' for 1000x1000 HD quality!
            img_url = response['data'][0].get('picture_xl')
            
            if img_url:
                # Filter out the escaped slashes
                img_url = img_url.replace('\\/', '/')
                return img_url
    except Exception as e:
        print(f"Deezer error for {artist_name}: {e}")
        
    return None

def create_collage(artist_names):
    # CHANGED: Canvas is now 900x900 pixels (HD size)
    collage = Image.new('RGB', (900, 900), (30, 30, 30)) 
    # CHANGED: Each square is now 300x300 pixels
    size = 300

    for i, artist_name in enumerate(artist_names):
        x = (i % 3) * size
        y = (i // 3) * size
        
        print(f"Processing {i+1}/9: {artist_name}")
        img_url = get_artist_image_from_deezer(artist_name)
        
        if img_url:
            try:
                img_response = requests.get(img_url, headers=HEADERS, timeout=10)
                img = Image.open(BytesIO(img_response.content))
                # Resize to the new 300x300 dimensions
                img = img.resize((size, size), Image.LANCZOS)
                collage.paste(img, (x, y))
                print(f"  -> HD Success!")
            except Exception as e:
                print(f"  -> Failed to download.")
        else:
            print(f"  -> Not found on Deezer.")

    # Save the new HD image
    collage.save('lastfm_monthly.png', quality=95)
    print("\nHD Collage saved successfully!")

if __name__ == "__main__":
    artist_names = get_monthly_artist_names()
    if len(artist_names) > 0:
        print(f"--- Found {len(artist_names)} artists from Last.fm ---")
        create_collage(artist_names)
    else:
        print("No artists found for this month.")
