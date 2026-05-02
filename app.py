    import os
    import numpy as np
    from tkinter import *
    from tkinter import filedialog
    from PIL import Image, ImageTk

    file_paths = []

    # 🎨 цвета
    BG = "#f5f7fa"
    CARD = "#ffffff"
    ACCENT = "#e91e63"
    TEXT = "#1f2937"
    SUBTEXT = "#6b7280"


    # 📂 загрузка
    def load_image(path):
        return Image.open(path).convert("RGB")


    # 🔥 удаление краёв
    def smart_crop_edges(img):
        np_img = np.array(img)
        gray = np.mean(np_img, axis=2)

        h, w = gray.shape

        def is_bg(v):
            return v < 30 or v > 235

        top = 0
        for y in range(h):
            if np.mean([is_bg(v) for v in gray[y]]) < 0.97:
                top = y
                break

        bottom = h
        for y in range(h - 1, -1, -1):
            if np.mean([is_bg(v) for v in gray[y]]) < 0.90:
                bottom = y
                break

        return img.crop((0, top, w, bottom))


    # 🎯 кроп (центр стабильный)
    def crop_control(img, ratio, offset):
        w, h = img.size

        if w / h > ratio:
            new_w = int(h * ratio)
            left = (w - new_w) // 2
            return img.crop((left, 0, left + new_w, h))

        else:
            new_h = int(w / ratio)

            center_top = (h - new_h) // 2
            shift = int((offset - 200) * (h - new_h) / 400)

            top = center_top + shift
            bottom = top + new_h

            if top < 0:
                top = 0
                bottom = new_h
            if bottom > h:
                bottom = h
                top = h - new_h

            cropped = img.crop((0, top, w, bottom))

            # 🔥 анти-чёрный фикс
            np_img = np.array(cropped)
            gray = np.mean(np_img, axis=2)

            for y in range(min(40, gray.shape[0])):
                if np.mean(gray[y]) < 35:
                    cropped = cropped.crop((0, y + 2, cropped.size[0], cropped.size[1]))
                    break

            return cropped


    # 🔍 zoom (ПОСЛЕ смещения)
    def apply_zoom(img, zoom):
        if zoom <= 1:
            return img

        w, h = img.size

        new_w = int(w / zoom)
        new_h = int(h / zoom)

        left = (w - new_w) // 2
        top = (h - new_h) // 2

        cropped = img.crop((left, top, left + new_w, top + new_h))

        return cropped.resize((w, h), Image.LANCZOS)


    # 📐 размер
    def get_output_size(mode, size_mode):
        if size_mode == "Авто":
            return (1080, 810) if mode == "4:3" else (810, 1080)

        base = int(size_mode)
        return (1080, base) if mode == "4:3" else (base, 1080)


    # ⚙️ обработка
    def process_image(path, folder, mode, offset, zoom, size_mode, name_template, index):
        img = load_image(path)

        ratio = 4/3 if mode == "4:3" else 3/4
        size = get_output_size(mode, size_mode)

        img = smart_crop_edges(img)
        img = crop_control(img, ratio, offset)
        img = apply_zoom(img, zoom)

        img = img.resize(size, Image.LANCZOS)

        ext = os.path.splitext(path)[1]

        if name_template:
            filename = f"{name_template}_{index}{ext}"
        else:
            filename = "clean_" + os.path.basename(path)

        img.save(os.path.join(folder, filename))


    # 📂 выбор файлов
    def select_files():
        global file_paths
        file_paths = filedialog.askopenfilenames()
        status.set(f"Файлов: {len(file_paths)}")
        preview()


    # 🖼️ preview
    def preview(event=None):
        if not file_paths:
            return

        mode = format_var.get()
        offset = offset_scale.get()
        zoom = zoom_scale.get() / 100

        img = load_image(file_paths[0])
        ratio = 4/3 if mode == "4:3" else 3/4

        img = smart_crop_edges(img)
        img = crop_control(img, ratio, offset)
        img = apply_zoom(img, zoom)

        img.thumbnail((450, 450))

        preview_img = ImageTk.PhotoImage(img)
        preview_label.config(image=preview_img)
        preview_label.image = preview_img


    # 🚀 обработка
    def process_all():
        folder = filedialog.askdirectory()
        if not folder:
            return

        mode = format_var.get()
        offset = offset_scale.get()
        zoom = zoom_scale.get() / 100
        size_mode = size_var.get()
        name_template = name_entry.get()

        for i, p in enumerate(file_paths, 1):
            process_image(p, folder, mode, offset, zoom, size_mode, name_template, i)

        status.set("Готово ✅")


    # 🎨 UI
    root = Tk()
    root.title("ПИШТИРТУ")
    root.geometry("1000x700")
    root.configure(bg=BG)

    main = Frame(root, bg=BG)
    main.pack(fill="both", expand=True, padx=20, pady=20)

    # левая панель
    left = Frame(main, bg=CARD, width=300)
    left.pack(side="left", fill="y")

    # правая (превью)
    right = Frame(main, bg=CARD)
    right.pack(side="right", fill="both", expand=True, padx=20)

    Label(left, text="ПИШТИРТУ", font=("Arial", 18, "bold"), bg=CARD, fg=TEXT).pack(pady=10)

    # формат
    format_var = StringVar(value="4:3")
    OptionMenu(left, format_var, "4:3", "3:4", command=preview).pack(pady=5)

    # размер
    Label(left, text="Размер", bg=CARD).pack()
    size_var = StringVar(value="Авто")
    OptionMenu(left, size_var, "Авто", "720", "810", "900", "1080", "1440", command=preview).pack(pady=5)

    # имя файла
    Label(left, text="Имя файла", bg=CARD).pack()
    name_entry = Entry(left)
    name_entry.pack(padx=10, fill="x")

    # смещение
    Label(left, text="Смещение (центр = 200)", bg=CARD).pack()
    offset_scale = Scale(left, from_=0, to=400, orient=HORIZONTAL, command=preview, bg=CARD)
    offset_scale.set(200)
    offset_scale.pack(fill="x", padx=10)

    # zoom
    Label(left, text="Приближение", bg=CARD).pack()
    zoom_scale = Scale(left, from_=100, to=200, orient=HORIZONTAL, command=preview, bg=CARD)
    zoom_scale.set(100)
    zoom_scale.pack(fill="x", padx=10)

    # кнопки
    Button(left, text="Выбрать файлы", bg=ACCENT, fg="white", command=select_files).pack(pady=10)
    Button(left, text="Обработать", bg="#2563eb", fg="white", command=process_all).pack()

    # превью
    preview_label = Label(right, bg=CARD)
    preview_label.pack(expand=True)

    # статус
    status = StringVar(value="Готов")
    Label(root, textvariable=status, bg=BG, fg=SUBTEXT).pack()

    root.mainloop()
