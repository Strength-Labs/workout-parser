import requests
import json
import getpass
from datetime import datetime, timedelta

def save_token(token, filename=".tokencache"):
    expires_at = datetime.now() + timedelta(hours=1)
    with open(filename, 'w') as f:
        json.dump({"token": token, "expires_at": expires_at.isoformat()}, f)

def load_token(filename=".tokencache"):
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
            expires_at = datetime.fromisoformat(data.get("expires_at"))
            if expires_at > datetime.now():
                return data.get("token")
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None

def get_access_token(email, password, api_base_url):
    token = load_token()
    if token:
        print("Using cached access token. 👍")
        return token
    url = f"{api_base_url}/users/tokens/sign_in"
    headers = {"Content-Type": "application/json"}
    payload = {"email": email, "password": password}
    print("Attempting to get new access token...")
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        token = response.json().get("token")
        if token:
            print("Successfully obtained new access token. 🎉")
            save_token(token)
            return token
        else:
            print("Authentication failed: No token in response.")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred during authentication: {e}")
        return None

def fetch_exercises(api_base_url, token):
    url = f"{api_base_url}/api/v1/exercises"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        exercises = response.json()
        with open("exerciselist.json", 'w') as f:
            json.dump(exercises, f, indent=2)
        print("Successfully saved exercise list to exerciselist.json")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exercises: {e}")

def main():
    api_base_url = "https://app.turnkey.coach"
    email = input("Enter your email: ")
    password = getpass.getpass("Enter your password: ")
    token = get_access_token(email, password, api_base_url)
    if token:
        fetch_exercises(api_base_url, token)
    else:
        print("Could not authenticate. Exiting.")

if __name__ == "__main__":
    main()
