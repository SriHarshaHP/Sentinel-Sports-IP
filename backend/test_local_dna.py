import os
import shutil
import cv2
from services.watermark_service import embed_watermark, detect_watermark

def local_dna_test():
    # Find any mp4 in the uploads folder to test with
    uploads = [f for f in os.listdir("uploads") if f.endswith(".mp4")]
    if not uploads:
        print("No sample video found in uploads to test.")
        return
    
    test_video = os.path.join("uploads", uploads[0])
    print(f"--- Running Local DNA Test on: {test_video} ---")
    
    # 1. Embed
    print("1. Embedding watermark (10-second coverage, High Intensity)...")
    protected_path = embed_watermark(test_video, "ORG_0001")
    print(f"   - Protected File: {protected_path}")
    
    # 2. Detect
    print("2. Detecting watermark locally...")
    detected = detect_watermark(protected_path)
    print(f"   - Detected ID: {detected}")
    
    if detected == "ORG_0001":
        print("\nSUCCESS: DNA is present locally and robust!")
    else:
        print("\nFAILURE: DNA is still not sticking. This indicates a system library conflict.")

if __name__ == "__main__":
    local_dna_test()
