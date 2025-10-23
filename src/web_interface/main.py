from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os

# Add parent directory to path so we can import the CLI modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Turnkey Coach Tools - Web Interface")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Mock data for preview
MOCK_CLIENTS = [
    {"id": 1, "full_name": "Sarah Mitchell", "last_workout": "2025-01-12", "status": "active"},
    {"id": 2, "full_name": "Mike Thompson", "last_workout": "2025-01-11", "status": "needs_attention"},
    {"id": 3, "full_name": "Emma Rodriguez", "last_workout": "2025-01-10", "status": "active"},
    {"id": 4, "full_name": "James Wilson", "last_workout": "2025-01-09", "status": "active"},
]

MOCK_FEED_DATA = [
    {
        "type": "workout_completed",
        "timestamp": "2025-01-12 14:30",
        "client": "Sarah Mitchell",
        "title": "Upper Body Strength - Completed!",
        "details": "Bench Press: 3x8 @ 135lbs | Pull-ups: 3x6 | Overhead Press: 3x10 @ 85lbs",
        "status": "completed"
    },
    {
        "type": "message", 
        "timestamp": "2025-01-12 09:15",
        "client": "Sarah Mitchell",
        "author": "Sarah",
        "text": "Feeling really strong today! Ready to crush this workout 💪",
        "avatar": "SM"
    },
    {
        "type": "metric_logged",
        "timestamp": "2025-01-11 22:00", 
        "client": "Sarah Mitchell",
        "metric": "Sleep Quality",
        "value": "8.5/10",
        "note": "Great sleep, ready for tomorrow!"
    },
    {
        "type": "workout_assigned",
        "timestamp": "2025-01-11 16:45",
        "client": "Mike Thompson", 
        "title": "Lower Body Power",
        "details": "Squats, Deadlifts, Box Jumps scheduled for tomorrow",
        "status": "assigned"
    }
]

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "clients": MOCK_CLIENTS,
        "total_clients": len(MOCK_CLIENTS),
        "active_today": 3,
        "pending_reviews": 2
    })

@app.get("/client/{client_id}/feed", response_class=HTMLResponse)
async def client_feed(request: Request, client_id: int):
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), MOCK_CLIENTS[0])
    return templates.TemplateResponse("feed.html", {
        "request": request,
        "client": client,
        "feed_items": MOCK_FEED_DATA
    })

@app.get("/client/{client_id}/workouts", response_class=HTMLResponse)
async def workout_browser(request: Request, client_id: int):
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), MOCK_CLIENTS[0])
    return templates.TemplateResponse("workouts.html", {
        "request": request,
        "client": client
    })

@app.get("/client/{client_id}/chat", response_class=HTMLResponse)
async def ai_chat(request: Request, client_id: int):
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), MOCK_CLIENTS[0])
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "client": client
    })

@app.get("/client/{client_id}/upload", response_class=HTMLResponse)
async def upload_workouts(request: Request, client_id: int):
    client = next((c for c in MOCK_CLIENTS if c["id"] == client_id), MOCK_CLIENTS[0])
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "client": client
    })

if __name__ == "__main__":
    print("🚀 Starting Turnkey Coach Tools Web Interface...")
    print("📱 Open http://localhost:8000 in your browser")
    print("📊 Press Ctrl+C to stop the server")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
    except KeyboardInterrupt:
        print("\n✅ Server stopped gracefully!")
