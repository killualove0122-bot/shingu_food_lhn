import tkinter as tk
from tkinter import messagebox
import urllib.request
import json
from datetime import datetime, timedelta

# -----------------------------------------------------------------------------
# 설정 / Configuration
# -----------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN = '8692795308:AAGskMMfHrAF0gV1fw-fdwwPOhzXzV1cWK4'
TELEGRAM_CHAT_ID = '8151874742'

# 서버에서 가져온 식단 데이터 (크롤링 결과 캐싱)
MENU_DATA = {
    "today": {
        "date": "2026년 4월 1일 (수요일)",
        "student": "• 조식: 햄참치마요덮밥, 하늘보리\n• 중식(한식): 순살안동찜닭, 미역국, 쌀밥, 감자고로케(케찹), 비빔막국수, 배추김치\n• 중식(양식): 미트소스스파게티, 크림스프, 후리가케밥, 프렌치토스트, 샐러드(드레싱), 배추김치\n• 분식: 불닭크림떡볶이, 튀김, 단무지",
        "staff": "• 중식: 오징어깻잎볶음, 소고기뭇국, 메밀전병구이, 메추리알조림, 들기름비빔국수, 배추김치"
    },
    "tomorrow": {
        "date": "2026년 4월 2일 (목요일)",
        "student": "• 조식: 밥은핑계야도시락, 요구르트\n• 중식(한식): 제육볶음, 참치김치찌개, 쌀밥, 치킨너겟*머스타드, 콩나물무침, 깍두기\n• 중식(양식): 치킨스테이크, 참치김치찌개, 쌀밥, 카레우동, 브로컬리흑임자샐러드, 깍두기\n• 분식: 메뉴 없음",
        "staff": "• 중식: 간장불고기, 얼갈이된장국, 연근고로케&강정소스, 도토리묵김치무침, 상추겉절이, 깍두기"
    }
}

class ShinguMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🏫 신구대학교 식단 알리미")
        self.root.geometry("500x650")
        self.root.configure(bg="#f0f4f7")

        # 1. 헤더
        header_frame = tk.Frame(root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        tk.Label(header_frame, text="🍱 신구대 학식 알리미", font=("Malgun Gothic", 20, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=20)

        # 2. 버튼 영역
        btn_frame = tk.Frame(root, bg="#f0f4f7")
        btn_frame.pack(pady=20)

        tk.Button(btn_frame, text="📅 오늘 식단 보기", font=("Malgun Gothic", 12), width=18, height=2,
                  bg="#3498db", fg="white", activebackground="#2980b9",
                  command=lambda: self.show_and_send_menu("today")).grid(row=0, column=0, padx=10)

        tk.Button(btn_frame, text="🔜 내일 식단 보기", font=("Malgun Gothic", 12), width=18, height=2,
                  bg="#e67e22", fg="white", activebackground="#d35400",
                  command=lambda: self.show_and_send_menu("tomorrow")).grid(row=0, column=1, padx=10)

        # 3. 텍스트 박스
        self.text_area = tk.Text(root, height=18, width=55, font=("Malgun Gothic", 10), 
                                bg="white", relief=tk.FLAT, padx=10, pady=10)
        self.text_area.pack(pady=10)

        # 4. 상태 메시지
        self.status_label = tk.Label(root, text="원하시는 날짜의 버튼을 눌러주세요.", 
                                     font=("Malgun Gothic", 10), bg="#f0f4f7", fg="#7f8c8d")
        self.status_label.pack(pady=10)

    def show_and_send_menu(self, day_key):
        data = MENU_DATA[day_key]
        
        # UI 업데이트
        self.text_area.delete(1.0, tk.END)
        display_text = f"📅 날짜: {data['date']}\n\n"
        display_text += "[학생식당 (서관)]\n" + data['student'] + "\n\n"
        display_text += "[교직원식당]\n" + data['staff'] + "\n\n"
        display_text += "--------------------------------------\n"
        display_text += "텔레그램으로 전송 중입니다..."
        
        self.text_area.insert(tk.END, display_text)
        self.status_label.config(text="텔레그램 전송 중...", fg="#3498db")
        self.root.update()

        # 텔레그램 전송용 텍스트 포맷팅 (HTML 방식이 특수문자에 더 안전합니다)
        telegram_message = f"🏫 <b>신구대학교 {'오늘' if day_key=='today' else '내일'}의 식단</b>\n"
        telegram_message += f"📅 {data['date']}\n\n"
        telegram_message += "🍱 <b>학생식당(서관)</b>\n" + data['student'] + "\n\n"
        telegram_message += "☕ <b>교직원식당</b>\n" + data['staff'] + "\n\n"
        telegram_message += "맛있게 드세요! 😋"

        # 텔레그램 전송
        if self.send_to_telegram(telegram_message):
            self.status_label.config(text="✅ 텔레그램 전송 완료!", fg="#27ae60")
            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, display_text.replace("텔레그램으로 전송 중입니다...", "텔레그램으로 전송되었습니다!"))
        else:
            self.status_label.config(text="❌ 전송 실패 (API 데이터 조절 필요)", fg="#e74c3c")

    def send_to_telegram(self, text):
        import ssl
        # SSL 인증서 검증을 건너뛰도록 설정
        context = ssl._create_unverified_context()
        
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        data_json = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_json, headers={'Content-Type': 'application/json'})
        
        try:
            with urllib.request.urlopen(req, context=context) as response:
                result = json.loads(response.read().decode())
                if not result.get("ok"):
                    print(f"텔레그램 응답 오류: {result.get('description')}")
                return result.get("ok", False)
        except Exception as e:
            print(f"네트워크/API 오류 발생: {e}")
            return False

if __name__ == "__main__":
    root = tk.Tk()
    app = ShinguMenuApp(root)
    root.mainloop()
