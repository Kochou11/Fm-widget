import os
import requests
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

USERNAME = os.environ['ANILIST_USERNAME']
API_URL = 'https://graphql.anilist.co'

# AniList color palette
COLORS = [
    None,       # Level 0: We will draw an outline instead of filling
    "#2d2b55", # Level 1: 1-2 episodes
    "#4b47a0", # Level 2: 3-5 episodes
    "#6c63ff", # Level 3: 6-8 episodes
    "#8b83ff"  # Level 4: 9+ episodes
]
OUTLINE_COLOR = "#2d2b55"
TEXT_COLOR = "#8b8b9e"

def get_user_id():
    query = '''
    query ($name: String) {
      User(name: $name) { id }
    }
    '''
    response = requests.post(API_URL, json={'query': query, 'variables': {'name': USERNAME}}).json()
    if 'errors' in response:
        print(f"Error finding user ID: {response['errors']}")
        return None
    return response.get('data', {}).get('User', {}).get('id')

def get_activity_data(user_id):
    activity_counts = {}
    has_next_page = True
    page = 1
    one_year_ago = int((datetime.utcnow() - timedelta(days=365)).timestamp())

    while has_next_page and page <= 50:
        query = '''
        query ($userId: Int, $page: Int) {
          Page(page: $page, perPage: 25) {
            pageInfo { hasNextPage }
            activities(userId: $userId, type: ANIME_LIST, sort: ID_DESC) {
              ... on ListActivity { createdAt }
            }
          }
        }
        '''
        variables = {'userId': user_id, 'page': page}
        response_json = requests.post(API_URL, json={'query': query, 'variables': variables}).json()
        
        if 'errors' in response_json:
            print(f"API Error: {response_json['errors']}")
            break
        page_data = response_json.get('data', {}).get('Page')
        if not page_data:
            break
            
        for activity in (page_data.get('activities') or []):
            timestamp = activity.get('createdAt')
            if not timestamp: continue
            if timestamp < one_year_ago:
                has_next_page = False
                break
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            activity_counts[date_str] = activity_counts.get(date_str, 0) + 1

        has_next_page = page_data.get('pageInfo', {}).get('hasNextPage', False) and has_next_page
        page += 1
        time.sleep(0.5)
    return activity_counts

def create_heatmap_png(activity_counts):
    cell_size = 11
    cell_gap = 2
    step = cell_size + cell_gap
    
    padding_left = 35
    padding_top = 20
    
    # Final image dimensions
    width = padding_left + 53 * step
    height = padding_top + 7 * step
    
    # Create image with transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Load font for labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9)
    except:
        font = ImageFont.load_default()

    today = datetime.utcnow()
    start_date = today - timedelta(days=365)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    days = ["", "Mon", "", "Wed", "", "Fri", ""]

    # 1. Draw Month Labels
    prev_month = -1
    for i in range(365):
        current_date = start_date + timedelta(days=i)
        curr_month = current_date.month
        if curr_month != prev_month:
            week_num = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
            x = padding_left + (week_num * step)
            draw.text((x, 4), months[curr_month-1], fill=TEXT_COLOR, font=font)
            prev_month = curr_month

    # 2. Draw Day Labels
    for i in range(7):
        if days[i]:
            y = padding_top + (i * step)
            # Calculate width to right-align the text
            bbox = draw.textbbox((0, 0), days[i], font=font)
            text_width = bbox[2] - bbox[0]
            draw.text((padding_left - text_width - 6, y), days[i], fill=TEXT_COLOR, font=font)

    # 3. Draw Grid Squares
    for i in range(365):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        day_of_week = current_date.weekday()
        week_number = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
        
        x1 = padding_left + (week_number * step)
        y1 = padding_top + (day_of_week * step)
        x2 = x1 + cell_size
        y2 = y1 + cell_size

        count = activity_counts.get(date_str, 0)
        
        if count == 0:
            # Empty dot: Draw transparent fill with an outline
            draw.rectangle([x1, y1, x2, y2], outline=OUTLINE_COLOR, width=1)
        elif count <= 2:
            draw.rectangle([x1, y1, x2, y2], fill=COLORS[1])
        elif count <= 5:
            draw.rectangle([x1, y1, x2, y2], fill=COLORS[2])
        elif count <= 8:
            draw.rectangle([x1, y1, x2, y2], fill=COLORS[3])
        else:
            draw.rectangle([x1, y1, x2, y2], fill=COLORS[4])

    img.save('anilist_heatmap.png')
    print(f"Generated GitHub-style PNG heatmap with {len(activity_counts)} active days.")

if __name__ == "__main__":
    print(f"Fetching data for {USERNAME}...")
    user_id = get_user_id()
    if user_id:
        print(f"Found User ID: {user_id}. Fetching activity...")
        counts = get_activity_data(user_id)
        create_heatmap_png(counts)
    else:
        print("Failed to get User ID.")
