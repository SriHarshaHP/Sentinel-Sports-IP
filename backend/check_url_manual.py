import sys
import os
import shutil
import uuid
from services.scraper_service import download_video_clip
from services.video_service import process_video_multi_hash
from services.watermark_service import detect_watermark
from services.db_service import db_service

def voting_match(multi_hashes: list[dict], threshold=35.0, vote_threshold=2):
    match_found = False
    matched_id = None
    best_distance = None
    
    for mh in multi_hashes:
        results = db_service.search_multi_hash(mh, n_results=20)
        
        vote_tally = {}
        dist_tally = {}
        frame_min_dist = None
        
        for hash_type in ["phash", "dhash", "whash"]:
            res = results.get(hash_type, {})
            distances = res.get("distances", [[]])
            metadatas = res.get("metadatas", [[]])
            
            matched_vids_for_this_algo = set()
            
            if distances and metadatas and len(distances[0]) > 0:
                for i in range(len(distances[0])):
                    dist = distances[0][i]
                    vid_id = metadatas[0][i].get("video_id")
                    
                    if frame_min_dist is None or dist < frame_min_dist:
                        frame_min_dist = dist
                    
                    if dist < threshold:
                        matched_vids_for_this_algo.add(vid_id)
                        if vid_id not in dist_tally or dist < dist_tally[vid_id]:
                            dist_tally[vid_id] = dist
                            
            for vid_id in matched_vids_for_this_algo:
                vote_tally[vid_id] = vote_tally.get(vid_id, 0) + 1
                            
        if frame_min_dist is not None:
            if best_distance is None or frame_min_dist < best_distance:
                best_distance = frame_min_dist
                
        for vid_id, votes in vote_tally.items():
            if votes >= vote_threshold:
                match_found = True
                matched_id = vid_id
                break
                
        if match_found:
            break
            
    similarity_score = None
    if best_distance is not None:
        similarity_score = round(max(0, 100 - (best_distance / 256.0) * 100), 1)
        
    return match_found, matched_id, best_distance, similarity_score

def check_url(url):
    print(f"--- Analyzing: {url} ---")
    try:
        # 1. Download
        print("1. Downloading clip...")
        clip_path = download_video_clip(url)
        
        # 2. Hashing (10 frames for drone-like speed)
        print("2. Extracting multi-hashes (10 frames)...")
        multi_hashes, _, _ = process_video_multi_hash(clip_path, num_frames=10)
        
        # 3. Fast Check (Threshold 55.0)
        print("3. Running Fast Check...")
        fast_match, fast_id, fast_dist, fast_sim = voting_match(multi_hashes, threshold=55.0, vote_threshold=1)
        print(f"   - Match Found: {fast_match}")
        if fast_match:
            print(f"   - Similarity: {fast_sim}%")
            print(f"   - Matched ID: {fast_id}")
            
        # 4. Deep Check (Watermark)
        print("4. Running Deep Check (Watermark)...")
        detected_watermark = None
        watermark_hit = False
        if fast_match:
            detected_watermark = detect_watermark(clip_path)
            watermark_hit = (detected_watermark == "ORG_0001")
            print(f"   - DNA Detected: {detected_watermark}")
        else:
            print("   - Skipping DNA check (no fast match).")
            
        # 5. Final Result
        is_pirated = fast_match and watermark_hit
        print("\n--- FINAL VERDICT ---")
        if is_pirated:
            print("STATUS: PIRATED CONTENT DETECTED (DNA SIGNATURE MATCH)")
        else:
            print("STATUS: CLEAN (No matching DNA found)")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    url = "https://youtu.be/Fc_tWoBaiDk?si=5_fgtno3dcAG7daC"
    check_url(url)
