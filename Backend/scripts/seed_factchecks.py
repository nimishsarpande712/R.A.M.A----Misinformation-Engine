# backend/scripts/seed_factchecks.py
"""
Seed fact checks from JSON file into MongoDB.
Run from Backend folder: python scripts/seed_factchecks.py
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path so we can import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB = os.getenv("MONGODB_DB", "rama_misinfo")

if not MONGODB_URI:
    print("❌ Error: MONGODB_URI not set in .env file")
    sys.exit(1)

print(f"🔌 Connecting to MongoDB...")
print(f"   Database: {MONGODB_DB}")

try:
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB]
    
    # Test connection
    client.server_info()
    print(f"✅ MongoDB connected successfully!")
    
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    sys.exit(1)

# Load fact checks from JSON
json_path = Path(__file__).parent.parent / "data" / "fact_checks.json"

if not json_path.exists():
    print(f"❌ Error: File not found at {json_path}")
    sys.exit(1)

print(f"\n📁 Loading data from: {json_path}")

try:
    data = json.loads(json_path.read_text(encoding="utf-8"))
    
    # Handle both list format and dict with 'items' key
    if isinstance(data, dict) and "items" in data:
        docs = data["items"]
    elif isinstance(data, list):
        docs = data
    else:
        print(f"❌ Invalid JSON format")
        sys.exit(1)
        
except json.JSONDecodeError as e:
    print(f"❌ JSON parse error: {e}")
    sys.exit(1)

print(f"   Found {len(docs)} documents")

# Normalize documents (ensure _id present)
for d in docs:
    if "_id" not in d:
        d["_id"] = d.get("id") or d.get("claim", "unknown")[:80]

# Insert into MongoDB
collection_name = "verified_claims"
collection = db[collection_name]

print(f"\n📥 Inserting into collection: {collection_name}")

# Use upsert to avoid duplicates
inserted = 0
updated = 0
for doc in docs:
    result = collection.update_one(
        {"_id": doc["_id"]},
        {"$set": doc},
        upsert=True
    )
    if result.upserted_id:
        inserted += 1
    elif result.modified_count > 0:
        updated += 1

print(f"\n✅ Done!")
print(f"   Inserted: {inserted}")
print(f"   Updated: {updated}")
print(f"   Total in collection: {collection.count_documents({})}")
