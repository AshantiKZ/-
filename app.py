import io
import os
import numpy as np
import streamlit as st
from PIL import Image

# Настройка страницы (адаптивность под мобильные и ПК)
st.set_page_config(
    page_title="ПИШТИРТУ WEB",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🎨 Цветовая палитра
st.markdown("""
    <style>
    .stApp { background-color: #f5f7fa; }
    h1, h2, h3, label { color: #1f2937 !important; font-weight: 600; }
    .stButton>button, .stDownloadButton>button {
        background-color: #e91e63 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stButton>button:hover, .stDownloadButton>button:hover { 
        background-color: #d81b60 !important; 
    }
    </style>
""", unsafe_allow_html=True)


# 📂 Загрузка
def load_image(file):
    return Image.open(file).convert("RGB")


# 🔥 Удаление краёв
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


# 🎯 Кроп (центр стабильный)
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

        # 🔥 Анти-чёрный фикс
        np_img = np.array(cropped)
        gray = np.mean(np_img, axis=2)

        for y in range(min(40, gray.shape[0])):
            if np.mean(gray[y]) < 35:
                cropped = cropped.crop((0, y + 2, cropped.size[0], cropped.size[1]))
                break

        return cropped


# 🔍 Zoom
def apply_zoom(img, zoom):
    if zoom <= 1:
        return img

    w, h = img.size
    new_w = int(w / zoom)
    new_h = int(h / zoom)

    left = (w - new_w) // 2
    top = (h - new_h) // 2

    cropped = img.crop((left, top, left + new_w, top + new_h))
    return cropped.resize((w, h), Image.Resampling.LANCZOS)


# 📐 Размер
def get_output_size(mode, size_mode):
    if size_mode == "Авто":
        return (1080, 810) if mode == "4:3" else (810, 1080)
    base = int(size_mode)
    return (1080, base) if mode == "4:3" else (base, 1080)


# ⚙️ Обработка одного изображения
def process_single_image(img, mode, offset, zoom, size_mode):
    ratio = 4/3 if mode == "4:3" else 3/4
    size = get_output_size(mode, size_mode)

    img = smart_crop_edges(img)
    img = crop_control(img, ratio, offset)
    img = apply_zoom(img, zoom)
    return img.resize(size, Image.Resampling.LANCZOS)


# --- ИНТЕРФЕЙС WEB ---

st.title("✂️ ПИШТИРТУ WEB")
st.write("Обрезайте скриншоты под правильный формат. Настройки применяются ко всем файлам.")

# Боковая панель
with st.sidebar:
    st.header("⚙️ Настройки")
    format_var = st.selectbox("Формат", ["4:3", "3:4"])
    size_var = st.selectbox("Размер", ["Авто", "720", "810", "900", "1080", "1440"])
    name_entry = st.text_input("Шаблон имени файлов (необязательно)", value="")
    
    offset_scale = st.slider("Смещение (центр = 200)", 0, 400, 200)
    zoom_scale = st.slider("Приближение (%)", 100, 200, 100) / 100.0

# Область загрузки
uploaded_files = st.file_uploader(
    "Выберите скриншоты", 
    type=["png", "jpg", "jpeg"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.subheader(f"🖼️ Обработанные файлы ({len(uploaded_files)})")
    
    # Выводим каждое изображение по отдельности
    for i, file in enumerate(uploaded_files, 1):
        # Читаем и обрабатываем изображение
        img = load_image(file)
        result_img = process_single_image(img, format_var, offset_scale, zoom_scale, size_var)
        
        # Формируем имя для сохранения
        ext = os.path.splitext(file.name)[1]
        img_format = "JPEG" if ext.lower() in [".jpg", ".jpeg"] else "PNG"
        
        if name_entry:
            filename = f"{name_entry}_{i}{ext}"
        else:
            filename = f"clean_{os.path.basename(file.name)}"

        # Переводим готовую картинку в байты
        img_buffer = io.BytesIO()
        result_img.save(img_buffer, format=img_format)
        img_bytes = img_buffer.getvalue()

        # Контейнер для каждого изображения (превью + кнопка)
        with st.container(border=True):
            col_img, col_btn = st.columns([3, 1])
            
            with col_img:
                st.image(result_img, caption=filename, use_container_width=True)
                
            with col_btn:
                st.write(" ")
                st.write(" ")
                # Прямая кнопка скачивания картинки
                st.download_button(
                    label=f"⬇️ Скачать {filename}",
                    data=img_bytes,
                    file_name=filename,
                    mime=f"image/{img_format.lower()}",
                    key=f"dl_{i}",
                    use_container_width=True
                )
else:
    st.info("👋 Загрузите изображения, чтобы начать работу.")
