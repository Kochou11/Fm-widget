import os
import requests
import time
from datetime import datetime, timedelta

USERNAME = os.environ['ANILIST_USERNAME']
API_URL = 'https://graphql.anilist.co'

# AniList color palette for the heatmap squares
COLORS = [
    "#16161a", # Level 0: Empty/No activity
    "#2d2b55", # Level 1: 1-2 episodes logged
    "#4b47a0", # Level 2: 3-5 episodes logged
    "#6c63ff", # Level 3: 6-8 episodes logged
    "#8b83ff"  # Level 4: 9+ episodes logged
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
        
        # SAFETY CHECK: If AniList returns an error, print it and stop to prevent crashing
        if 'errors' in response_json:
            print(f"API Error on page {page}: {response_json['errors']}")
            break
            
        # SAFETY CHECK: If data is missing, stop
        page_data = response_json.get('data', {}).get('Page')
        if not page_data:
            print(f"Missing page data on page {page}. Stopping.")
            break
            
        activities = page_data.get('activities') or []
        
        for activity in activities:
            timestamp = activity.get('createdAt')
            if not timestamp:
                continue
                
            # Stop fetching if we go further back than 1 year
            if timestamp < one_year_ago:
                has_next_page = False
                break
                
            # Convert Unix timestamp to YYYY-MM-DD
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            activity_counts[date_str] = activity_counts.get(date_str, 0) + 1

        has_next_page = page_data.get('pageInfo', {}).get('hasNextPage', False) and has_next_page
        page += 1
        
        # Be polite to AniList's servers: wait half a second between pages
        time.sleep(0.5)

    return activity_counts

def generate_svg(activity_counts):
    cell_size = 11
    cell_gap = 2
    width = 53 * (cell_size + cell_gap) 
    height = 7 * (cell_size + cell_gap)  
    
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#16161a" rx="6"/>'
    ]

    today = datetime.utcnow()
    start_date = today - timedelta(days=365)

    for i in range(365):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        day_of_week = current_date.weekday() 
        week_number = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
        
        x = (week_number + 1) * (cell_size + cell_gap)
        y = day_of_week * (cell_size + cell_gap)

        count = activity_counts.get(date_str, 0)
        if count == 0:
            color = COLORS[0]
        elif count <= 2:
            color = COLORS[1]
        elif count <= 5:
            color = COLORS[2]
        elif count <= 8:
            color = COLORS[3]
        else:
            color = COLORS[4]

        svg_lines.append(f'<rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{color}" rx="2"/>')

    svg_lines.append('</svg>')
    
    with open('anilist_heatmap.svg', 'w') as f:
        f.write('\n'.join(svg_lines))
    print(f"Generated heatmap with {len(activity_counts)} active days.")

if __name__ == "__main__":
    print(f"Fetching data for {USERNAME}...")
    user_id = get_user_id()
    
    if user_id:
        print(f"Found User ID: {user_id}. Fetching activity pages...")
        counts = get_activity_data(user_id)
        generate_svg(counts)
    else:
        print("Failed to get User ID. Check your ANILIST_USERNAME secret.")
