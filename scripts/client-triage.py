#!/usr/bin/env python3
"""
Client Triage Tool — Red flag scanner for Karl's coaching roster.

Uses the TKC API (via workout-parser credentials) to analyze all clients
and surface trouble spots: missed workouts, stalled progress, MIA clients,
incomplete workouts, etc.

Outputs a markdown report suitable for LLM summarization or direct reading.
"""
import sys
import os
import json
import requests
from datetime import datetime, timedelta, date
from collections import defaultdict

# Resolve repo root from script location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, REPO_ROOT)
os.chdir(REPO_ROOT)

from src.tools.format_tool import format_workouts_to_markup

# --- Config ---
API_BASE_URL = "https://app.turnkey.coach"


def get_token():
    """Get API token using workout-parser's stored credentials."""
    from src.settings import get_stored_credentials
    email, password = get_stored_credentials()
    resp = requests.post(
        f"{API_BASE_URL}/users/tokens/sign_in",
        headers={"Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    resp.raise_for_status()
    data = resp.json()
    return data["token"], data["resource_owner"]["id"]


def get_clients(token, user_id):
    """Fetch all clients for the coach."""
    resp = requests.get(
        f"{API_BASE_URL}/api/v1/users/{user_id}/clients",
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    rels = resp.json()
    seen = set()
    clients = []
    for r in rels:
        c = r.get("client", {})
        cid = c.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            clients.append({
                "id": cid,
                "name": c.get("full_name", "Unknown"),
                "email": c.get("email", ""),
                "time_zone": c.get("time_zone", "America/Chicago"),
            })
    return sorted(clients, key=lambda x: x["name"])


def get_recent_workouts(token, client_id, days=21):
    """Fetch workouts from the last N days for a client.
    
    Uses the TKC API pattern: GET /api/v1/workouts?user_id=X
    This returns a summary list. For triage we only need dates + completion status,
    so we fetch individual workout details only when needed.
    """
    start_date = (date.today() - timedelta(days=days)).isoformat()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get workout summaries
    resp = requests.get(
        f"{API_BASE_URL}/api/v1/workouts",
        headers=headers,
        params={
            "user_id": client_id,
            "sort": "ascending",
            "published": True,
            "start_date": start_date,
        },
    )
    if resp.status_code != 200:
        return []
    
    summaries = resp.json()
    
    # Fetch details for each workout (we need completion status + exercises)
    workouts = []
    for s in summaries:
        detail_resp = requests.get(
            f"{API_BASE_URL}/api/v1/workouts/{s['id']}",
            headers=headers,
        )
        if detail_resp.status_code == 200:
            workouts.append(detail_resp.json())
    
    return workouts


def get_recent_messages(token, client_name, all_conversations):
    """Get recent messages from a client's conversation."""
    import re
    import html as h
    
    messages = []
    # Find this client's conversation
    for c in all_conversations:
        display = c.get("display_name") or ""
        if display and client_name.lower() in display.lower():
            convo_id = c["id"]
            resp = requests.get(
                f"{API_BASE_URL}/api/v1/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={"conversation_id": convo_id, "page": 1, "per_page": 10},
            )
            if resp.status_code == 200:
                for m in resp.json():
                    body = h.unescape(re.sub("<[^>]+>", "", m.get("body", "")))
                    sender = m.get("user", {}).get("full_name", "?")
                    ts = m.get("created_at", "")[:10]
                    messages.append({"date": ts, "sender": sender, "body": body[:200]})
            break
    return messages


def extract_comments(workouts):
    """Extract all comments from workout data."""
    import re
    import html as h
    
    comments = []
    for w in workouts:
        w_date = w.get("workout_date", "")
        # Workout-level comments
        for c in w.get("comments", []) or []:
            body = h.unescape(re.sub("<[^>]+>", "", c.get("body", "")))
            user = c.get("user", {}).get("full_name", "?")
            comments.append({"date": w_date, "user": user, "body": body[:200], "context": "workout"})
        # Exercise-level comments
        for ae in w.get("assigned_exercises", []) or []:
            ex_name = ae.get("exercise", {}).get("name", "?")
            for c in ae.get("comments", []) or []:
                body = h.unescape(re.sub("<[^>]+>", "", c.get("body", "")))
                user = c.get("user", {}).get("full_name", "?")
                comments.append({"date": w_date, "user": user, "body": body[:200], "context": ex_name})
    return comments


def analyze_client(token, client, today=None, all_conversations=None):
    """Analyze a single client and return red flags."""
    if today is None:
        today = date.today()

    client_id = client["id"]
    workouts = get_recent_workouts(token, client_id, days=21)

    flags = []
    stats = {
        "name": client["name"],
        "id": client_id,
        "total_workouts_3w": 0,
        "completed": 0,
        "missed": 0,
        "upcoming": 0,
        "last_activity": None,
        "days_since_activity": None,
        "flags": flags,
        "severity": 0,  # 0=green, 1=yellow, 2=orange, 3=red
    }

    if not workouts:
        flags.append("⚠️ No workouts found in last 3 weeks")
        stats["severity"] = 2
        return stats

    past_workouts = []
    upcoming_workouts = []

    for w in workouts:
        w_date = w.get("workout_date", "")
        if not w_date:
            continue
        try:
            wd = date.fromisoformat(w_date)
        except ValueError:
            continue

        if wd <= today:
            past_workouts.append(w)
        else:
            upcoming_workouts.append(w)

    stats["total_workouts_3w"] = len(past_workouts)
    stats["upcoming"] = len(upcoming_workouts)

    # Completion analysis
    for w in past_workouts:
        if w.get("completed"):
            stats["completed"] += 1
        else:
            stats["missed"] += 1

    # Completion rate
    if past_workouts:
        completion_rate = stats["completed"] / len(past_workouts)
        if completion_rate < 0.5:
            flags.append(f"🔴 Low completion rate: {completion_rate:.0%} ({stats['completed']}/{len(past_workouts)})")
            stats["severity"] = max(stats["severity"], 3)
        elif completion_rate < 0.75:
            flags.append(f"🟡 Moderate completion: {completion_rate:.0%} ({stats['completed']}/{len(past_workouts)})")
            stats["severity"] = max(stats["severity"], 1)

    # Last activity (last completed workout or last_activity timestamp)
    activity_dates = []
    for w in past_workouts:
        if w.get("completed") and w.get("workout_date"):
            try:
                activity_dates.append(date.fromisoformat(w["workout_date"]))
            except ValueError:
                pass
        if w.get("last_activity"):
            try:
                la = datetime.fromisoformat(w["last_activity"].replace("Z", "+00:00"))
                activity_dates.append(la.date())
            except (ValueError, AttributeError):
                pass

    if activity_dates:
        last_active = max(activity_dates)
        stats["last_activity"] = last_active.isoformat()
        days_since = (today - last_active).days
        stats["days_since_activity"] = days_since

        if days_since >= 14:
            flags.append(f"🔴 MIA — no activity in {days_since} days")
            stats["severity"] = max(stats["severity"], 3)
        elif days_since >= 7:
            flags.append(f"🟠 Quiet — no activity in {days_since} days")
            stats["severity"] = max(stats["severity"], 2)

    # No upcoming workouts programmed
    if not upcoming_workouts:
        flags.append("🟡 No upcoming workouts programmed")
        stats["severity"] = max(stats["severity"], 1)

    # Consecutive missed workouts (last 5)
    recent_past = sorted(past_workouts, key=lambda w: w.get("workout_date", ""))[-5:]
    consecutive_missed = 0
    for w in reversed(recent_past):
        if not w.get("completed"):
            consecutive_missed += 1
        else:
            break
    if consecutive_missed >= 3:
        flags.append(f"🔴 {consecutive_missed} consecutive missed workouts")
        stats["severity"] = max(stats["severity"], 3)

    # Extract comments from workouts
    comments = extract_comments(workouts)
    # Only include client comments (not coach), most recent first
    client_comments = [c for c in comments if c["user"] != "Karl Schudt"]
    stats["recent_comments"] = client_comments[-5:]  # last 5

    # Get recent messages if conversations available
    if all_conversations:
        messages = get_recent_messages(token, client["name"], all_conversations)
        client_messages = [m for m in messages if m["sender"] != "Karl Schudt"]
        stats["recent_messages"] = client_messages[:3]  # last 3
    else:
        stats["recent_messages"] = []

    # Store last 7 days of workouts as TKC-markup for flagged clients
    seven_days_ago = today - timedelta(days=7)
    recent_workouts = [w for w in workouts if w.get("workout_date") and
                       date.fromisoformat(w["workout_date"]) >= seven_days_ago and
                       date.fromisoformat(w["workout_date"]) <= today]
    if recent_workouts:
        try:
            stats["tkc_markup"] = format_workouts_to_markup(
                sorted(recent_workouts, key=lambda w: w["workout_date"]),
                coach_user_id=3623  # Karl's user ID
            )
        except Exception:
            stats["tkc_markup"] = None
    else:
        stats["tkc_markup"] = None

    return stats


def generate_report(all_stats):
    """Generate a markdown triage report."""
    today = date.today()
    lines = [
        f"# Client Triage Report — {today.strftime('%A, %B %d, %Y')}",
        "",
        f"**Clients analyzed:** {len(all_stats)}",
        "",
    ]

    # Sort by severity (worst first)
    all_stats.sort(key=lambda s: (-s["severity"], s["name"]))

    # Count severities
    red = sum(1 for s in all_stats if s["severity"] >= 3)
    orange = sum(1 for s in all_stats if s["severity"] == 2)
    yellow = sum(1 for s in all_stats if s["severity"] == 1)
    green = sum(1 for s in all_stats if s["severity"] == 0)

    lines.append(f"**🔴 Red:** {red} | **🟠 Orange:** {orange} | **🟡 Yellow:** {yellow} | **🟢 Green:** {green}")
    lines.append("")

    # Red flags section
    flagged = [s for s in all_stats if s["flags"]]
    if flagged:
        lines.append("---")
        lines.append("## Needs Attention")
        lines.append("")
        for s in flagged:
            severity_icon = {0: "🟢", 1: "🟡", 2: "🟠", 3: "🔴"}[s["severity"]]
            lines.append(f"### {severity_icon} {s['name']} (#{s['id']})")
            activity_str = f"Last active: {s['last_activity']}" if s["last_activity"] else "No recent activity"
            lines.append(f"Workouts (3w): {s['completed']}/{s['total_workouts_3w']} completed | Upcoming: {s['upcoming']} | {activity_str}")
            for f in s["flags"]:
                lines.append(f"- {f}")
            # Add recent client comments if any
            if s.get("recent_comments"):
                lines.append("")
                lines.append("**Recent comments from client:**")
                for c in s["recent_comments"]:
                    lines.append(f'- [{c["date"]}] ({c["context"]}): "{c["body"]}"')
            # Add recent messages if any
            if s.get("recent_messages"):
                lines.append("")
                lines.append("**Recent messages from client:**")
                for m in s["recent_messages"]:
                    lines.append(f'- [{m["date"]}] "{m["body"]}"')
            # Add TKC-markup for red clients
            if s["severity"] >= 3 and s.get("tkc_markup"):
                lines.append("")
                lines.append("<details><summary>Last 7 days (TKC-markup)</summary>")
                lines.append("")
                lines.append("```")
                lines.append(s["tkc_markup"])
                lines.append("```")
                lines.append("</details>")
            lines.append("")

    # Green section (brief)
    clean = [s for s in all_stats if not s["flags"]]
    if clean:
        lines.append("---")
        lines.append("## All Clear")
        lines.append("")
        for s in clean:
            lines.append(f"- **{s['name']}** — {s['completed']}/{s['total_workouts_3w']} completed, last active {s.get('last_activity', '?')}")
        lines.append("")

    return "\n".join(lines)


def main():
    print("Authenticating...", file=sys.stderr)
    token, user_id = get_token()

    print("Fetching client list...", file=sys.stderr)
    clients = get_clients(token, user_id)
    print(f"Found {len(clients)} clients", file=sys.stderr)

    print("Fetching conversations...", file=sys.stderr)
    convos_resp = requests.get(
        f"{API_BASE_URL}/api/v1/conversations",
        headers={"Authorization": f"Bearer {token}"},
    )
    all_conversations = []
    if convos_resp.status_code == 200:
        cdata = convos_resp.json()
        all_conversations = cdata.get("private_conversations", []) + cdata.get("channels", [])
    print(f"Found {len(all_conversations)} conversations", file=sys.stderr)

    print("Analyzing clients...", file=sys.stderr)
    all_stats = []
    for i, client in enumerate(clients):
        # Skip test accounts
        if "test" in client["name"].lower() or "mcgee" in client["name"].lower():
            continue
        print(f"  [{i+1}/{len(clients)}] {client['name']}...", file=sys.stderr)
        try:
            stats = analyze_client(token, client, all_conversations=all_conversations)
            all_stats.append(stats)
        except Exception as e:
            print(f"  ERROR analyzing {client['name']}: {e}", file=sys.stderr)
            all_stats.append({
                "name": client["name"],
                "id": client["id"],
                "total_workouts_3w": 0,
                "completed": 0,
                "missed": 0,
                "upcoming": 0,
                "last_activity": None,
                "days_since_activity": None,
                "flags": [f"⚠️ Error: {e}"],
                "severity": 2,
            })

    report = generate_report(all_stats)
    print(report)


if __name__ == "__main__":
    main()
