import sys
import os
sys.path.append('c:\\Hackathon\\Hack2skill\\backend')
from services.video_service import process_video_multi_hash
from services.db_service import db_service

def test():
    clip_path = os.path.join("uploads", "e7fab5bf-dbd2-4410-b7e5-e69c93725f82.mp4")
    print(f"Testing with {clip_path}")
    
    multi_hashes, phashes, frames = process_video_multi_hash(clip_path, num_frames=5)
    
    for idx, mh in enumerate(multi_hashes):
        print(f"\n--- Frame {idx} ---")
        results = db_service.search_multi_hash(mh, n_results=3)
        
        for hash_type in ["phash", "dhash", "whash"]:
            res = results.get(hash_type, {})
            distances = res.get("distances", [[]])
            metadatas = res.get("metadatas", [[]])
            
            if distances and metadatas and len(distances[0]) > 0:
                print(f"[{hash_type}] Top 3 matches:")
                for i in range(min(3, len(distances[0]))):
                    dist = distances[0][i]
                    vid_id = metadatas[0][i].get("video_id")
                    print(f"   dist={dist:.1f}  vid={vid_id[:8]}")
            else:
                print(f"[{hash_type}] No matches")

if __name__ == "__main__":
    test()
