import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from sentence_transformers import SentenceTransformer
import pickle

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_title: str
    text: str
    page: Optional[int] = None
    chunk_index: int = 0
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self):
        data = asdict(self)
        # Convert numpy array to list for JSON serialization
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data

class VectorStore:
    def __init__(self, storage_dir="vector_store", model_name="all-MiniLM-L6-v2"):
        """
        Initialize vector store with sentence transformer model
        all-MiniLM-L6-v2: Fast, good quality, 384 dimensions
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.chunks_file = self.storage_dir / "chunks.pkl"
        self.embeddings_file = self.storage_dir / "embeddings.npy"
        self.metadata_file = self.storage_dir / "metadata.json"
        
        # Load sentence transformer model
        print(f"Loading embedding model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        print("Model loaded successfully!")
        
        # Load existing data
        self.chunks: List[Chunk] = []
        self.embeddings: Optional[np.ndarray] = None
        self._load_data()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        """
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():
                chunks.append(chunk)
        
        return chunks
    
    def add_document(self, doc_id: str, doc_title: str, text: str, 
                     page_count: Optional[int] = None) -> int:
        """
        Add a document to the vector store by chunking and embedding it
        Returns the number of chunks created
        """
        # Chunk the text
        text_chunks = self.chunk_text(text)
        
        # Parse page markers if present (for PDFs)
        chunks_with_pages = self._extract_page_info(text_chunks, text)
        
        # Create Chunk objects
        new_chunks = []
        for idx, (chunk_text, page_num) in enumerate(chunks_with_pages):
            chunk = Chunk(
                chunk_id=f"{doc_id}_chunk_{idx}",
                doc_id=doc_id,
                doc_title=doc_title,
                text=chunk_text,
                page=page_num,
                chunk_index=idx
            )
            new_chunks.append(chunk)
        
        # Generate embeddings
        chunk_texts = [c.text for c in new_chunks]
        embeddings = self.model.encode(chunk_texts, convert_to_numpy=True)
        
        # Add embeddings to chunks
        for chunk, embedding in zip(new_chunks, embeddings):
            chunk.embedding = embedding
        
        # Add to store
        self.chunks.extend(new_chunks)
        
        # Update embeddings matrix
        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])
        
        # Save data
        self._save_data()
        
        return len(new_chunks)
    
    def _extract_page_info(self, chunks: List[str], full_text: str) -> List[tuple]:
        """
        Extract page numbers from chunks if they contain page markers
        Returns list of (chunk_text, page_number) tuples
        """
        result = []
        
        # Check if text has page markers (like "--- Page X ---")
        if "--- Page" in full_text:
            for chunk in chunks:
                # Find page marker in chunk
                page_num = None
                for line in chunk.split('\n'):
                    if '--- Page' in line:
                        try:
                            page_num = int(line.split('Page')[1].split('---')[0].strip())
                            break
                        except:
                            pass
                result.append((chunk, page_num))
        else:
            # No page markers, all chunks have None for page
            result = [(chunk, None) for chunk in chunks]
        
        return result
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Search for top-k most similar chunks to the query
        Returns list of dicts with doc_title, chunk_text, page, and similarity score
        """
        if not self.chunks or self.embeddings is None:
            return []
        
        # Embed the query
        query_embedding = self.model.encode([query], convert_to_numpy=True)[0]
        
        # Calculate cosine similarity
        similarities = self._cosine_similarity(query_embedding, self.embeddings)
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Build results
        results = []
        for idx in top_indices:
            chunk = self.chunks[idx]
            results.append({
                'doc_title': chunk.doc_title,
                'doc_id': chunk.doc_id,
                'chunk_text': chunk.text,
                'page': chunk.page,
                'chunk_index': chunk.chunk_index,
                'similarity': float(similarities[idx])
            })
        
        return results
    
    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks associated with a document
        Returns the number of chunks deleted
        """
        # Find indices of chunks to keep
        indices_to_keep = [i for i, chunk in enumerate(self.chunks) if chunk.doc_id != doc_id]
        indices_to_delete = [i for i, chunk in enumerate(self.chunks) if chunk.doc_id == doc_id]
        
        num_deleted = len(indices_to_delete)
        
        if num_deleted == 0:
            return 0
        
        # Update chunks and embeddings
        self.chunks = [self.chunks[i] for i in indices_to_keep]
        
        if self.embeddings is not None:
            self.embeddings = self.embeddings[indices_to_keep]
        
        # Save updated data
        self._save_data()
        
        return num_deleted
    
    def _cosine_similarity(self, query_vec: np.ndarray, embeddings: np.ndarray) -> np.ndarray:
        """
        Calculate cosine similarity between query and all embeddings
        """
        # Normalize vectors
        query_norm = query_vec / np.linalg.norm(query_vec)
        embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        
        # Calculate dot product (cosine similarity for normalized vectors)
        similarities = np.dot(embeddings_norm, query_norm)
        
        return similarities
    
    def _save_data(self):
        """Save chunks and embeddings to disk"""
        # Save chunks (without embeddings in pickle to save space)
        chunks_data = []
        for chunk in self.chunks:
            chunk_dict = {
                'chunk_id': chunk.chunk_id,
                'doc_id': chunk.doc_id,
                'doc_title': chunk.doc_title,
                'text': chunk.text,
                'page': chunk.page,
                'chunk_index': chunk.chunk_index
            }
            chunks_data.append(chunk_dict)
        
        with open(self.chunks_file, 'wb') as f:
            pickle.dump(chunks_data, f)
        
        # Save embeddings separately
        if self.embeddings is not None:
            np.save(self.embeddings_file, self.embeddings)
        
        # Save metadata
        metadata = {
            'num_chunks': len(self.chunks),
            'embedding_dim': self.embeddings.shape[1] if self.embeddings is not None else 0
        }
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def _load_data(self):
        """Load chunks and embeddings from disk"""
        if self.chunks_file.exists():
            with open(self.chunks_file, 'rb') as f:
                chunks_data = pickle.load(f)
            
            self.chunks = [Chunk(**data) for data in chunks_data]
        
        if self.embeddings_file.exists():
            self.embeddings = np.load(self.embeddings_file)
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        doc_ids = set(chunk.doc_id for chunk in self.chunks)
        return {
            'total_chunks': len(self.chunks),
            'total_documents': len(doc_ids),
            'embedding_dim': self.embeddings.shape[1] if self.embeddings is not None else 0
        }