import sys
import os
sys.path.append(os.getcwd())
from services.scraper_service import download_video_clip
from services.video_service import process_video_multi_hash
from main import voting_match
from services.watermark_service import detect_watermark

target_url = "https://youtu.be/BBdooRFdnpc?si=_Wuhuu6rqFVCR-Y1"

def test_manual_detection():
    print(f"--- DEBUGGING DETECTION FOR: {target_url} ---")
    
    try:
        # 1. Download
        print("Downloading clip...")
        clip_path = download_video_clip(target_url)
        print(f"Downloaded to {clip_path}")
        
        # 2. Extract Hashes
        print("Extracting fingerprints...")
        multi_hashes, phashes, frames = process_video_multi_hash(clip_path, num_frames=10)
        
        # 3. Check DB
        print("Searching database...")
        fast_match, fast_matched_id, fast_best_dist, fast_similarity = voting_match(
            multi_hashes, threshold=55.0, vote_threshold=1
        )
        
        # 4. Check Watermark
        print("Checking forensic watermark...")
        detected_watermark = detect_watermark(clip_path)
        
        print("\n--- RESULTS ---")
        print(f"Similarity Match: {fast_match} (Score: {fast_similarity}%)")
        print(f"Matched ID: {fast_matched_id}")
        print(f"Watermark Detected: {detected_watermark}")
        
        if not fast_match and not detected_watermark:
            print("\nCONCLUSION: No match found. The video is likely NOT in your Vault or the search threshold is too strict.")
        elif fast_match and fast_similarity < 90.0 and not detected_watermark:
             print("\nCONCLUSION: Weak match found, but below auto-alert threshold (90%).")
        else:
            print("\nCONCLUSION: Video SHOULD be detected by the drone.")
            
        # Cleanup
        if os.path.exists(clip_path):
            os.remove(clip_path)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_manual_detection()
