
import os
import openai
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

prompt = (
    """
아이들을 위한 에피소드 제목과 캐릭터별 대사를 작성해줘.
형식은 다음과 같이:
제목: ...
대본:
뚜비: ...
피코: ...
뽀요: ...
"""
)

response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "너는 어린이 애니메이션 시나리오 작가야."},
        {"role": "user", "content": prompt}
    ]
)

gpt_reply = response['choices'][0]['message']['content']
lines = gpt_reply.splitlines()
title_line = next((line for line in lines if line.startswith("제목:")), "제목: 알 수 없음")
title = title_line.replace("제목:", "").strip()
script_text = "\n".join(line for line in lines if not line.startswith("제목:")).strip()

notion_url = "https://api.notion.com/v1/pages"
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

today = datetime.now().strftime("%Y-%m-%d")
data = {
    "parent": {"database_id": DATABASE_ID},
    "properties": {
        "에피소드 제목": {"title": [{"text": {"content": title}}]},
        "대본": {"rich_text": [{"text": {"content": script_text}}]},
        "상태": {"select": {"name": "대본 완료"}},
        "생성 날짜": {"date": {"start": today}}
    }
}

res = requests.post(notion_url, headers=headers, json=data)
print("노션 등록 완료!" if res.status_code == 200 else f"실패: {res.text}")
