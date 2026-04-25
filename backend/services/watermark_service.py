import os
import cv2
import numpy as np

def embed_watermark(video_path, watermark_id="ORG_0001"):
    # Output path
    output_path = video_path.replace(".mp4", f"_protected_{watermark_id}.mp4")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video for watermarking: {video_path}")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    frame_count = 0
    # Sentinel DNA v2: A 16x16 bit pattern injected into the luminance channel
    # This survives block-based compression (8x8 blocks) much better
    dna_pattern = np.zeros((16, 16), dtype=np.uint8)
    # Simple 4-quadrant checkerboard pattern
    dna_pattern[0:8, 0:8] = 1
    dna_pattern[8:16, 8:16] = 1

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_count < 150: 
            # Inject subtle luma modulation (+5 units) in the top-left 16x16 pixels
            roi = frame[0:16, 0:16, 0].astype(np.int16)
            roi = np.clip(roi + (dna_pattern * 5), 0, 255)
            frame[0:16, 0:16, 0] = roi.astype(np.uint8)
                
        out.write(frame)
        frame_count += 1
        
    cap.release()
    out.release()
    return output_path

def detect_watermark(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
        
    dna_pattern = np.zeros((16, 16), dtype=np.uint8)
    dna_pattern[0:8, 0:8] = 1
    dna_pattern[8:16, 8:16] = 1
    
    votes = 0
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret or frame_count > 150: 
            break
            
        # Differential check: Are 'on' pixels brighter than 'off' pixels in the 16x16 grid?
        roi = frame[0:16, 0:16, 0].astype(np.int32)
        
        on_pixels = roi[dna_pattern == 1]
        off_pixels = roi[dna_pattern == 0]
        
        if len(on_pixels) > 0 and len(off_pixels) > 0:
            avg_on = np.mean(on_pixels)
            avg_off = np.mean(off_pixels)
            
            # Since we modulate by +5, avg_on should be significantly higher
            # We use a threshold of 1.0 for high robustness
            if avg_on > (avg_off + 1.0):
                votes += 1
            
        frame_count += 1
        
    cap.release()
    # Require 75/150 frames for a positive match
    if votes > 75:
        return "ORG_0001"
    return None
