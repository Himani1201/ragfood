import os
import time
from dotenv import load_dotenv
from upstash_vector import Index
from requests.exceptions import RequestException, Timeout, ConnectionError

# Load environment
load_dotenv()

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
TIMEOUT = 30  # seconds


class UpstashClient:
    """Wrapper for Upstash Vector with retry logic and error handling"""
    
    def __init__(self):
        """Initialize Upstash client from environment variables"""
        try:
            url = os.getenv("UPSTASH_VECTOR_REST_URL")
            token = os.getenv("UPSTASH_VECTOR_REST_TOKEN")
            
            if not url or not token:
                raise ValueError("Missing UPSTASH_VECTOR_REST_URL or UPSTASH_VECTOR_REST_TOKEN in .env")
            
            self.index = Index(url=url, token=token)
            self._verify_connection()
        except Exception as e:
            print(f"❌ Failed to initialize Upstash: {e}")
            raise
    
    def _verify_connection(self):
        """Test connection on startup"""
        try:
            info = self.index.info()
            print(f"✅ Connected to Upstash Vector")
            print(f"   Vectors in index: {info.vector_count}")
            print(f"   Dimension: {info.dimension}")
            return True
        except Exception as e:
            raise ConnectionError(f"Cannot reach Upstash: {e}")
    
    def upsert_with_retry(self, vectors):
        """
        Upsert vectors with exponential backoff retry.
        
        Args:
            vectors: List of tuples (id, text, metadata)
        
        Returns:
            Response from Upstash
        """
        for attempt in range(MAX_RETRIES):
            try:
                return self.index.upsert(vectors)
            except (Timeout, ConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️  Upsert attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Upsert failed after {MAX_RETRIES} attempts: {e}")
                    raise
            except RequestException as e:
                print(f"❌ Request error during upsert: {e}")
                raise
    
    def query_with_retry(self, question, top_k=3):
        """
        Query with exponential backoff retry.
        
        Args:
            question: Query text
            top_k: Number of top results to return
        
        Returns:
            List of query results with metadata
        """
        for attempt in range(MAX_RETRIES):
            try:
                return self.index.query(
                    data=question,
                    top_k=top_k,
                    include_metadata=True
                )
            except (Timeout, ConnectionError) as e:
                if attempt < MAX_RETRIES - 1:
                    wait_time = RETRY_DELAY * (2 ** attempt)
                    print(f"⚠️  Query attempt {attempt + 1} failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Query failed after {MAX_RETRIES} attempts: {e}")
                    raise
            except RequestException as e:
                print(f"❌ Request error during query: {e}")
                raise
    
    def batch_upsert(self, vectors, batch_size=500):
        """
        Upsert vectors in batches for better performance.
        
        Args:
            vectors: List of tuples (id, text, metadata)
            batch_size: Number of vectors per batch
        
        Returns:
            Total number of vectors upserted
        """
        total_upserted = 0
        
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            try:
                self.upsert_with_retry(batch)
                total_upserted += len(batch)
                print(f"✅ Uploaded {total_upserted}/{len(vectors)} vectors")
            except Exception as e:
                print(f"❌ Batch upsert failed at index {i}: {e}")
                raise
        
        return total_upserted
    
    def get_info(self):
        """Get index information"""
        try:
            return self.index.info()
        except Exception as e:
            print(f"❌ Failed to get index info: {e}")
            raise
