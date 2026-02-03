import tkinter as tk
from PIL import ImageGrab, Image
import pytesseract
import webbrowser
import re

# Tesseract 설치 경로 설정 (윈도우 기준)
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\KwonGa_Game\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

class URLSnatcher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-alpha', 0.3) # 화면을 반투명하게
        self.root.attributes('-fullscreen', True)
        self.root.config(cursor="cross")
        
        self.canvas = tk.Canvas(self.root, cursor="cross", bg="grey")
        self.canvas.pack(fill="both", expand=True)
        
        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_move_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, 1, 1, outline='red', width=2)

    def on_move_press(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_button_release(self, event):
        end_x, end_y = event.x, event.y
        self.root.withdraw() # 캡처를 위해 잠시 숨김
        
        # 드래그한 영역 캡처
        bbox = (min(self.start_x, end_x), min(self.start_y, end_y), 
                max(self.start_x, end_x), max(self.start_y, end_y))
        img = ImageGrab.grab(bbox)
        
        # OCR 수행
        text = pytesseract.image_to_string(img).strip()
        print(f"인식된 텍스트: {text}")
        
        # URL 추출 (정규표현식)
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        urls = url_pattern.findall(text)
        
        if urls:
            full_url = urls[0] if urls[0].startswith('http') else 'http://' + urls[0]
            webbrowser.open(full_url)
        else:
            print("URL을 찾지 못했습니다.")
            
        self.root.destroy()

if __name__ == "__main__":
    print("ESC를 누르면 종료됩니다. URL 영역을 드래그하세요!")
    app = URLSnatcher()
    app.root.mainloop()