import cv2
import os
from services.hash_service import generate_phash, generate_multi_hash
from PIL import Image

def process_video_and_extract_frames(video_path, num_frames=5):
    """
    Extract frames and generate perceptual hashes.
    Returns (hashes, frames) where hashes are simple phash strings
    for backward compatibility with the vector DB.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    extracted_frames = []
    hashes = []
    
    frames_to_grab = min(num_frames, total_frames) if total_frames > 0 else num_frames
    step = total_frames / max(1, frames_to_grab) if total_frames > 0 else fps
    
    for i in range(frames_to_grab):
        frame_id = int(step * i)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            extracted_frames.append(pil_img)
            hashes.append(generate_phash(pil_img))
            
    cap.release()
    return hashes, extracted_frames


def process_video_multi_hash(video_path, num_frames=15):
    """
    Enhanced frame extraction with multi-hash fingerprinting.
    Optimized for Render Free Tier: Reduced default frames to 15.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Cannot open video")

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    extracted_frames = []
    multi_hashes = []
    phashes = []
    
    frames_to_grab = min(num_frames, total_frames) if total_frames > 0 else num_frames
    step = total_frames / max(1, frames_to_grab) if total_frames > 0 else fps
    
    prev_phash = None
    
    for i in range(frames_to_grab):
        frame_id = int(step * i)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            
            mh = generate_multi_hash(pil_img)
            
            # Skip near-duplicate frames (scene-change detection)
            # If the phash is too similar to the previous frame, skip it
            if prev_phash is not None:
                from services.hash_service import hamming_distance
                dist = hamming_distance(mh["phash"], prev_phash)
                if dist < 5:  # Nearly identical frame
                    continue
            
            prev_phash = mh["phash"]
            extracted_frames.append(pil_img)
            multi_hashes.append(mh)
            phashes.append(mh["phash"])
            
    cap.release()
    return multi_hashes, phashes, extracted_frames
