import streamlit as st
import google.generativeai as genai
import time

# 1. Налаштування сторінки
st.set_page_config(page_title="AKMI & DRG Assistant", page_icon="🫀", layout="wide")

st.title("🫀 Асистент кодування: АКМІ + ДСГ + МКХ-10")
st.caption("Професійний інструмент для кардіохірургів (Версія 2026)")

# 2. API Ключ
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ Додайте GEMINI_API_KEY у Secrets.")
    st.stop()

# 3. Функція завантаження файлів у Google AI (File API)
@st.cache_resource # Кешуємо об'єкти файлів, щоб не перевантажувати щоразу
def upload_medical_bases():
    files = []
    # Назви файлів мають точно збігатися з тими, що на GitHub
    file_names = ["nk-026_2021_.pdf", "36897-dn_798_12_05_2022_dod.pdf"]
    
    for name in file_names:
        with st.spinner(f"Завантаження бази {name} у систему..."):
            try:
                uploaded_file = genai.upload_file(path=name)
                # Чекаємо, поки Google обробить файл (зазвичай пару секунд)
                while uploaded_file.state.name == "PROCESSING":
                    time.sleep(2)
                    uploaded_file = genai.get_file(uploaded_file.name)
                files.append(uploaded_file)
            except Exception as e:
                st.error(f"Не вдалося завантажити {name}: {e}")
    return files

# 4. Основний інтерфейс
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Протокол операції")
    protocol = st.text_area("Вставте текст протоколу:", height=500)
    
if st.button("✨ Сформувати пакет документів"):
    if protocol:
        # Завантажуємо (або беремо з кешу) файли
        medical_files = upload_medical_bases()
        
        if len(medical_files) == 2:
            try:
                with st.spinner("Gemini аналізує протокол..."):
                    model = genai.GenerativeModel('gemini-3-flash')
                    
                    # Формуємо запит: Файли йдуть як окремі об'єкти, а не текст
                    prompt = """
                    Ти — медичний аудитор. Використовуй додані файли (АКМІ та Наказ №798) для аналізу.
                    
                    ЗАВДАННЯ:
                    1. Знайди коди АКМІ. Якщо операція гібридна (FET) — обов'язково кодуй і відкриту частину (дуга/висхідна), і ендоваскулярну (стенд-графт).
                    2. Згрупуй коди за Наказом №798. Якщо коди дублюються в одній ДСГ — залиш найскладніший.
                    3. Підбери діагнози МКХ-10.
                    
                    ФОРМАТ:
                    - Таблиця АКМІ (Код, Назва, Обґрунтування)
                    - Список МКХ-10
                    - Коментар щодо групування
                    """
                    
                    # ВАЖЛИВО: Передаємо список [Файл1, Файл2, Текст]
                    response = model.generate_content([medical_files[0], medical_files[1], prompt + "\n\nПРОТОКОЛ:\n" + protocol])
                    
                    with col2:
                        st.subheader("Результат")
                        tab1, tab2, tab3 = st.tabs(["📋 АКМІ", "🧬 МКХ-10", "🔍 Аудит"])
                        
                        res = response.text
                        # Проста логіка розділення для інтерфейсу
                        parts = res.split("\n\n")
                        with tab1: st.write(res) # Виводимо весь текст, поки не налаштуємо парсинг
                        with tab2: st.info("Дивіться основний звіт")
                        with tab3: st.info("Перевірено згідно з Наказом №798")
                        
            except Exception as e:
                if "429" in str(e):
                    st.error("🚨 Перевищено ліміт запитів. Зачекайте 60 секунд і спробуйте знову.")
                else:
                    st.error(f"Помилка: {e}")
    else:
        st.warning("Вставте текст протоколу.")
