
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    from qdrant_client import QdrantClient
    url = os.getenv("QDRANT_URL")
    key = os.getenv("QDRANT_API_KEY")
    
    if not url:
        print("QDRANT_URL not set")
        sys.exit(0)
        
    client = QdrantClient(url=url, api_key=key)
    collections = client.get_collections().collections
    print(f"Collections: {[c.name for c in collections]}")
    
    for col in collections:
        count = client.count(col.name).count
        print(f"Collection {col.name}: {count} points")
        
        # Peek at a few points
        points = client.scroll(col.name, limit=5)[0]
        for p in points:
            print(f"  Point {p.id}: {p.payload.get('key', 'no-key')}")

except Exception as e:
    print(f"Error: {e}")
