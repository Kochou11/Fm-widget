import os
import requests
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
    return response['data']['User']['id']

def get_activity_data(user_id):
    # We will fetch up to 50 pages (~1250 activities) to ensure we cover a full year
    activity_counts = {}
    has_next_page = True
    page = 1

    one_year_ago = int((datetime.utcnow() - timedelta(days=365)).timestamp())

    while has_next_page and page <= 50:
        query = '''
        query ($userId: Int, $page: Int) {
          Page(page: $page, perPage: 25) {
            pageInfo { hasNextPage }
            activities(userId: $userId, type: ANIME_LIST, sort: CREATED_AT_DESC) {
              ... on ListActivity {
                createdAt
              }
            }
          }
        }
        '''
        variables = {'userId': user_id, 'page': page}
        response = requests.post(API_URL, json={'query': query, 'variables': variables}).json()
        
        for activity in response['data']['Page']['activities']:
            timestamp = activity['createdAt']
            
            # Stop fetching if we go further back than 1 year
            if timestamp < one_year_ago:
                has_next_page = False
                break
                
            # Convert Unix timestamp to YYYY-MM-DD
            date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            activity_counts[date_str] = activity_counts.get(date_str, 0) + 1

        has_next_page = response['data']['Page']['pageInfo']['hasNext_page'] and has_next_page
        page += 1

    return activity_counts

def generate_svg(activity_counts):
    # SVG Dimensions (Standard GitHub heatmap sizing)
    cell_size = 11
    cell_gap = 2
    width = 53 * (cell_size + cell_gap) # 53 weeks
    height = 7 * (cell_size + cell_gap)  # 7 days
    
    svg_lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="#16161a" rx="6"/>'
    ]

    today = datetime.utcnow()
    start_date = today - timedelta(days=365)

    for i in range(365):
        current_date = start_date + timedelta(days=i)
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Calculate grid position
        day_of_week = current_date.weekday() # Monday is 0
        week_number = (start_date + timedelta(days=i)).isocalendar()[1] - start_date.isocalendar()[1]
        
        x = (week_number + 1) * (cell_size + cell_gap)
        y = day_of_week * (cell_size + cell_gap)

        # Determine color based on activity count
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
    
    # Save the SVG
    with open('anilist_heatmap.svg', 'w') as f:
        f.write('\n'.join(svg_lines))
    print(f"Generated heatmap with {len(activity_counts)} active days.")

if __name__ == "__main__":
    print(f"Fetching data for {USERNAME}...")
    user_id = get_user_id()
    counts = get_activity_data(user_id)
    generate_svg(counts)
