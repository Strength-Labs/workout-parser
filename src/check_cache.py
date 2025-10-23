#!/usr/bin/env python3
"""
Check cache state for Paul Nelson
"""
import os
import json
from src.api_client import get_access_token, get_clients
from src.directory_migration import get_client_dir
from src.encoding_utils import safe_json_load

# Get Paul Nelson's info
token, user_id = get_access_token()
clients = get_clients(token, user_id)
paul = None
for client in clients:
    if "paul nelson" in client['full_name'].lower():
        paul = client
        break

if not paul:
    print("❌ Paul Nelson not found")
    exit(1)

client_id = paul['id']
client_dir = get_client_dir(client_id)
workout_cache_path = os.path.join(client_dir, f"workouts_user_{client_id}.json")

print(f"Client: {paul['full_name']} (ID: {client_id})")
print(f"Client dir: {client_dir}")
print(f"Cache path: {workout_cache_path}")

# Check if directory exists
if not os.path.exists(client_dir):
    print("❌ Client directory does not exist")
    exit(1)
print("✅ Client directory exists")

# Check if cache file exists
if not os.path.exists(workout_cache_path):
    print("❌ Cache file does not exist - this explains the full download!")
    # List what files ARE in the directory
    files = os.listdir(client_dir)
    print(f"Files in client dir: {files}")
    exit(1)
print("✅ Cache file exists")

# Check cache file size and contents
file_size = os.path.getsize(workout_cache_path)
print(f"Cache file size: {file_size:,} bytes")

# Try to load the cache
print("Loading cache...")
try:
    workouts = safe_json_load(workout_cache_path, default=[])
    if not workouts:
        print("❌ Cache loaded but is empty")
    else:
        print(f"✅ Cache loaded: {len(workouts)} workouts")
        
        # Check for valid workouts
        valid_workouts = [w for w in workouts if w.get('workout_date') and w.get('id')]
        print(f"Valid workouts: {len(valid_workouts)}")
        
        if valid_workouts:
            print(f"Date range: {min(w['workout_date'] for w in valid_workouts)} to {max(w['workout_date'] for w in valid_workouts)}")
        else:
            print("❌ No valid workouts - this triggers full download!")
            
except Exception as e:
    print(f"❌ Error loading cache: {e}")