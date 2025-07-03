# Discord ID <-> Trello ID 저장

import json
import os

MAPPING_FILE = "data/user_trello_map.json"

# 저장해둔 json 로딩
def load_user_mapping():
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # 저장해둔 json 파일이 존재하지 않는 경우(최초시) 초기화로 에러방지.
    return {}

# 디스코드 유저 id와 트렐로 멤버id 매핑 및 저장.
def save_user_mapping(discord_user_id, trello_member_id, trello_user_name):
    mappings = load_user_mapping()
    mappings[str(discord_user_id)] = {
        "trello_member_id": trello_member_id,
        "trello_user_name": trello_user_name
    }
    with open(MAPPING_FILE, 'w', encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)

# 내정보 확인시 아래 함수르 활용. 디스코드id를 넘겨주고 트렐로 id 반환.
def get_trello_info(discord_user_id):
    mappings = load_user_mapping()
    return mappings.get(str(discord_user_id))

