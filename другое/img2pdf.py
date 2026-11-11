import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import os

class Img2PdfApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Фото в PDF (с поворотом)")
        self.root.geometry("850x650")

        self.images = []      # Список объектов PIL Image
        self.current_idx = 0
        self.tk_image = None  # Ссылка для сборщика мусора

        self.setup_ui()

    def setup_ui(self):
        # Панель кнопок
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, pady=5)

        tk.Button(btn_frame, text="Загрузить фото", command=self.load_images).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="< Пред", command=self.prev_image).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="След >", command=self.next_image).pack(side=tk.LEFT, padx=5)
        
        # Кнопки поворота
        tk.Button(btn_frame, text="⟲ Влево (90°)", command=lambda: self.rotate(-90)).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Вправо (90°) ⟳", command=lambda: self.rotate(90)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Сохранить в PDF", command=self.save_pdf, bg="#d4edda").pack(side=tk.RIGHT, padx=5)

        # Область предпросмотра
        self.canvas = tk.Canvas(self.root, bg="#f0f0f0")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Статус-бар
        self.status = tk.Label(self.root, text="Фото не загружены", anchor="w", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X, padx=5, pady=2)

    def load_images(self):
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp")]
        paths = filedialog.askopenfilenames(title="Выберите фото", filetypes=filetypes)
        if not paths:
            return

        self.images = []
        for p in paths:
            img = Image.open(p)
            # Автоматический поворот по EXIF (критично для фото с мобильных)
            img = ImageOps.exif_transpose(img)
            self.images.append(img)

        self.current_idx = 0
        self.show_image()
        self.update_status()

    def show_image(self):
        if not self.images:
            return

        img = self.images[self.current_idx]

        # Адаптация под размер канваса
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10: canvas_w = 800
        if canvas_h < 10: canvas_h = 500

        img_copy = img.copy()
        img_copy.thumbnail((canvas_w, canvas_h), Image.Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(img_copy)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w//2, canvas_h//2, image=self.tk_image, anchor=tk.CENTER)

    def prev_image(self):
        if self.images and self.current_idx > 0:
            self.current_idx -= 1
            self.show_image()
            self.update_status()

    def next_image(self):
        if self.images and self.current_idx < len(self.images) - 1:
            self.current_idx += 1
            self.show_image()
            self.update_status()

    def rotate(self, angle):
        if not self.images:
            return
        # Крутим оригинал в памяти, чтобы при сохранении в PDF он уже был повернут
        self.images[self.current_idx] = self.images[self.current_idx].rotate(angle, expand=True)
        self.show_image()

    def save_pdf(self):
        if not self.images:
            messagebox.showwarning("Ошибка", "Сначала загрузите фото!")
            return

        path = filedialog.asksaveasfilename(
            title="Сохранить PDF",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not path:
            return

        # PDF не поддерживает RGBA или P, конвертируем всё в RGB
        rgb_images = []
        for img in self.images:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            rgb_images.append(img)

        # Сохраняем первый кадр, остальные добавляем через append_images
        rgb_images[0].save(
            path,
            "PDF",
            resolution=150.0, # Баланс между качеством и размером файла
            save_all=True,
            append_images=rgb_images[1:]
        )
        messagebox.showinfo("Готово", f"PDF успешно собран:\n{path}")

    def update_status(self):
        self.status.config(text=f"Фото {self.current_idx + 1} из {len(self.images)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = Img2PdfApp(root)
    # Перерисовка превью при изменении размера окна
    root.bind("<Configure>", lambda e: app.show_image())
    root.mainloop()