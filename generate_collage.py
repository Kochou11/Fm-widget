import os
import requests
from PIL import Image
from io import BytesIO

# Get secrets from GitHub environment
API_KEY = os.environ['LASTFM_API_KEY']
USERNAME = os.environ['LASTFM_USERNAME']

def get_monthly_artists():
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={USERNAME}&period=1month&api_key={API_KEY}&format=json&limit=9"
    response = requests.get(url).json()
    
    image_urls = []
    print(f"--- Found {len(response['topartists']['artist'])} artists ---")
    
    for i, artist in enumerate(response['topartists']['artist']):
        img_url = artist['image'][-1]['#text']
        artist_name = artist['name']
        
        # Print what the script is seeing
        print(f"Artist {i+1}: {artist_name} | URL: {img_url}")
        
        # Skip if empty, or if it's the default Last.fm grey silhouette placeholder
        is_empty = not img_url
        is_placeholder = "2a96cbd8b46e442fc41c2b86b821562f" in img_url
        
        if is_empty or is_placeholder:
            print("  -> Skipping (Missing image or is default placeholder)")
        else:
            image_urls.append(img_url)
            
    print(f"--- Total valid images to use: {len(image_urls)} ---")
    return image_urls[:9]

def create_collage(image_urls):
    # Create a blank 3x3 canvas (300x300 pixels)
    collage = Image.new('RGB', (300, 300), (30, 30, 30)) 
    size = 100
    
    for i in range(9):
        x = (i % 3) * size
        y = (i // 3) * size
        
        if i < len(image_urls):
            try:
                print(f"Downloading image for slot {i+1}...")
                response = requests.get(image_urls[i], timeout=10)
                response.raise_for_status() # Forces an error if the image fails to load
                img = Image.open(BytesIO(response.content))
                img = img.resize((size, size), Image.LANCZOS)
                collage.paste(img, (x, y))
                print(f"  -> Success!")
            except Exception as e:
                print(f"  -> Failed to load: {e}")
        else:
            print(f"Slot {i+1} left blank.")

    collage.save('lastfm_monthly.png')
    print("Collage saved successfully!")

if __name__ == "__main__":
    urls = get_monthly_artists()
    create_collage(urls)
