# 스프린트 파일에 정보를 저장하고 불러올때 활용하는 데이터관리파일

import os
import json

SPRINT_META_FILE = "data/sprint_meta.json"

def load_sprint_meta():
    if os.path.exists(SPRINT_META_FILE):
        with open(SPRINT_META_FILE, "r") as f:
            return json.load(f)
    return {}

def save_sprint_meta(data):
    with open(SPRINT_META_FILE, "w") as f:
        json.dump(data, f, indent=2)

def add_sprint_meta(list_id, name, due_date, created_by):
    data = load_sprint_meta()
    data[list_id] = {
        "name": name,
        "due": due_date,
        "created_by": created_by
    }
    save_sprint_meta(data)

def get_all_sprints():
    return load_sprint_meta()