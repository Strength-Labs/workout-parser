#!/usr/bin/env python3
"""
Quick test to isolate where the AI chat hangs
"""
import sys
from src.api_client import get_access_token, get_clients, get_workout_history_headless

print("Testing headless workout history function...")

# Get auth
print("1. Getting authentication...")
token, user_id = get_access_token()
if not token:
    print("❌ Auth failed")
    sys.exit(1)
print("✅ Auth successful")

# Get clients
print("2. Getting clients...")
clients = get_clients(token, user_id)
if not clients:
    print("❌ No clients")
    sys.exit(1)
print(f"✅ Got {len(clients)} clients")

# Find Paul Nelson (client 35)
paul = None
for client in clients:
    if "paul nelson" in client['full_name'].lower():
        paul = client
        break

if not paul:
    print("❌ Paul Nelson not found")
    # Use first client as fallback
    paul = clients[0]
    print(f"Using {paul['full_name']} instead")

print(f"3. Testing headless workout history for {paul['full_name']}...")
try:
    workouts = get_workout_history_headless(token, paul)
    print(f"✅ Success! Got {len(workouts)} workouts")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()