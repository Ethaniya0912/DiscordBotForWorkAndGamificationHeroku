#사용자와 Trello ID 매핑관리

import json
import os

USER_FILE = "data/trello_users.json"

def load_user_data():
    if not os.path.exists(USER_FILE):
        return {}
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_user_data(data):
    with open(USER_FILE, 'w') as f:
        json.dumps(data, f, indent=2)

def get_trello_id_for_user(discord_id):
    users = load_user_data()
    return users.get(discord_id)

def set_trello_id_for_user(discord_id,trello_id):
    users = load_user_data()
    users[discord_id] = trello_id
    save_user_data(users)
