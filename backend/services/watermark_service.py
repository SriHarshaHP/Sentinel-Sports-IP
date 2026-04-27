import os
import cv2
import numpy as np

def _id_to_bits(watermark_id):
    # Convert hex string (e.g. "A1B2C3D4") to 32 bits
    try:
        val = int(watermark_id, 16)
    except:
        val = 0
    return [(val >> i) & 1 for i in range(32)]

def _bits_to_id(bits):
    val = 0
    for i, bit in enumerate(bits):
        if bit:
            val |= (1 << i)
    return f"{val:08X}"

def embed_watermark(video_path, watermark_id="00000001"):
    output_path = video_path.replace(".mp4", f"_protected_{watermark_id}.mp4")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {video_path}")
        
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    bits = _id_to_bits(watermark_id)
    # Create 8x8 cell grid (16x16 pixels, each cell is 2x2)
    # Even cells (r+c%2 == 0) are Reference (0), Odd are Data
    dna_mask = np.zeros((16, 16), dtype=np.uint8)
    bit_idx = 0
    for r in range(0, 16, 2):
        for c in range(0, 16, 2):
            if ((r//2) + (c//2)) % 2 != 0 and bit_idx < 32:
                if bits[bit_idx]:
                    dna_mask[r:r+2, c:c+2] = 1
                bit_idx += 1

    while True:
        ret, frame = cap.read()
        if not ret: break
        
        # Continuously embed the DNA grid in every frame so it survives trimming
        roi = frame[0:16, 0:16, 0].astype(np.int16)
        roi = np.clip(roi + (dna_mask * 8), 0, 255) # Slightly stronger (+8) for 2x2 cells
        frame[0:16, 0:16, 0] = roi.astype(np.uint8)
        
        out.write(frame)
    cap.release(); out.release()
    return output_path

def detect_watermark(video_path):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened(): return None
    
    bit_votes = [0] * 32
    valid_frames = 0
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret or frame_count > 150: break
        roi = frame[0:16, 0:16, 0].astype(np.int32)
        
        # Decode the 32 bits from the 8x8 cell grid
        bit_idx = 0
        for r in range(0, 16, 2):
            for c in range(0, 16, 2):
                if ((r//2) + (c//2)) % 2 != 0 and bit_idx < 32:
                    # Data cell vs surrounding reference cells mean
                    cell_mean = np.mean(roi[r:r+2, c:c+2])
                    # Simple local reference: check a neighboring cell that is definitely a reference cell
                    ref_r, ref_c = r, c-2 if c >= 2 else c+2
                    ref_mean = np.mean(roi[ref_r:ref_r+2, ref_c:ref_c+2])
                    
                    if cell_mean > (ref_mean + 1.5):
                        bit_votes[bit_idx] += 1
                    bit_idx += 1
        valid_frames += 1
        frame_count += 1
    
    cap.release()
    if valid_frames == 0: return None
    
    # Consolidate votes (require > 50% of frames to agree on a bit)
    final_bits = [1 if v > (valid_frames // 2) else 0 for v in bit_votes]
    
    # Validation: If all bits are 0, it's probably not watermarked
    if sum(final_bits) == 0: return None
    
    return _bits_to_id(final_bits)

