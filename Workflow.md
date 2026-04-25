#Workflow


Phase 1: The Vault (Asset Protection)
Upload Video
User submits original content
Watermark Injection
Embed unique identifier using invisible watermarking
Frame Extraction
Extract frames using FFmpeg
Hash Generation
Generate pHash for each frame
Storage
Store watermark ID, frame hashes, and metadata
Use vector database such as ChromaDB, Pinecone, or Milvus
Output
Protected video
Indexed fingerprint database



Phase 2: The Sentinel (Continuous Monitoring)
Execution Mode
Background worker or cron job running periodically
Steps
Keyword Scraping
Query platforms using predefined keywords
Metadata Filtering
Filter recent uploads (last 1 hour)
Limit to top 100 videos
Fast Check (Thumbnail Matching)
Download thumbnails
Generate pHash
Compare with Vault hashes
Threshold: 70 percent similarity or higher
Deep Check (Video Verification)
Download first 5 seconds
Extract frames
Detect watermark
Output
List of suspected infringements



Phase 3: The Enforcement (Action Dashboard)
Features
Risk Map
Display:
URLs of suspected videos
Similarity score
Timestamp
Proof Engine
Show:
Original versus detected frame
Highlight detected watermark ID
One-Click Takedown
Generate DMCA takedown notice
Optional API-based reporting to platforms