# main.py
import sys
import os

# [1순위] 노트북 환경의 'NoneType' 출력 에러 방지 패치
class DummyWriter:
    def write(self, x): pass
    def flush(self): pass

if sys.stdout is None: sys.stdout = DummyWriter()
if sys.stderr is None: sys.stderr = DummyWriter()

# 필수 라이브러리 로드
import requests
import json
import webbrowser
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from io import BytesIO

# --- 설정 및 경로 (GitHub 및 SmartTunnel 연동) ---
CURRENT_VERSION = "1.0"
JSON_URL = "https://raw.githubusercontent.com/jyenckorea/ImageRFA/main/ImageRFA_version.json"
SPLASH_URL = "https://raw.githubusercontent.com/jyenckorea/ImageRFA/main/splash.jpg"

class ImageRFA_Launcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # 메인 창 숨김
        
        # 스플래시(초기 이미지) 창 설정
        self.splash = tk.Toplevel(self.root)
        self.splash.overrideredirect(True)
        self.splash.attributes("-topmost", True)
        
        # 로딩 상태 표시 레이아웃
        self.status_label = tk.Label(self.splash, text="보안 인증 및 업데이트 확인 중...", font=("맑은 고딕", 10), bg="white")
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        self.img_label = tk.Label(self.splash, text="ImageRFA_AI\nConnecting...", font=("Helvetica", 18))
        self.img_label.pack(expand=True, fill=tk.BOTH)
        
        self.center_window(self.splash, 500, 350) # 화면 중앙 배치
        
        self.ver_info = {} # 버전 정보를 저장할 딕셔너리
        
        # 온라인 체크 시작
        self.root.after(100, self.perform_security_check)
        self.root.mainloop()

    def center_window(self, win, w, h):
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def perform_security_check(self):
        try:
            # 1. 인터넷 연결 및 스플래시 이미지 로딩
            response_img = requests.get(SPLASH_URL, timeout=5)
            response_img.raise_for_status() # 인터넷 미연결 시 예외 발생
            
            img_data = BytesIO(response_img.content)
            pil_img = Image.open(img_data).resize((500, 300), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            self.img_label.config(image=tk_img, text="")
            self.img_label.image = tk_img
            self.splash.update()

            # 2. 깃허브 JSON 버전 정보 획득
            response_ver = requests.get(JSON_URL, timeout=5)
            response_ver.raise_for_status()
            self.ver_info = response_ver.json()
            
            # [보안] 필수 데이터 누락 시 즉시 종료 (Strict Mode)
            if "latest_version" not in self.ver_info or "min_allowed_version" not in self.ver_info:
                raise KeyError("서버 인증 데이터가 올바르지 않습니다.")

            # 3. 최소 버전 체크 (강제 종료 대상)
            cur_v = float(CURRENT_VERSION)
            min_v = float(self.ver_info["min_allowed_version"])
            
            if cur_v < min_v:
                messagebox.showerror("보안 차단", f"현재 버전({CURRENT_VERSION})은 보안 정책에 의해 사용이 금지되었습니다.\n공식 사이트에서 반드시 업데이트를 진행해 주세요.")
                webbrowser.open(self.ver_info.get("update_url", "https://www.smarttunnel.kr"))
                sys.exit()

            # 4. 검사 통과 시 메인 앱 실행 단계로 진입
            self.status_label.config(text="인증 완료. 시스템을 시작합니다.")
            self.splash.update()
            self.root.after(500, self.process_version_and_launch)

        except Exception as e:
            # 네트워크 장애 또는 데이터 손상 시 즉시 종료
            messagebox.showerror("실행 실패", f"보안 인증 서버에 연결할 수 없습니다.\n인터넷 연결을 확인해 주세요.\n\n(상세: {e})")
            sys.exit()

    def process_version_and_launch(self):
        # [핵심] 1. 초기 실행 이미지(스플래시)를 먼저 닫음
        self.splash.destroy()
        
        cur_v = float(CURRENT_VERSION)
        latest_v = float(self.ver_info["latest_version"])
        update_url = self.ver_info.get("update_url", "https://www.smarttunnel.kr")
        
        # [핵심] 2. 버전 상태에 따른 분기 처리
        if cur_v < latest_v:
            msg = self.ver_info.get("message", "새로운 버전이 출시되었습니다.")
            # 권장 업데이트 경고 문구 (실행은 가능하다는 내용 포함)
            full_msg = f"{msg}\n\n현재 버전으로도 실행은 가능하나, 안정성을 위해 업데이트를 권장합니다.\n\n지금 새 버전을 설치하시겠습니까?\n('예' 선택 시 종료 후 사이트 이동, '아니오' 선택 시 프로그램 실행)"
            
            if messagebox.askyesno("업데이트 권장", full_msg):
                # '예' 선택: 실행 멈춤 및 사이트 이동
                webbrowser.open(update_url)
                sys.exit()
            else:
                # '아니오' 선택: 프로그램 계속 실행
                self.launch_main_app()
        else:
            # 최신 버전인 경우 즉시 실행
            self.launch_main_app()

    def launch_main_app(self):
        # 무거운 AI 엔진 및 메인 UI 모듈 로드
        from ui.main_window import RockAnalyzerApp
        self.app = RockAnalyzerApp(self.root)
        self.root.deiconify() # 메인 화면 표시

if __name__ == "__main__":
    ImageRFA_Launcher()