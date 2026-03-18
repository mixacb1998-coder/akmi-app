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
@st.cache_resource
def upload_medical_bases():
    files = []
    # Назви файлів з твого репозиторію
    file_names = ["nk-026_2021_.pdf", "36897-dn_798_12_05_2022_dod.pdf"]
    
    for name in file_names:
        with st.spinner(f"Завантаження бази {name}..."):
            try:
                uploaded_file = genai.upload_file(path=name)
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
        medical_files = upload_medical_bases()
        
        if len(medical_files) == 2:
            try:
                # Використовуємо модель flash для швидкості та контексту
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # --- КРОК 1: Тільки АКМІ ---
                with st.spinner("Крок 1: Пошук кодів в АКМІ..."):
                    step1_prompt = f"""
                    Аналізуй цей ПРОТОКОЛ ОПЕРАЦІЇ. 
                    Використовуй ТІЛЬКИ перший доданий файл (АКМІ - nk-026_2021_.pdf).
                    
                    ЗАВДАННЯ:
                    1. Визнач усі коди процедур АКМІ, що відповідають протоколу.
                    2. Якщо операція гібридна або FET — виділи окремо відкриту та ендоваскулярну частини.
                    3. Поверни ТІЛЬКИ список кодів та їх назви.
                    
                    ПРОТОКОЛ:
                    {protocol}
                    """
                    # Передаємо тільки файл АКМІ (індекс 0)
                    response1 = model.generate_content([medical_files[0], step1_prompt])
                    extracted_codes = response1.text

                # --- КРОК 2: Тільки ДСГ (Наказ 798) ---
                with st.spinner("Крок 2: Групування за ДСГ..."):
                    step2_prompt = f"""
                    Ти — медичний аудитор. Маєш список кодів АКМІ, знайдених у протоколі:
                    {extracted_codes}
                    
                    Використовуй другий доданий файл (Наказ №798 - 36897-dn_798_12_05_2022_dod.pdf).
                    
                    ЗАВДАННЯ:
                    1. Знайди ці коди у таблицях Наказу №798.
                    2. Визнач відповідну ДСГ. Якщо кодів кілька — вибери ту ДСГ, яка є пріоритетною або найскладнішою.
                    3. Підбери діагноз МКХ-10.
                    
                    ФОРМАТ ВІДПОВІДІ:
                    - Таблиця: Код АКМІ | Назва | Номер ДСГ | Назва ДСГ
                    - Список МКХ-10
                    - Обґрунтування вибору ДСГ
                    """
                    # Передаємо тільки файл ДСГ (індекс 1)
                    response2 = model.generate_content([medical_files[1], step2_prompt])

                # Виведення результатів
                with col2:
                    st.subheader("Результат аналізу")
                    tab1, tab2 = st.tabs(["📋 Фінальний звіт", "🔍 Знайдені коди АКМІ"])
                    
                    with tab1:
                        st.markdown(response2.text)
                    
                    with tab2:
                        st.info("Результат першого етапу пошуку (АКМІ):")
                        st.write(extracted_codes)
                        
            except Exception as e:
                if "400" in str(e):
                    st.error("🚨 Помилка 400: Навіть при розділенні файл ДСГ занадто великий для прямого аналізу. Спробуйте скоротити текст протоколу або перевірте структуру файлів.")
                else:
                    st.error(f"Помилка: {e}")
    else:
        st.warning("Вставте текст протоколу.")
