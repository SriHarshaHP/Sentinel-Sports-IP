import os
import yt_dlp
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=API_KEY)


def search_youtube(keyword: str, max_results: int = 1):
    from datetime import datetime, timedelta
    # Optimize keywords for YouTube: replace commas with spaces and clean whitespace
    cleaned = keyword.replace(",", " ").replace("  ", " ").strip()
    # FORCE ONLY TWO WORDS: Prevent 'Keyword Overload' which breaks YouTube search
    optimized_keyword = " ".join(cleaned.split()[:2])
    yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
    
    search_response = youtube.search().list(
        q=optimized_keyword,
        part='id,snippet',
        maxResults=max_results,
        type='video',
        videoEmbeddable='true',
        order='date',
        publishedAfter=yesterday
    ).execute()
    
    videos = []
    for search_result in search_response.get('items', []):
        raw_title = search_result['snippet']['title']
        # Clean title for console-safe logging
        clean_title = raw_title.encode('ascii', 'ignore').decode('ascii')
        
        # Additional safety check for LIVE keywords in title
        if any(kw in clean_title.upper() for kw in ['LIVE', '🔴', 'PREMIERE', 'BROADCAST']):
            continue
            
        if search_result['snippet'].get('liveBroadcastContent') != 'none':
            continue
            
        videos.append({
            'video_id': search_result['id']['videoId'],
            'title': raw_title,
            'url': f"https://www.youtube.com/watch?v={search_result['id']['videoId']}"
        })
    return videos

def download_video_clip(url: str, output_dir: str = "uploads/") -> str:
    # Ensure absolute path for reliability
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)

    COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "cookies.txt")

    # Render/Cloud environment detection
    is_render = os.getenv("RENDER") == "true"
    
    ydl_opts = {
        'format': 'worst[ext=mp4]/worst',
        'download_sections': [{
            'start_time': 0,
            'end_time': 10,
        }],
        'force_keyframes_at_cuts': True,
        'outtmpl': os.path.join(abs_output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'extractor_args': {
            'youtube': {
                # Use mobile clients which are less likely to be blocked by 'bot detection'
                'player_client': ['android', 'ios'],
                'skip': ['hls', 'dash']
            }
        },
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=True)
            except Exception as e:
                # Log the error but don't crash the whole process
                print(f"Extraction failed for {url}: {e}")
                return None
                    
            if not info_dict:
                return None
                
            video_id = info_dict.get("id", None)
            
            # Find the file using glob to handle any extension (.mp4, .mkv, .webm)
            import glob
            matches = glob.glob(os.path.join(abs_output_dir, f"{video_id}.*"))
            if matches:
                # Return the most recently modified match just in case
                matches.sort(key=os.path.getmtime, reverse=True)
                return matches[0]
                
            raise Exception(f"File with ID {video_id} not found in {abs_output_dir}")
    except Exception as e:
        raise Exception(f"Failed to download video '{url}': {e}")
