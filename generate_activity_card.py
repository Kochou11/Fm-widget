import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

USERNAME = os.environ['ANILIST_USERNAME']
API_URL = 'https://graphql.anilist.co'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Theme Colors
BG_COLOR = (22, 22, 26)       
BORDER_COLOR = (45, 43, 85)   
TEXT_COLOR = (139, 139, 158)  
HIGHLIGHT = (108, 99, 255)    
DIVIDER_COLOR = (45, 43, 85)  

def get_user_id():
    query = '''
    query ($name: String) {
      User(name: $name) { id }
    }
    '''
    resp = requests.post(API_URL, json={'query': query, 'variables': {'name': USERNAME}}, headers=HEADERS, timeout=15).json()
    if 'errors' in resp:
        print(f"Error finding user: {resp['errors']}")
        return None
    return resp.get('data', {}).get('User', {}).get('id')

def get_current_lists(user_id):
    # Using the "Page" query, which is the correct AniList standard
    query = '''
    query ($id: Int) {
      anime: Page(page: 1, perPage: 1) {
        mediaList(userId: $id, type: ANIME, status: CURRENT, sort: UPDATED_TIME_DESC) {
          media { coverImage { large } title { romaji english } episodes }
          progress
          updatedAt
        }
      }
      manga: Page(page: 1, perPage: 1) {
        mediaList(userId: $id, type: MANGA, status: CURRENT, sort: UPDATED_TIME_DESC) {
          media { coverImage { large } title { romaji english } chapters }
          progress
          updatedAt
        }
      }
    }
    '''
    
    try:
        resp = requests.post(API_URL, json={'query': query, 'variables': {'id': user_id}}, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        response = resp.json()
        
        if 'errors' in response:
            print(f"AniList API Error: {response['errors']}")
            return {}
            
        anime_data = response.get('data', {}).get('anime', {}).get('mediaList', [])
        manga_data = response.get('data', {}).get('manga', {}).get('mediaList', [])
        
        return {'anime': anime_data, 'manga': manga_data}
        
    except Exception as e:
        print(f"Network/API Error: {e}")
        return {}

def draw_text_wrapped(draw, text, x, y, max_width, font, fill_color):
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    if current_line:
        lines.append(' '.join(current_line))
        
    for i, line in enumerate(lines):
        draw.text((x, y + (i * 18)), line, font=font, fill=fill_color)
    return len(lines) * 18 

def create_card(data):
    width, height = 820, 200
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([0, 0, width-1, height-1], outline=BORDER_COLOR, width=2)
    draw.line([(410, 15), (410, 185)], fill=DIVIDER_COLOR, width=2)

    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_status = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_header = font_title = font_status = ImageFont.load_default()

    now = time.time()
    thirty_mins_ago = now - (30 * 60)

    # --- PROCESS ANIME ---
    anime_list = data.get('anime', [])
    draw.text((150, 20), "ANIME", font=font_header, fill=HIGHLIGHT)
    
    if anime_list and len(anime_list) > 0:
        anime = anime_list[0] 
        title = anime['media']['title'].get('romaji') or anime['media']['title'].get('english') or "Unknown"
        progress = anime['progress']
        total = anime['media'].get('episodes') or "?"
        updated_at = anime['updatedAt']
        
        try:
            cover_url = anime['media']['coverImage']['large']
            cover_resp = requests.get(cover_url, headers=HEADERS, timeout=10)
            cover_img = Image.open(BytesIO(cover_resp.content)).convert("RGBA")
            cover_img = cover_img.resize((120, 170), Image.LANCZOS)
            img.paste(cover_img, (20, 15), cover_img)
        except: pass
        
        draw_text_wrapped(draw, title, 150, 45, 240, font_title, "white")
        draw.text((150, 95), f"Ep {progress} / {total}", font=font_status, fill=TEXT_COLOR)
        
        if updated_at > thirty_mins_ago:
            draw.text((150, 120), "▶ Currently Watching", font=font_status, fill=HIGHLIGHT)
        else:
            draw.text((150, 120), "⏸ Was Watching", font=font_status, fill=TEXT_COLOR)
    else:
        draw.text((150, 60), "No anime in list", font=font_status, fill=TEXT_COLOR)

    # --- PROCESS MANGA ---
    manga_list = data.get('manga', [])
    draw.text((560, 20), "MANGA", font=font_header, fill=HIGHLIGHT)
    
    if manga_list and len(manga_list) > 0:
        manga = manga_list[0] 
        title = manga['media']['title'].get('romaji') or manga['media']['title'].get('english') or "Unknown"
        progress = manga['progress']
        total = manga['media'].get('chapters') or "?"
        updated_at = manga['updatedAt']
        
        try:
            cover_url = manga['media']['coverImage']['large']
            cover_resp = requests.get(cover_url, headers=HEADERS, timeout=10)
            cover_img = Image.open(BytesIO(cover_resp.content)).convert("RGBA")
            cover_img = cover_img.resize((120, 170), Image.LANCZOS)
            img.paste(cover_img, (430, 15), cover_img)
        except: pass
        
        draw_text_wrapped(draw, title, 560, 45, 240, font_title, "white")
        draw.text((560, 95), f"Ch {progress} / {total}", font=font_status, fill=TEXT_COLOR)
        
        if updated_at > thirty_mins_ago:
            draw.text((560, 120), "▶ Currently Reading", font=font_status, fill=HIGHLIGHT)
        else:
            draw.text((560, 120), "⏸ Was Reading", font=font_status, fill=TEXT_COLOR)
    else:
        draw.text((560, 60), "No manga in list", font=font_status, fill=TEXT_COLOR)

    img.save('current_activity.png')
    print("Activity card generated successfully!")

if __name__ == "__main__":
    print(f"Fetching activity for {USERNAME}...")
    user_id = get_user_id()
    
    if user_id:
        print(f"Found User ID: {user_id}. Fetching lists...")
        data = get_current_lists(user_id)
        if data:
            create_card(data)
        else:
            print("Skipping card generation due to API error.")
    else:
        print("Failed to get User ID.")
