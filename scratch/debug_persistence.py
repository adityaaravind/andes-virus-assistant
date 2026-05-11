
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

from alerts.persistent_kv import kv_get

key = "fear_index_votes"
data = kv_get(key)

if data:
    print(f"Data found for {key}")
    print(f"Vote count: {len(data.get('votes', []))}")
else:
    print(f"No data found for {key}")

print(f"QDRANT_URL: {os.getenv('QDRANT_URL')}")
