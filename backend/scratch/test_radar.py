import os
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)

def test_search(keyword):
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    print(f"SEARCHING FOR: {keyword} (Since {yesterday})")
    
    res = youtube.search().list(
        q=keyword,
        part='id,snippet',
        maxResults=40,
        type='video',
        order='date',
        publishedAfter=yesterday
    ).execute()
    
    for i, item in enumerate(res.get('items', [])):
        title = item['snippet']['title']
        v_id = item['id']['videoId']
        published = item['snippet']['publishedAt']
        print(f"[{i+1}] {title} ({v_id}) - {published}")

if __name__ == "__main__":
    test_search("mlbb benedetta")
