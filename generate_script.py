
import os
import requests
import openai
from dotenv import load_dotenv
from datetime import datetime
from notion_client import Client as NotionClient

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
notion = NotionClient(auth=os.getenv("NOTION_TOKEN"))
NOTION_DB_ID = os.getenv("NOTION_DATABASE_ID")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")
USERNAME = os.getenv("PYTHONANYWHERE_USERNAME")

# 캐릭터별 목소리 매핑
CHARACTER_VOICES = {
    "뚜비": "21m00Tcm4TlvDq8ikWAM",
    "피코": "EXAVITQu4vr4xnSDxMaL",
    "뽀요": "MF3mGyEYCl7XYWbV9V6O"
}

def log_error(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open("audio/error.log", "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def create_script_prompt():
    return """아이들을 위한 에피소드 제목과 캐릭터별 대사를 작성해줘.
형식은 다음과 같이:
제목: 무지개 숲에서 길을 잃은 뚜비
대본:
뚜비: 여기가 어디지...? 길을 잃은 것 같아.
피코: 걱정 마! 내가 지도를 봐줄게!
뽀요: 먼저 침착해야 해. 우리 같이 해결해보자!
"""

def generate_script():
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "너는 어린이 애니메이션 시나리오 작가야."},
            {"role": "user", "content": create_script_prompt()}
        ]
    )
    return response["choices"][0]["message"]["content"]

def parse_script(gpt_output):
    lines = gpt_output.strip().split("\n")
    title = ""
    lines_dict = {}
    for line in lines:
        if line.startswith("제목:"):
            title = line.replace("제목:", "").strip()
        elif ":" in line:
            character, dialogue = line.split(":", 1)
            character = character.strip()
            dialogue = dialogue.strip()
            if character in CHARACTER_VOICES:
                lines_dict.setdefault(character, []).append(dialogue)
    return title, lines_dict

def tts_generate(character, texts):
    voice_id = CHARACTER_VOICES[character]
    full_text = " ".join(texts)
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": full_text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.7
        }
    }

    response = requests.post(url, headers=headers, json=data)
    if response.status_code != 200:
        log_error(f"{character} - 음성 생성 실패 | {response.status_code} | {response.text}")
        print(f"[{character}] 음성 생성 실패 ❌ | 상태코드: {response.status_code}")
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"audio/{character}_{timestamp}.mp3"
    with open(filename, "wb") as f:
        f.write(response.content)

    return f"https://{USERNAME}.pythonanywhere.com/{filename}"

def create_notion_card(title, full_script, voice_links):
    timestamp = datetime.now().isoformat()
    notion.pages.create(
        parent={"database_id": NOTION_DB_ID},
        properties={
            "에피소드 제목": {"title": [{"text": {"content": title}}]},
            "대본": {"rich_text": [{"text": {"content": full_script}}]},
            "상태": {"select": {"name": "대본 생성됨"}},
            "생성 날짜": {"date": {"start": timestamp}},
            "음성 링크": {"url": voice_links[0] if voice_links else None}
        }
    )

def main():
    print("▶ GPT 대본 생성 중...")
    script = generate_script()
    title, parsed = parse_script(script)

    print("▶ 캐릭터별 음성 생성 중...")
    voice_links = []
    for character, lines in parsed.items():
        url = tts_generate(character, lines)
        if url:
            voice_links.append(url)

    print("▶ 노션 카드 생성 중...")
    create_notion_card(title, script, voice_links)
    print("✅ 완료! 자동 생성된 카드가 노션에 추가됐습니다.")

if __name__ == "__main__":
    main()
