import chromadb
from chromadb.config import Settings

class VectorDBService:
    def __init__(self, persist_directory="./chroma_db"):
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.collection = self.client.get_or_create_collection(name="video_hashes")
        # Separate collections for each hash type (multi-hash support)
        self.dhash_collection = self.client.get_or_create_collection(name="video_dhashes")
        self.whash_collection = self.client.get_or_create_collection(name="video_whashes")

    def _hex_to_vector(self, h: str, target_dim=256):
        """Convert hex hash to binary float vector with consistent dimensionality."""
        binary_str = bin(int(h, 16))[2:].zfill(target_dim)
        # Truncate or pad to target_dim
        if len(binary_str) > target_dim:
            binary_str = binary_str[:target_dim]
        elif len(binary_str) < target_dim:
            binary_str = binary_str.zfill(target_dim)
        return [float(b) for b in binary_str]

    def insert_hashes(self, video_id: str, hashes: list[str]):
        """Insert phash vectors (backward compatible, now 256-bit)."""
        vectors = []
        ids = []
        metadatas = []
        
        for i, h in enumerate(hashes):
            vector = self._hex_to_vector(h)
            vectors.append(vector)
            ids.append(f"{video_id}_frame_{i}")
            metadatas.append({"video_id": video_id, "frame": i, "hash": h})
            
        self.collection.add(
            embeddings=vectors,
            ids=ids,
            metadatas=metadatas
        )

    def insert_multi_hashes(self, video_id: str, multi_hashes: list[dict]):
        """
        Insert multi-hash fingerprints (phash, dhash, whash) into separate collections.
        This enables cross-algorithm voting for much higher accuracy.
        """
        p_vectors, p_ids, p_metas = [], [], []
        d_vectors, d_ids, d_metas = [], [], []
        w_vectors, w_ids, w_metas = [], [], []
        
        for i, mh in enumerate(multi_hashes):
            frame_id = f"{video_id}_frame_{i}"
            meta = {"video_id": video_id, "frame": i}
            
            # phash
            p_vectors.append(self._hex_to_vector(mh["phash"]))
            p_ids.append(frame_id)
            p_metas.append({**meta, "hash": mh["phash"]})
            
            # dhash
            d_vectors.append(self._hex_to_vector(mh["dhash"]))
            d_ids.append(frame_id)
            d_metas.append({**meta, "hash": mh["dhash"]})
            
            # whash
            w_vectors.append(self._hex_to_vector(mh["whash"]))
            w_ids.append(frame_id)
            w_metas.append({**meta, "hash": mh["whash"]})
        
        self.collection.add(embeddings=p_vectors, ids=p_ids, metadatas=p_metas)
        self.dhash_collection.add(embeddings=d_vectors, ids=d_ids, metadatas=d_metas)
        self.whash_collection.add(embeddings=w_vectors, ids=w_ids, metadatas=w_metas)

    def search_hash(self, h: str, n_results=1):
        """Search phash collection (backward compatible)."""
        try:
            vector = self._hex_to_vector(h)
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=n_results
            )
            return results
        except Exception as e:
            return {"error": str(e), "distances": [[]]}

    def search_multi_hash(self, multi_hash: dict, n_results=3):
        """
        Search across all hash collections and return combined results.
        Returns a dict with results from each algorithm for voting.
        """
        results = {}
        
        for hash_type, collection in [
            ("phash", self.collection),
            ("dhash", self.dhash_collection),
            ("whash", self.whash_collection),
        ]:
            try:
                h = multi_hash[hash_type]
                vector = self._hex_to_vector(h)
                res = collection.query(
                    query_embeddings=[vector],
                    n_results=n_results
                )
                results[hash_type] = res
            except Exception:
                results[hash_type] = {"distances": [[]], "metadatas": [[]]}
        
        return results

db_service = VectorDBService()
