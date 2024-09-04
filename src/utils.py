import json
import os

from datetime import datetime
import requests


def load_config(config_file: str):
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
        
def save_config(config_file: str, config) -> None:
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def load_muted_users(muted_users_file: str):
    """Load the list of muted users from the JSON file."""
    if os.path.exists(muted_users_file):
        with open(muted_users_file, 'r') as muted_file:
            return json.load(muted_file)
    return []

def save_muted_users(muted_users_file: str, muted_users) -> None:
    """Save the lsit of muted users to the JSON file, restricted to admins."""
    with open(muted_users_file, 'w') as muted_file:
        json.dump(muted_users, muted_file)

def get_recent_muted_usernames(muted_users_file: str):
    # Load the list of muted users and remove expired mutes
    muted_users = load_muted_users(muted_users_file)
    current_time = datetime.utcnow().isoformat()
    muted_users = [user for user in muted_users if user['expires_at'] > current_time]
    save_muted_users(muted_users_file, muted_users)

    muted_usernames = {user['username'] for user in muted_users}
    
    return muted_usernames

def load_cat_picture(api_key: str, limit: int = 1, has_breeds: bool = True) -> requests.Response:
    url = f"https://api.thecatapi.com/v1/images/search?limit={limit}&has_breeds={int(has_breeds)}&api_key={api_key}"
    res = requests.get(url)
    return res