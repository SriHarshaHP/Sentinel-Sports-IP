import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.db_service import db_service

def delete_video(short_id):
    # Find the full video_id by getting all items and checking the start
    results = db_service.collection.get(include=["metadatas"])
    
    full_id = None
    for meta in results.get("metadatas", []):
        vid_id = meta.get("video_id")
        if vid_id and str(vid_id).upper().startswith(short_id.upper()):
            full_id = vid_id
            break
            
    if not full_id:
        print(f"Could not find video starting with {short_id}")
        return
        
    print(f"Found full video_id: {full_id}. Deleting...")
    
    # Delete from all collections
    db_service.collection.delete(where={"video_id": full_id})
    db_service.dhash_collection.delete(where={"video_id": full_id})
    db_service.whash_collection.delete(where={"video_id": full_id})
    print("Deleted from Chroma DB.")
    
    # Try to delete from protected/ folder
    protected_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'protected'))
    if os.path.exists(protected_dir):
        for f in os.listdir(protected_dir):
            if f.startswith(full_id):
                file_path = os.path.join(protected_dir, f)
                try:
                    os.remove(file_path)
                    print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

if __name__ == "__main__":
    delete_video("3EA0FEDA")
