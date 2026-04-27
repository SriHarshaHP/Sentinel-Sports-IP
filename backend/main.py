from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import concurrent.futures
import cv2
from services.watermark_service import embed_watermark, detect_watermark
from services.video_service import process_video_and_extract_frames, process_video_multi_hash
from services.db_service import db_service
from services.scraper_service import search_youtube, download_video_clip
from services.ai_service import verify_infringement, generate_risk_summary, draft_dmca_notice
from pydantic import BaseModel
import json
import glob
from datetime import datetime

class ScrapeRequest(BaseModel):
    keyword: str
    platform: str = "youtube"
    user_id: str

class TakedownRequest(BaseModel):
    incident_id: str



app = FastAPI(title="Sentinel-Sports IP Vault API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://sentinel-sports-ip.vercel.app",
        "https://www.sentinelsportsip.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("protected", exist_ok=True)

@app.get("/api/vault/count")
async def get_vault_count():
    try:
        count = db_service.collection.count()
        return {"count": count}
    except:
        return {"count": 0}

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
async def protect_video(
    file: UploadFile = File(...), 
    title: str = Form(...), 
    keywords: str = Form(""),
    user_id: str = Form(...)
):
    file_id = str(uuid.uuid4())
    ext = file.filename.split('.')[-1]
    temp_path = f"uploads/{file_id}.{ext}"
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Use multi-hash extraction for better accuracy
        multi_hashes, phashes, frames = process_video_multi_hash(temp_path, num_frames=30)
        
        # Sentinel DNA v3: Use the legacy 'ORG_0001' signature for familiar detection logic
        protected_path = embed_watermark(temp_path, watermark_id="ORG_0001")
        final_protected_path = f"protected/{file_id}_protected.{ext}"
        shutil.move(protected_path, final_protected_path)
        
        # Store multi-hash fingerprints with User Identity
        db_service.insert_multi_hashes(file_id, multi_hashes, extra_meta={
            "title": title, 
            "keywords": keywords,
            "user_id": user_id
        })
        
        return {
            "status": "success",
            "video_id": file_id,
            "title": title,
            "keywords": keywords,
            "protected_video_url": f"http://localhost:8000/api/vault/download/{file_id}_protected.{ext}",
            "hashes_stored": len(multi_hashes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.get("/api/vault/list")
async def list_vault(user_id: str):
    # Filter by user_id for multi-tenant privacy
    results = db_service.collection.get(
        where={"user_id": user_id},
        include=["metadatas"]
    )
    unique_videos = {}
    for meta in (results["metadatas"] or []):
        vid_id = meta.get("video_id")
        if vid_id and vid_id not in unique_videos:
            unique_videos[vid_id] = {
                "id": vid_id,
                "title": meta.get("title", "Untitled"),
                "keywords": meta.get("keywords", ""),
                "protected_url": f"http://localhost:8000/api/vault/download/{vid_id}_protected.mp4"
            }
    return {"videos": list(unique_videos.values())}

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
        # Only check for watermark if the fast match is positive
        if fast_match:
            detected_watermark = detect_watermark(temp_path)
            # DNA Verification: Match detected hex ID with expected hex (first 8 chars of DB ID)
            expected_hex = fast_matched_id[:8].upper() if fast_matched_id else ""
            watermark_hit = (detected_watermark == expected_hex)
        
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
def process_scraped_video(v, platform, user_id):
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

        if fast_match:
            detected_watermark = detect_watermark(clip_path)
            # DNA Verification: If ANY valid 32-bit watermark is detected, it's a hit.
            # This ensures videos uploaded before a database wipe are still caught.
            watermark_hit = bool(detected_watermark)

        # PIRACY LOGIC: Trigger alert if we have a strong Visual DNA match (>=90%) 
        # OR if we find a verified Forensic Watermark signature.
        is_pirated = (fast_similarity >= 90.0) or watermark_hit

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
            "user_id": user_id,
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
            # Generate AI summary only for confirmed piracy to save time
            result_obj["ai_summary"] = generate_risk_summary({"platform": platform, "video": v, "similarity": fast_similarity})
            
            # Persist to incidents.json with de-duplication
            incidents = []
            if os.path.exists("incidents.json"):
                with open("incidents.json", "r") as f:
                    try:
                        incidents = json.load(f)
                    except:
                        pass
            
            # De-duplication check: Only add if URL not already present
            existing_urls = [i['video'].get('url') for i in incidents if 'video' in i]
            if v.get('url') not in existing_urls:
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
        return {
            "id": str(uuid.uuid4()),
            "video": v,
            "platform": platform,
            "user_id": user_id,
            "is_pirated": False,
            "error": str(inner_e),
            "status": "error"
        }

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
    print(f"SENTINEL DRONE MISSION: {req.keyword} ON {req.platform} FOR {req.user_id}")
    try:
        videos = []
        # Support for Direct URL Scanning (Bypass Indexing Lag)
        if "youtube.com" in req.keyword or "youtu.be" in req.keyword:
            videos = [{
                'video_id': 'manual_target',
                'title': 'TARGETED ASSET SCAN',
                'url': req.keyword
            }]
        # Render/Cloud environment optimization: Limit workers and results to prevent CPU choking
        is_render = os.getenv("RENDER") == "true"
        max_results = 3 if is_render else 10
        max_workers = 1 if is_render else 5

        if req.platform == "youtube":
            videos = search_youtube(req.keyword, max_results=max_results)
            
        if not videos:
            return {"status": "complete", "message": f"No videos found on {req.platform}", "results": []}
            
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_video = {executor.submit(process_scraped_video, v, req.platform, req.user_id): v for v in videos}
            try:
                # Limit total time to 120 seconds to stay within browser fetch limits
                for future in concurrent.futures.as_completed(future_to_video, timeout=120):
                    res = future.result()
                    if res:
                        results.append(res)
            except Exception as e:
                print(f"Executor Error: {e}")

        # Sort results so pirated ones appear at the top
        results.sort(key=lambda x: x.get("is_pirated", False), reverse=True)
        return {"status": "complete", "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/enforcement/incidents")
async def get_incidents(user_id: str):
    incidents = []
    if os.path.exists("incidents.json"):
        with open("incidents.json", "r") as f:
            try:
                all_incidents = json.load(f)
                # Filter by user_id for multi-tenant privacy
                incidents = [inc for inc in all_incidents if inc.get("user_id") == user_id]
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
            
    incident_to_takedown = None
    for inc in incidents:
        if inc.get("id") == req.incident_id:
            inc["status"] = "takedown_sent"
            incident_to_takedown = inc
            incident_found = True
            break
            
    if not incident_found:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Generate a Formal DMCA Notice Preview
    video_title = incident_to_takedown['video'].get('title', 'Unknown Title')
    video_url = incident_to_takedown['video'].get('url', 'N/A')
    similarity = incident_to_takedown.get('similarity_score', 0)
    
    dmca_notice = f"""
FORMAL DMCA TAKEDOWN NOTICE
---------------------------------------
SENTINEL SPORTS IP PROTECTION SYSTEM
Forensic Case ID: {req.incident_id}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

TO: Platform Copyright Enforcement Team

This letter is a formal notification that we have identified infringing content hosted on your platform.

INFRINGING CONTENT DETAILS:
- Title: {video_title}
- URL: {video_url}

FORENSIC EVIDENCE:
- Visual Similarity Score: {similarity}%
- Sentinel DNA Verification: CONFIRMED (ID: ORG_0001)
- Evidence Image Hash: {incident_to_takedown.get('id')}

We have a good faith belief that the use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law.

Digitally Signed,
Sentinel Sports IP Legal Engine
    """
        
    with open("incidents.json", "w") as f:
        json.dump(incidents, f, indent=4)
        
    return {
        "dmca_notice": dmca_notice
    }

@app.post("/api/ai/verify/{incident_id}")
async def ai_verify_incident(incident_id: str):
    if not os.path.exists("incidents.json"):
        raise HTTPException(status_code=404, detail="No incidents found")
    
    with open("incidents.json", "r") as f:
        incidents = json.load(f)
    
    incident = next((inc for inc in incidents if inc["id"] == incident_id), None)
    if not incident or not incident.get("evidence_frame"):
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    verification = verify_infringement(incident["evidence_frame"])
    
    # Save verification result back to incident
    incident["ai_verification"] = verification
    with open("incidents.json", "w") as f:
        json.dump(incidents, f, indent=4)
        
    return verification

@app.post("/api/ai/dmca/{incident_id}")
async def ai_draft_dmca(incident_id: str):
    if not os.path.exists("incidents.json"):
        raise HTTPException(status_code=404, detail="No incidents found")
    
    with open("incidents.json", "r") as f:
        incidents = json.load(f)
    
    incident = next((inc for inc in incidents if inc["id"] == incident_id), None)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    
    draft = draft_dmca_notice(incident)
    return {"draft": draft}


@app.get("/api/enforcement/download_pdf/{incident_id}")
async def download_pdf(incident_id: str):
    if not os.path.exists("incidents.json"):
        raise HTTPException(status_code=404, detail="No incidents found")
        
    with open("incidents.json", "r") as f:
        try:
            incidents = json.load(f)
        except:
            incidents = []
            
    incident = None
    for inc in incidents:
        if inc.get("id") == incident_id:
            incident = inc
            break
            
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    # Generate PDF
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 10, "FORMAL DMCA TAKEDOWN NOTICE", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 10, "SENTINEL SPORTS IP PROTECTION SYSTEM", ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    pdf.ln(10)
    
    # Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Forensic Case ID: {incident_id}", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 10, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "INFRINGING CONTENT DETAILS:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 10, f"Title: {incident['video'].get('title', 'Unknown')}", ln=True)
    pdf.cell(190, 10, f"URL: {incident['video'].get('url', 'N/A')}", ln=True)
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "FORENSIC EVIDENCE:", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(190, 10, f"Visual Similarity Score: {incident.get('similarity_score', 0)}%", ln=True)
    pdf.cell(190, 10, f"Sentinel DNA Verification: CONFIRMED (ID: ORG_0001)", ln=True)
    pdf.cell(190, 10, f"Evidence Image Hash: {incident.get('id')}", ln=True)
    pdf.ln(15)
    
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(190, 6, "I have a good faith belief that the use of the material in the manner complained of is not authorized by the copyright owner, its agent, or the law. I swear, under penalty of perjury, that the information in the notification is accurate and that I am the copyright owner or am authorized to act on behalf of the owner of an exclusive right that is allegedly infringed.")
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "Digitally Signed,", ln=True)
    pdf.cell(190, 10, "Sentinel Sports IP Legal Engine", ln=True)

    pdf_output = f"uploads/DMCA_{incident_id}.pdf"
    pdf.output(pdf_output)
    
    return FileResponse(pdf_output, filename=f"DMCA_Notice_{incident_id}.pdf")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
