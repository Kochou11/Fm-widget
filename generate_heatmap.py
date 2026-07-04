import os
import requests
import time
from datetime import datetime, timedelta

USERNAME = os.environ['ANILIST_USERNAME']
API_URL = 'https://graphql.anilist.co'

# AniList color palette
COLORS = [
    "#16161a", # Level 0: Empty (We will use this for the base, but draw an outline instead)
    "#2d2b55", # Level 1: 1-2 episodes
    "#4b47a0", # Level 2: 3-5 episodes
    "#6c63ff", # Level 3: 6-8 episodes
    "#8b83ff"  # Level 4: 9+ episodes
]

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
              ... on ListActivity {
                createdAt
              }
            }
          }
        }
        '''
        variables = {'userId': user_id, 'page': page}
        response_json = requests.post(API_URL, json={'query': query, 'variables': variables}).json()
        
        if 'errors' in response_json:
            print(f"API Error on page {page}: {response_json['errors']}")
            break
            
        page_data = response_json.get('data', {}).get('Page')
        if not page_data:
            break
            
        activities = page_data.get('activities') or []
        
        for activity in activities:
            timestamp = activity.get('createdAt')
            if not timestamp:
                continue
                
            if timestamp < one_year_ago:
                has_next_page = False
                break
                
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            activity_counts[date_str] = activity_counts.get(date_str, 0) + 1

        has_next_page = page_data.get('pageInfo', {}).get('hasNextPage', False) and has_next_page
        page += 1
        time.sleep(0.5) # Be polite to AniList API

    return activity_counts

def generate_svg(activity_counts):
    # Sizing variables matching GitHub's style
    cell_size = 11
    cell_gap = 2
    step = cell_size + cell_gap
    
    # Add padding for the text labels
    padding_left = 35  # Space for "Mon", "Wed", "Fri"
    padding_top = 20   # Space for "Jan", "Feb", "Mar"
    
    width = padding_left + 53 * step
    height = padding_top + 7 * step
    
    text_style = 'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; font-size: 9px; fill: #8b8b9e;'

    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        # Using transparent background so it blends perfectly into AniList's dark theme
    ]

    today = datetime.utcnow()
    start_date = today - timedelta(days=365)
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    days = ["", "Mon", "", "Wed", "", "Fri", ""] # GitHub only shows Mon, Wed, Fri

    # --- 1. DRAW MONTH LABELS ---
    prev_month = -1
    for i in range(365):
        current_date = start_date + timedelta(days=i)
        curr_month = current_date.month
        
        if curr_month != prev_month:
            week_num = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
            x = padding_left + (week_num * step)
            svg_lines.append(f'<text x="{x}" y="{padding_top - 6}" style="{text_style}">{months[curr_month-1]}</text>')
            prev_month = curr_month

    # --- 2. DRAW DAY LABELS ---
    for i in range(7):
        if days[i]:
            y = padding_top + (i * step) + 9
            svg_lines.append(f'<text x="{padding_left - 6}" y="{y}" text-anchor="end" style="{text_style}">{days[i]}</text>')

    # --- 3. DRAW SQUARES (Empty dots vs Filled squares) ---
    for i in range(365):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        day_of_week = current_date.weekday() # Monday is 0
        week_number = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
        
        x = padding_left + (week_number * step)
        y = padding_top + (day_of_week * step)

        count = activity_counts.get(date_str, 0)
        
        if count == 0:
            # INACTIVE DAY: Draw an outlined "dot" to look like GitHub
            fill = "transparent"
            stroke = "#2d2b55"
            stroke_width = 1
        elif count <= 2:
            fill, stroke, stroke_width = COLORS[1], "none", 0
        elif count <= 5:
            fill, stroke, stroke_width = COLORS[2], "none", 0
        elif count <= 8:
            fill, stroke, stroke_width = COLORS[3], "none", 0
        else:
            fill, stroke, stroke_width = COLORS[4], "none", 0

        svg_lines.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" rx="2"/>')

    svg_lines.append('</svg>')
    
    with open('anilist_heatmap.svg', 'w') as f:
        f.write('\n'.join(svg_lines))
    print(f"Generated GitHub-style heatmap with {len(activity_counts)} active days.")

if __name__ == "__main__":
    print(f"Fetching data for {USERNAME}...")
    user_id = get_user_id()
    
    if user_id:
        print(f"Found User ID: {user_id}. Fetching activity pages...")
        counts = get_activity_data(user_id)
        generate_svg(counts)
    else:
        print("Failed to get User ID. Check your ANILIST_USERNAME secret.")
