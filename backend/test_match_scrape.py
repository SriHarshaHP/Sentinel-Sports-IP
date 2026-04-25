import sys
import os
sys.path.append('c:\\Hackathon\\Hack2skill\\backend')
from services.video_service import process_video_multi_hash
from services.db_service import db_service

def test():
    uploads = [f for f in os.listdir("uploads") if f.startswith("yt_")]
    
    for upload in uploads:
        clip_path = os.path.join("uploads", upload)
        try:
            multi_hashes, phashes, frames = process_video_multi_hash(clip_path, num_frames=10)
        except:
            continue
            
        for idx, mh in enumerate(multi_hashes):
            results = db_service.search_multi_hash(mh, n_results=10)
            
            p_res = results.get("phash", {}).get("distances", [[999]])[0]
            d_res = results.get("dhash", {}).get("distances", [[999]])[0]
            w_res = results.get("whash", {}).get("distances", [[999]])[0]
            
            p_min = p_res[0] if p_res else 999
            d_min = d_res[0] if d_res else 999
            w_min = w_res[0] if w_res else 999
            
            # Count how many are < 60
            votes = 0
            if p_min < 60: votes += 1
            if d_min < 60: votes += 1
            if w_min < 60: votes += 1
            
            if votes >= 1:
                print(f"Video {upload} Frame {idx} -> p:{p_min:.1f} d:{d_min:.1f} w:{w_min:.1f}")

if __name__ == "__main__":
    test()
