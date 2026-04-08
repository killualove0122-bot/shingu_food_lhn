import os
import urllib.request
import json
from datetime import datetime

# -----------------------------------------------------------------------------
# 설정 / Configuration
# -----------------------------------------------------------------------------
# 환경 변수에서 가져오되, 값이 없으면 기본값(내 컴퓨터용) 사용
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8692795308:AAGskMMfHrAF0gV1fw-fdwwPOhzXzV1cWK4')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '8151874742')

import ssl
from bs4 import BeautifulSoup

def get_today_menu():
    """신구대학교 홈페이지에서 오늘자 식단 데이터를 크롤링합니다."""
    today = datetime.now()
    target_date_str = today.strftime("%d") # "08" 등 일자만 추출
    
    # SSL 인증서 검증 건너뛰기 및 레거시 연결 허용
    context = ssl._create_unverified_context()
    context.set_ciphers('DEFAULT@SECLEVEL=1') # 보안 수준 조정
    context.options |= 0x4 # SSL_OP_LEGACY_SERVER_CONNECT (레거시 서버 연결 허용)
    
    # 1. 학생식당(서관 - CONTENTS_NO=3) 크롤링
    student_url = "https://www.shingu.ac.kr/cms/FR_CON/index.do?MENU_ID=1630&CONTENTS_NO=3"
    
    # 2. 교직원식당(CONTENTS_NO=2) 크롤링
    staff_url = "https://www.shingu.ac.kr/cms/FR_CON/index.do?MENU_ID=1630&CONTENTS_NO=2"
    
    menu_data = {
        "date": today.strftime("%Y년 %m월 %d일"),
        "student_cafeteria": {"breakfast": "정보 없음", "lunch_korean": "정보 없음", "lunch_western": "정보 없음", "snack": "정보 없음"},
        "staff_cafeteria": {"lunch": "정보 없음"}
    }

    try:
        # 학생식당 크롤링
        req = urllib.request.Request(student_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            days = soup.select('ul.menu_list > li')
            
            for day in days:
                date_text = day.select_one('.date').get_text(strip=True)
                if target_date_str in date_text:
                    menu_data["date"] = date_text # 실제 페이지의 날짜 텍스트 사용
                    items = day.select('.menu_item')
                    for item in items:
                        m_type = item.select_one('.type').get_text(strip=True)
                        m_content = item.select_one('.content').get_text(strip=True)
                        
                        if "조식" in m_type: menu_data["student_cafeteria"]["breakfast"] = m_content
                        elif "중식" in m_type:
                            if "한식" in m_content or "백반" in m_content:
                                menu_data["student_cafeteria"]["lunch_korean"] = m_content
                            elif "양식" in m_content or "일품" in m_content:
                                menu_data["student_cafeteria"]["lunch_western"] = m_content
                            else:
                                menu_data["student_cafeteria"]["lunch_korean"] = m_content
                        elif "분식" in m_type: menu_data["student_cafeteria"]["snack"] = m_content

        # 교직원식당 크롤링
        req = urllib.request.Request(staff_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, context=context) as response:
            html = response.read().decode('utf-8')
            soup = BeautifulSoup(html, 'html.parser')
            days = soup.select('ul.menu_list > li')
            for day in days:
                date_text = day.select_one('.date').get_text(strip=True)
                if target_date_str in date_text:
                    items = day.select('.menu_item')
                    for item in items:
                        m_type = item.select_one('.type').get_text(strip=True)
                        m_content = item.select_one('.content').get_text(strip=True)
                        if "중식" in m_type:
                            menu_data["staff_cafeteria"]["lunch"] = m_content
                        
    except Exception as e:
        print(f"크롤링 중 오류 발생: {e}")
        
    return menu_data

def format_menu_message(menu):
    """식단 데이터를 텔레그램 메시지용 텍스트로 변환합니다."""
    message = f"🏫 *신구대학교 오늘의 식단*\n📅 {menu['date']}\n\n"
    
    message += "🍱 *학생식당(서관)*\n"
    message += f"• 조식: {menu['student_cafeteria']['breakfast']}\n"
    message += f"• 중식(한식): {menu['student_cafeteria']['lunch_korean']}\n"
    message += f"• 중식(양식): {menu['student_cafeteria']['lunch_western']}\n"
    message += f"• 분식: {menu['student_cafeteria']['snack']}\n\n"
    
    message += "☕ *교직원식당*\n"
    message += f"• 중식: {menu['staff_cafeteria']['lunch']}\n\n"
    
    message += "맛있게 드세요! 😋"
    return message

def send_to_telegram(text):
    """텔레그렘으로 메시지를 전송합니다."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    
    data_json = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=data_json, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result.get("ok", False)
    except Exception as e:
        print(f"전송 중 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("📋 식단 정보를 가져오는 중...")
    menu = get_today_menu()
    formatted_text = format_menu_message(menu)
    
    print("🚀 텔레그렘으로 전송 시도 중...")
    if send_to_telegram(formatted_text):
        print("✅ 성공: 오늘의 식단이 텔레그렘으로 전송되었습니다!")
    else:
        print("❌ 실패: 메시지 전송에 실패했습니다.")
