import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.scraper_service import download_video_clip
from services.video_service import process_video_multi_hash
from main import voting_match

url = "https://youtu.be/vZIM4M5B0ZI?si=bLjJWGj_9OL23PZF"

print("Downloading video clip...")
clip_path = download_video_clip(url)
print(f"Downloaded to {clip_path}")

print("Processing multi-hashes...")
multi_hashes, phashes, frames = process_video_multi_hash(clip_path, num_frames=30)

print("Running fast check...")
fast_match, fast_matched_id, fast_best_dist, fast_similarity = voting_match(
    multi_hashes, threshold=55.0, vote_threshold=1
)
print(f"Fast Check: match={fast_match}, id={fast_matched_id}, dist={fast_best_dist}, sim={fast_similarity}")

print("Running deep check...")
deep_match, deep_matched_id, deep_best_dist, deep_similarity = voting_match(
    multi_hashes, threshold=30.0, vote_threshold=2
)
print(f"Deep Check: match={deep_match}, id={deep_matched_id}, dist={deep_best_dist}, sim={deep_similarity}")
