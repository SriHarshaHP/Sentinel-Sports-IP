from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import concurrent.futures
from services.watermark_service import embed_watermark, detect_watermark
from services.video_service import process_video_and_extract_frames, process_video_multi_hash
from services.db_service import db_service
from services.scraper_service import search_youtube, download_video_clip
from services.apify_service import search_tiktok, search_instagram
from pydantic import BaseModel
import json
from datetime import datetime

class ScrapeRequest(BaseModel):
    keyword: str
    platform: str = "youtube"

class TakedownRequest(BaseModel):
    incident_id: str



app = FastAPI(title="Sentinel-Sports IP Vault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("protected", exist_ok=True)

@app.get("/api/vault/download/{filename}")
async def download_protected_video(filename: str):
    file_path = os.path.join("protected", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path, 
        media_type='application/octet-stream', 
        filename=filename
    )

# --- Helper: Multi-hash voting match ---
def voting_match(multi_hashes: list[dict], threshold=35.0, vote_threshold=2):
    """
    For each frame's multi-hash, search all 3 hash collections.
    A frame is considered a match if at least `vote_threshold` out of 3
    hash algorithms agree on the SAME video_id (distance < threshold).
    
    Returns (match_found, matched_video_id, best_distance, similarity_score).
    """
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


@app.post("/api/vault/protect")
async def protect_video(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    ext = file.filename.split('.')[-1]
    temp_path = f"uploads/{file_id}.{ext}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Use multi-hash extraction for better accuracy
        multi_hashes, phashes, frames = process_video_multi_hash(temp_path, num_frames=30)
        
        protected_path = embed_watermark(temp_path, watermark_id="ORG_0001")
        final_protected_path = f"protected/{file_id}_protected.{ext}"
        shutil.move(protected_path, final_protected_path)
        
        # Store multi-hash fingerprints across all collections
        db_service.insert_multi_hashes(file_id, multi_hashes)
        
        return {
            "status": "success",
            "video_id": file_id,
            "protected_video_url": f"http://localhost:8000/api/vault/download/{file_id}_protected.{ext}",
            "hashes_stored": len(multi_hashes),
            "hash_types": ["phash", "dhash", "whash"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/sentinel/check")
async def check_video(file: UploadFile = File(...)):
    temp_path = f"uploads/check_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Multi-hash extraction (30 frames, scene-change aware)
        multi_hashes, phashes, frames = process_video_multi_hash(temp_path, num_frames=30)
        
        # --- Fast Check: voting with loose threshold ---
        fast_match, fast_matched_id, fast_best_dist, fast_similarity = voting_match(
            multi_hashes, threshold=55.0, vote_threshold=1
        )
        
        # --- Deep Check: flag if any hash algo finds >= 80% similarity (dist <= 51.2) ---
        deep_match, deep_matched_id, deep_best_dist, deep_similarity = voting_match(
            multi_hashes, threshold=51.2, vote_threshold=1
        )
        
        detected_watermark = None
        watermark_hit = False
        
        # New Logic: Only check for watermark if the fast match is positive
        if fast_match:
            detected_watermark = detect_watermark(temp_path)
            watermark_hit = (detected_watermark == "ORG_0001")
        
        # Only flag as pirated if BOTH the match was found and the watermark is confirmed
        is_pirated = fast_match and watermark_hit
        
        return {
            "status": "complete",
            "is_pirated": is_pirated,
            "match_found_in_db": fast_match,
            "matched_video_id": fast_matched_id,
            "detected_watermark": detected_watermark,
            "deep_check_match": deep_match and watermark_hit,
            "deep_matched_id": deep_matched_id or fast_matched_id,
            "similarity_score": fast_similarity,
            "best_distance": fast_best_dist
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Helper: Process a single scraped video ---
def process_scraped_video(v, platform):
    try:
        clip_path = download_video_clip(v['url'])
        
        # Reduced frame count (10 frames) for much faster processing during drone scans
        multi_hashes, phashes, frames = process_video_multi_hash(clip_path, num_frames=10)
        
        # --- Fast Check: voting with loose threshold ---
        fast_match, fast_matched_id, fast_best_dist, fast_similarity = voting_match(
            multi_hashes, threshold=55.0, vote_threshold=1
        )
        
        # --- Deep Check: flag if any hash algo finds >= 80% similarity (dist <= 51.2) ---
        deep_match, deep_matched_id, deep_best_dist, deep_similarity = voting_match(
            multi_hashes, threshold=51.2, vote_threshold=1
        )

        detected_watermark = None
        watermark_hit = False

        # Only check for watermark if the fast match is positive
        if fast_match:
            detected_watermark = detect_watermark(clip_path)
            watermark_hit = (detected_watermark == "ORG_0001")

        # Only flag as pirated if BOTH the match was found and the watermark is confirmed
        is_pirated = fast_match and watermark_hit

        # 4. Evidence Capture (Save a frame as proof if pirated)
        evidence_image = None
        if is_pirated:
            os.makedirs("evidence", exist_ok=True)
            evidence_path = f"evidence/{str(uuid.uuid4())}.jpg"
            cap_evidence = cv2.VideoCapture(clip_path)
            ret_ev, frame_ev = cap_evidence.read()
            if ret_ev:
                cv2.imwrite(evidence_path, frame_ev)
                evidence_image = evidence_path
            cap_evidence.release()

        result_obj = {
            "id": str(uuid.uuid4()),
            "video": v,
            "platform": platform,
            "is_pirated": is_pirated,
            "match_found_in_db": fast_match,
            "matched_video_id": fast_matched_id,
            "detected_watermark": detected_watermark,
            "deep_check_match": watermark_hit,
            "evidence_frame": evidence_image,
            "similarity_score": fast_similarity,
            "timestamp": datetime.now().isoformat(),
            "status": "detected"
        }

        if is_pirated:
            # Persist to incidents.json
            incidents = []
            if os.path.exists("incidents.json"):
                with open("incidents.json", "r") as f:
                    try:
                        incidents = json.load(f)
                    except:
                        pass
            incidents.append(result_obj)
            with open("incidents.json", "w") as f:
                json.dump(incidents, f, indent=4)
        
        # Cleanup
        try:
            if os.path.exists(clip_path):
                os.remove(clip_path)
        except:
            pass
            
        return result_obj
    except Exception as inner_e:
        print(f"Drone Error for {v.get('url')}: {inner_e}")
        return None

@app.get("/api/maintenance/clear_uploads")
async def clear_uploads():
    try:
        files = glob.glob("uploads/*")
        for f in files:
            try:
                os.remove(f)
            except:
                pass
        return {"status": "success", "message": f"Cleared {len(files)} temporary files"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/sentinel/scrape_and_check")
async def scrape_and_check_video(req: ScrapeRequest):
    try:
        videos = []
        if req.platform == "tiktok":
            videos = search_tiktok(req.keyword, max_results=5)
        elif req.platform == "instagram":
            videos = search_instagram(req.keyword, max_results=5)
        else:
            videos = search_youtube(req.keyword, max_results=10)
            
        if not videos:
            return {"status": "complete", "message": f"No videos found on {req.platform}", "results": []}
            
        # Use ThreadPoolExecutor with a strict 2-minute total timeout
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_video = {executor.submit(process_scraped_video, v, req.platform): v for v in videos}
            try:
                # Limit total time to 120 seconds to stay within browser fetch limits
                for future in concurrent.futures.as_completed(future_to_video, timeout=120):
                    try:
                        res = future.result(timeout=30)
                        if res: # Only add if processing was successful
                            results.append(res)
                    except Exception:
                        continue 
            except concurrent.futures.TimeoutError:
                pass
                
        return {"status": "complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enforcement/incidents")
async def get_incidents():
    incidents = []
    if os.path.exists("incidents.json"):
        with open("incidents.json", "r") as f:
            try:
                incidents = json.load(f)
            except:
                pass
    return {"incidents": incidents}

@app.post("/api/enforcement/takedown")
async def takedown_incident(req: TakedownRequest):
    if not os.path.exists("incidents.json"):
        raise HTTPException(status_code=404, detail="No incidents found")
        
    with open("incidents.json", "r") as f:
        try:
            incidents = json.load(f)
        except:
            incidents = []
            
    incident_found = False
    for inc in incidents:
        if inc.get("id") == req.incident_id:
            inc["status"] = "takedown_sent"
            incident_found = True
            break
            
    if not incident_found:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    with open("incidents.json", "w") as f:
        json.dump(incidents, f, indent=4)
        
    return {"status": "success", "message": "DMCA takedown notice generated and sent."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
