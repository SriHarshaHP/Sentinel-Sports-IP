import os
from apify_client import ApifyClient
from dotenv import load_dotenv

load_dotenv()

# Securely load the token from environment variables
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
client = ApifyClient(APIFY_API_TOKEN)

def search_tiktok(keyword: str, max_results: int = 1):
    run_input = {
        "hashtags": [keyword.replace(" ", "")], # hashtags shouldn't have spaces
        "resultsPerPage": max_results,
        "shouldDownloadVideos": False,
    }
    
    # Official clockwork/tiktok-scraper actor
    run = client.actor("clockwork/tiktok-scraper").call(run_input=run_input)
    
    videos = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        if len(videos) >= max_results: break
        video_url = item.get("videoUrl") or item.get("webVideoUrl")
        if video_url:
            videos.append({
                'video_id': item.get("id", "tiktok_video"),
                'title': item.get("text", "TikTok Video")[:50],
                'url': video_url
            })
    return videos

def search_instagram(keyword: str, max_results: int = 1):
    run_input = {
        "search": keyword.replace(" ", ""),
        "searchType": "hashtag",
        "resultsType": "posts",
        "resultsLimit": max_results,
    }
    
    # Official apify/instagram-scraper actor
    run = client.actor("apify/instagram-scraper").call(run_input=run_input)
    
    videos = []
    for item in client.dataset(run["defaultDatasetId"]).iterate_items():
        if len(videos) >= max_results: break
        video_url = item.get("videoUrl")
        if video_url:
            videos.append({
                'video_id': item.get("shortCode", "insta_video"),
                'title': item.get("caption", "Instagram Reel")[:50] if item.get("caption") else "Instagram Reel",
                'url': video_url
            })
    return videos
