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

    ydl_opts = {
        # Force the absolute lowest resolution (144p) to save massive amounts of data
        'format': 'worst[ext=mp4]/worst',
        # Only download the first 10 seconds of the video for forensic analysis
        'download_sections': [{
            'start_time': 0,
            'end_time': 10,
        }],
        'force_keyframes_at_cuts': True,
        # Force a simple filename template
        'outtmpl': os.path.join(abs_output_dir, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        'socket_timeout': 20,
        'retries': 2,
        'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web', 'android_vr'],
                'skip': ['hls', 'dash']
            }
        },
        # Ignore errors so one bad cookie/video doesn't kill the whole drone
        'ignoreerrors': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # We use extract_info with download=True
            try:
                info_dict = ydl.extract_info(url, download=True)
            except Exception as e:
                # If cookie error occurs, try one more time WITHOUT cookies
                if "cookies" in str(e).lower():
                    ydl_opts['cookiefile'] = None
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl_no_cookies:
                        info_dict = ydl_no_cookies.extract_info(url, download=True)
                else:
                    raise e
                    
            if not info_dict:
                raise Exception("Could not extract video info")
                
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
