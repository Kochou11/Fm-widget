import os
import requests
from PIL import Image
from io import BytesIO

# Get secrets from GitHub environment
API_KEY = os.environ['LASTFM_API_KEY']
USERNAME = os.environ['LASTFM_USERNAME']

def get_monthly_artists():
    # Changed method from gettopalbums to gettopartists
    url = f"http://ws.audioscrobbler.com/2.0/?method=user.gettopartists&user={USERNAME}&period=1month&api_key={API_KEY}&format=json&limit=9"
    response = requests.get(url).json()
    
    image_urls = []
    # Changed parsing to target 'topartists' -> 'artist'
    for artist in response['topartists']['artist']:
        # Get the highest quality image (extralarge)
        img_url = artist['image'][-1]['#text']
        
        # Last.fm returns a placeholder silhouette if no artist picture exists; skip it
        if "2a96cbd8b46e442fc41c2b86b821562f" not in img_url and "https://" in img_url:
            image_urls.append(img_url)
            
    return image_urls[:9] # Ensure exactly 9

def create_collage(image_urls):
    # Create a blank 3x3 canvas (300x300 pixels)
    collage = Image.new('RGB', (300, 300), (30, 30, 30)) 
    size = 100
    
    # Loop exactly 9 times to maintain the grid structure
    for i in range(9):
        x = (i % 3) * size
        y = (i // 3) * size
        
        # Only try to paste if we actually got a valid image URL for this slot
        if i < len(image_urls):
            try:
                response = requests.get(image_urls[i])
                img = Image.open(BytesIO(response.content))
                img = img.resize((size, size), Image.LANCZOS)
                collage.paste(img, (x, y))
            except Exception as e:
                # If the image fails to load, it just leaves the dark background
                pass

    collage.save('lastfm_monthly.png')
    print("Artist collage saved successfully!")

if __name__ == "__main__":
    urls = get_monthly_artists()
    create_collage(urls)
