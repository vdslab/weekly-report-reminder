from dotenv import load_dotenv
import os
import json
import requests
from datetime import date


# === ESA API を使って今週の週報を投稿したユーザー一覧を取得 ===
def get_posted_users(team: str, folder: str, headers: dict):
    posted = set() # 投稿済みユーザーのスクリーンネームを格納するセット
    page = 1
    while True:
        url = f"https://api.esa.io/v1/teams/{team}/posts" # 投稿一覧を取得する esa API のエンドポイント
        params = {
            "q": f"dir:{folder}", # 検索クエリ：指定フォルダ内の投稿を取得
            "per_page": 20, # 1ページあたりの取得件数
            "page": page # 取得するページ番号
        } # クエリパラメータ
        res = requests.get(url, headers=headers, params=params) # esa API に GET リクエストを送信
        res.raise_for_status()
        data = res.json()
        posts = data.get("posts", []) # 記事の一覧を取得
        if not posts:
            break
        posted.update(p["created_by"]["screen_name"] for p in posts if p["wip"] == False) # 投稿者のスクリーンネームをセットに追加
        page += 1
    return posted


# === Discord の Webhook を使って未投稿ユーザーに通知 ===
def notify_discord(not_posted_members, user_map, webhook_url):
    mentions = [user_map[u] for u in not_posted_members if u in user_map] # スクリーンネームをメンション形式に変換
    if not mentions:
        content = "全員が週報を記入済みです 🎉"
    else:
        content = "以下のメンバーはまだ週報を記入していません\n" + "\n".join(mentions)

    res = requests.post(webhook_url, json={"content": content}) # Discord の Webhook に POST リクエストを送信
    res.raise_for_status()


def main():
    # === GitHub Secrets から OS 環境変数を読み込む ===
    TOKEN = os.environ.get("ESA_TOKEN")
    TEAM = os.environ.get("ESA_TEAM")
    DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
    USER_MAP = json.loads(os.environ.get("USER_MAP_JSON"))

    # === 今週の週報フォルダ名を自動生成して FOLDER に設定 ===
    today = date.today()
    year, week, _ = today.isocalendar()
    FOLDER = f"週報/{year}/{week}"

    headers = {"Authorization": f"Bearer {TOKEN}"} # リクエストヘッダー
    posted_members = get_posted_users(TEAM, FOLDER, headers) # 投稿済みユーザーリスト
    all_members = set(USER_MAP.keys()) # 全ユーザーリスト
    not_posted_members = all_members - posted_members # 未投稿ユーザーリスト

    # === Discord に通知 ===
    notify_discord(not_posted_members, USER_MAP, DISCORD_WEBHOOK_URL) 

if __name__ == "__main__":
    main()
