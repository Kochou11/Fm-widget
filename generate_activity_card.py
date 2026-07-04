import os
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

USERNAME = os.environ['ANILIST_USERNAME']
API_URL = 'https://graphql.anilist.co'
HEADERS = {'User-Agent': 'Mozilla/5.0'}

# Theme Colors
BG_COLOR = (22, 22, 26)       # AniList Dark Background
BORDER_COLOR = (45, 43, 85)   # Subtle Purple Border
TEXT_COLOR = (139, 139, 158)  # Grey Text
HIGHLIGHT = (108, 99, 255)    # AniList Bright Blue
DIVIDER_COLOR = (45, 43, 85)  # Line between Anime/Manga

def get_current_lists():
    query = '''
    query ($name: String) {
      User(name: $name) {
        currentAnime: mediaList(type: ANIME, status: CURRENT, sort: UPDATED_TIME_DESC, perPage: 1) {
          media { coverImage { large } title { romaji english } episodes }
          progress
          updatedAt
        }
        currentManga: mediaList(type: MANGA, status: CURRENT, sort: UPDATED_TIME_DESC, perPage: 1) {
          media { coverImage { large } title { romaji english } chapters }
          progress
          updatedAt
        }
      }
    }
    '''
    response = requests.post(API_URL, json={'query': query, 'variables': {'name': USERNAME}}, headers=HEADERS).json()
    return response.get('data', {}).get('User', {})

def draw_text_wrapped(draw, text, x, y, max_width, font, fill_color):
    # Wraps long anime titles so they don't overflow the box
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
    return len(lines) * 18 # Return height used

def create_card(data):
    # Canvas size (Wide banner style)
    width, height = 820, 200
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Draw borders
    draw.rectangle([0, 0, width-1, height-1], outline=BORDER_COLOR, width=2)
    draw.line([(410, 15), (410, 185)], fill=DIVIDER_COLOR, width=2)

    # Load Fonts
    try:
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_status = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_header = font_title = font_status = ImageFont.load_default()

    now = time.time()
    thirty_mins_ago = now - (30 * 60)

    # --- PROCESS ANIME (Left Side) ---
    anime_list = data.get('currentAnime')
    draw.text((150, 20), "ANIME", font=font_header, fill=HIGHLIGHT)
    
    if anime_list and len(anime_list) > 0:
        anime = anime_list[0]
        title = anime['media']['title'].get('romaji') or anime['media']['title'].get('english') or "Unknown"
        progress = anime['progress']
        total = anime['media'].get('episodes') or "?"
        updated_at = anime['updatedAt']
        
        # Draw Cover
        try:
            cover_url = anime['media']['coverImage']['large']
            cover_resp = requests.get(cover_url, headers=HEADERS, timeout=10)
            cover_img = Image.open(BytesIO(cover_resp.content)).convert("RGBA")
            cover_img = cover_img.resize((120, 170), Image.LANCZOS)
            img.paste(cover_img, (20, 15), cover_img)
        except: pass
        
        # Draw Text
        draw_text_wrapped(draw, title, 150, 45, 240, font_title, "white")
        draw.text((150, 95), f"Ep {progress} / {total}", font=font_status, fill=TEXT_COLOR)
        
        # 30-Minute Logic
        if updated_at > thirty_mins_ago:
            draw.text((150, 120), "▶ Currently Watching", font=font_status, fill=HIGHLIGHT)
        else:
            draw.text((150, 120), "⏸ Was Watching", font=font_status, fill=TEXT_COLOR)
    else:
        draw.text((150, 60), "No anime in list", font=font_status, fill=TEXT_COLOR)

    # --- PROCESS MANGA (Right Side) ---
    manga_list = data.get('currentManga')
    draw.text((560, 20), "MANGA", font=font_header, fill=HIGHLIGHT)
    
    if manga_list and len(manga_list) > 0:
        manga = manga_list[0]
        title = manga['media']['title'].get('romaji') or manga['media']['title'].get('english') or "Unknown"
        progress = manga['progress']
        total = manga['media'].get('chapters') or "?"
        updated_at = manga['updatedAt']
        
        # Draw Cover
        try:
            cover_url = manga['media']['coverImage']['large']
            cover_resp = requests.get(cover_url, headers=HEADERS, timeout=10)
            cover_img = Image.open(BytesIO(cover_resp.content)).convert("RGBA")
            cover_img = cover_img.resize((120, 170), Image.LANCZOS)
            img.paste(cover_img, (430, 15), cover_img)
        except: pass
        
        # Draw Text
        draw_text_wrapped(draw, title, 560, 45, 240, font_title, "white")
        draw.text((560, 95), f"Ch {progress} / {total}", font=font_status, fill=TEXT_COLOR)
        
        # 30-Minute Logic
        if updated_at > thirty_mins_ago:
            draw.text((560, 120), "▶ Currently Reading", font=font_status, fill=HIGHLIGHT)
        else:
            draw.text((560, 120), "⏸ Was Reading", font=font_status, fill=TEXT_COLOR)
    else:
        draw.text((560, 60), "No manga in list", font=font_status, fill=TEXT_COLOR)

    img.save('current_activity.png')
    print("Activity card generated!")

if __name__ == "__main__":
    print(f"Fetching activity for {USERNAME}...")
    data = get_current_lists()
    create_card(data)
