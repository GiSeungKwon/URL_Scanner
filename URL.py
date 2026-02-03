import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import ImageGrab
import pytesseract
import webbrowser
import re
import json
import os

CONFIG_FILE = 'config.json'

class URLSnatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("URL Snatcher - Dashboard")
        self.root.geometry("420x300")
        
        self.tesseract_path = self.load_config()
        self.init_ui()
        self.create_finder() 
        
        self.root.mainloop()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get('tesseract_path', "")
        return ""

    def save_config(self, path):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'tesseract_path': path}, f)

    def init_ui(self):
        path_frame = tk.LabelFrame(self.root, text="Tesseract 설정", padx=10, pady=10)
        path_frame.pack(fill="x", padx=10, pady=5)

        self.path_label = tk.Label(path_frame, text=f"경로: {self.tesseract_path if self.tesseract_path else '미설정'}", 
                                  fg="blue", wraplength=380, justify="left")
        self.path_label.pack(anchor="w")

        self.warning_label = tk.Label(path_frame, text="", fg="red")
        self.warning_label.pack(anchor="w")
        self.check_path_validity()

        btn_browse = tk.Button(path_frame, text="경로 지정", command=self.browse_path)
        btn_browse.pack(side="left", padx=5)

        tk.Label(self.root, text="[사용법]\n1. Scan Area를 대상 위에 배치\n2. 내부에서 '마우스 왼쪽 버튼'으로 드래그!", 
                 fg="#333", font=("Arial", 10, "bold")).pack(pady=15)

    def create_finder(self):
        """마우스 이벤트를 받는 세미 투명 뷰파인더"""
        self.finder = tk.Toplevel(self.root)
        self.finder.title("Scan Area")
        self.finder.geometry("500x400") # 창을 조금 더 크게 기본 설정
        self.finder.attributes("-topmost", True)
        
        # 중요: 투명도를 0.01로 설정하여 클릭은 인식하되 배경은 보이게 함
        self.finder.attributes('-alpha', 0.3) # 0.01로 하면 너무 안보여서 테스트용으로 0.3 권장, 이후 0.01 조절
        self.finder.config(bg='white')

        self.canvas = tk.Canvas(self.finder, bg='white', highlightthickness=0, cursor="cross")
        self.canvas.pack(fill="both", expand=True)
        
        # 테두리 가이드
        self.canvas.create_rectangle(0, 0, 500, 400, outline='red', width=5, tags="border")

        self.start_x = self.start_y = None
        self.rect = None

        # 왼쪽 버튼으로 드래그 하도록 변경 (사용성 개선)
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.finder.bind("<Configure>", self.update_border)

    def update_border(self, event):
        self.canvas.delete("border")
        self.canvas.create_rectangle(0, 0, event.width, event.height, outline='red', width=5, tags="border")

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect: self.canvas.delete(self.rect)
        # 드래그 영역을 잘 보이게 빨간색 점선으로 표시
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, 
                                                 outline='blue', width=2, dash=(4, 4))

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        # 실제 스크린 좌표 계산
        x1 = self.finder.winfo_rootx() + min(self.start_x, event.x)
        y1 = self.finder.winfo_rooty() + min(self.start_y, event.y)
        x2 = self.finder.winfo_rootx() + max(self.start_x, event.x)
        y2 = self.finder.winfo_rooty() + max(self.start_y, event.y)
        
        self.canvas.delete(self.rect)
        self.perform_ocr(x1, y1, x2, y2)

    def check_path_validity(self):
        if not self.tesseract_path or not os.path.exists(self.tesseract_path):
            self.warning_label.config(text="⚠ tesseract.exe 파일이 없습니다.", fg="red")
            return False
        self.warning_label.config(text="✅ 엔진 준비 완료", fg="green")
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        return True

    def browse_path(self):
        path = filedialog.askopenfilename(title="tesseract.exe 선택", filetypes=[("Executables", "*.exe")])
        if path:
            self.tesseract_path = path
            self.save_config(path)
            self.path_label.config(text=f"경로: {path}")
            self.check_path_validity()

    def perform_ocr(self, x1, y1, x2, y2):
        if not self.check_path_validity(): return
        
        # 드래그 영역이 너무 작으면 무시
        if abs(x1 - x2) < 5 or abs(y1 - y2) < 5: return

        self.finder.attributes('-alpha', 0) # 캡처 시 완전히 투명하게
        self.root.after(150)
        
        try:
            img = ImageGrab.grab(bbox=(x1, y1, x2, y2))
            text = pytesseract.image_to_string(img, lang='eng+kor').strip() # 한글도 대비
            
            url_pattern = re.compile(r'https?://\S+|www\.\S+')
            urls = url_pattern.findall(text)
            
            if urls:
                full_url = urls[0] if urls[0].startswith('http') else 'http://' + urls[0]
                webbrowser.open(full_url)
            else:
                messagebox.showinfo("인식 결과", f"텍스트: {text}\n\nURL을 발견하지 못했습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"OCR 프로세스 오류: {e}")
        
        self.finder.attributes('-alpha', 0.3) # 다시 원래대로

if __name__ == "__main__":
    URLSnatcher()