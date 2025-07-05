# 보드, 리스트, 카드의 ID를 자동 조회하는 파이썬 스크립트

# 보드이름 -> 보드ID
# 보드ID + 리스트 이름 -> 리스트 ID
# 리스트 ID + 카드 이름 -> 카드 ID

import os
import requests
from dotenv import load_dotenv

#.env 파일에서 API키 불러오기
load_dotenv()
KEY = os.getenv("TRELLO_KEY")
TOKEN = os.getenv(("TRELLO_TOKEN"))
board_id = os.getenv("TRELLO_BOARD_ID")

# TRELLO API 기본 URL
BASE_URL = "https://api.trello.com/1"

class TrelloLookup:

    # 보드 이름 -> ID 찾기
    @staticmethod
    def get_board_id_by_name(board_name):
        url = f"{BASE_URL}/members/me/boards"
        params = {"key" : KEY, "token" : TOKEN}
        res = requests.get(url, params=params)
        for board in res.json():
            if board["name"] == board_name:
                return board["id"]
        return None

    # 리스트 이름 -> ID 찾기 (보드 ID 필요)
    @staticmethod
    def get_list_id_by_name(board_id, list_name):
        url = f"{BASE_URL}/boards/{board_id}/lists"
        params = {"key": KEY, "token" : TOKEN}
        res = requests.get(url, params=params)
        for lst in res.json():
            if lst["name"] == list_name:
                return lst["id"]
        return None

    @staticmethod
    def get_lists(board_id):
        url = f"{BASE_URL}/boards/{board_id}/lists"
        params = {"key": KEY, "token": TOKEN}
        res = requests.get(url, params=params)

        if res.status_code != 200:
            print(f"X 리스트 조회 실패 - 상태코드{res.status_code}")
            return []
        return res.json()

    # 만료일이 존재하는 리스트 조회.
    @staticmethod
    def get_lists_with_due(board_id):
        url = f"{BASE_URL}/boards/{board_id}/lists"
        params = {"key": KEY, "token": TOKEN}
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return []
        return [lst for lst in res.json() if "desc" in lst and "만료일" in lst["desc"]]

    # 리스트 이름이 특정 접미사로 끝나는 리스트 ID 반환
    @staticmethod
    def get_list_id_endswith(board_id, name_suffix):
        url = f"{BASE_URL}/boards/{board_id}/lists"
        params = {"key": KEY, "token": TOKEN}
        res = requests.get(url, params=params)

        if res.status_code != 200:
            return None

        for lst in res.json():
            if lst["name"].strip().lower().endswith(name_suffix.lower()):
                return lst["id"]
        return None

    # 해당 리스트가 보드에 있는지 확인
    @staticmethod
    def is_list_on_board(list_id, board_id):
        url = f"{BASE_URL}/lists/{list_id}"
        params = {
            "key": KEY,
            "token": TOKEN
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return False
        return res.json().get("idBoard") == board_id

   # 카드 이름 -> ID 찾기 (리스트 ID 필요)
    @staticmethod
    def get_card_id_by_name(list_id, card_name) :
        url = f"{BASE_URL}/lists/{list_id}/cards"
        params = {"key": KEY, "token" : TOKEN}
        res = requests.get(url, params=params)
        for card in res.json():
            if card["name"] == card_name:
                return card["id"]
        return None

    # 카드 인포 가져오기.
    @staticmethod
    def get_card_info_by_id(card_id):
        url = f"{BASE_URL}/cards/{card_id}"
        params = {"key": KEY, "token": TOKEN}
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return res.json()
        return None

    # 카드 갯수 세기.
    @staticmethod
    def get_card_count(list_id):
        url = f"{BASE_URL}/lists/{list_id}/cards"
        params = {
            "key": KEY,
            "token": TOKEN
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return 0
        return len(res.json())

    # 전체 카드 정보 반환
    @staticmethod
    def get_card(list_id):
        url = f"{BASE_URL}/lists/{list_id}/cards"
        params = {
            "key": KEY,
            "token": TOKEN
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return 0
        return res.json()

    # ------------ TRELLO API 함수-------------
    @staticmethod
    def create_card(name, list_id):
        url = f"{BASE_URL}/lists/{list_id}/cards"
        params = {"key": KEY, "token": TOKEN, "idList" : list_id, "name":name}
        res = requests.post(url, params=params)
        return res.json()

    @staticmethod
    def create_list(board_id, name):
        url = f"{BASE_URL}/lists"
        params = {
            "key": KEY,
            "token": TOKEN,
            "idBoard" : board_id,
            "name":name,
            "pos": "bottom" # 리스트를 가장 오른쪽에 생성
        }
        res = requests.post(url, params=params)
        return res.json()

    @staticmethod
    def create_list_with_due(board_id, name, due_date_str):
        url = f"{BASE_URL}/lists"
        desc = f"만료일: {due_date_str}"  # 리스트 설명에 만료일 저장
        params = {
            "key": KEY,
            "token": TOKEN,
            "idBoard" : board_id,
            "name": name,
            "desc": desc,
            "pos": "bottom"  # 리스트를 가장 오른쪽에 생성
        }
        res = requests.post(url, params=params)
        return res.json()

    @staticmethod
    def archive_list(list_id):
        url = f"{BASE_URL}/lists/{list_id}/closed"
        params = {"key": KEY, "token": TOKEN, "value": "true"}
        res = requests.put(url, params=params)
        return res.json()

    #-------------------보드, 카드 전체조회함수--------------
    @staticmethod
    def get_all_cards():
        url = f"{BASE_URL}/members/me/cards"
        params = {"key": KEY, "token": TOKEN}
        res = requests.get(url, params=params)
        return res.json()

    @staticmethod
    def get_all_boards():
        url = f"{BASE_URL}/members/me/boards"
        params = {
            "key": KEY,
            "token": TOKEN,
            "fields": "name,id",  # 필요한 필드만 요청
            "filter": "open"  # 닫힌 보드는 제외
        }
        res = requests.get(url, params=params)
        if res.status_code != 200:
            return []
        return res.json()

    #------------------카드 담당자 설정, 해제, 조회, 완료------------

    @staticmethod
    def assign_member_to_card(card_id, member_id):
        url = f"{BASE_URL}/cards/{card_id}/idMembers"
        params = {"key": KEY, "token": TOKEN, "value": member_id}
        return requests.post(url, params=params)

    @staticmethod
    def remove_member_from_card(card_id, member_id):
        url = f"{BASE_URL}/cards/{card_id}/idMembers/{member_id}"
        params = {"key": KEY, "token": TOKEN}
        return requests.delete(url, params=params)

    @staticmethod
    def get_cards_by_member(BOARD_ID, member_id):
        url = f"{BASE_URL}/boards/{board_id}/cards"
        params = {"key": KEY, "token": TOKEN}
        response = requests.get(url, params=params)
        cards = response.json()
        return [card for card in cards if member_id in card["idMembers"]]

    # 카드 이름으로 찾기(id 대신)
    @staticmethod
    def get_card_id_by_name(board_id, card_name):
        url = f"{BASE_URL}/boards/{board_id}/cards"
        params = {
            "key": KEY,
            "token": TOKEN
        }
        response = requests.get(url,params=params)
        if response.status_code != 200:
            print("Trello API 오류:", response.text)
            return None

        cards = response.json()
        #카드 이름이 정확히 일치하는 첫 번째 카드 반환
        for card in cards:
            if card["name"] == card_name:
                return card["id"]
        # 카드 이름이 일치하지않으면 None 반환
        return None

    @staticmethod
    def mark_card_complete(card_id):
        url = f"{BASE_URL}/cards/{card_id}"
        params = {"key": KEY, "token": TOKEN}
        current = requests.get(url, params=params).json()
        new_name = f"✅{current['name']}" if not current['name'].startswith("✅") else current['name']
        return requests.put(url, params={**params, "name": new_name})

    @staticmethod
    def move_card_to_list(card_id, list_id):
        url = f"{BASE_URL}/cards/{card_id}"
        params = {"key": KEY, "token": TOKEN, "idList": list_id}
        return requests.put(url, params=params)