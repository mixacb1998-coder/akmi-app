import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. Налаштування сторінки
st.set_page_config(page_title="AKMI & DRG Assistant", page_icon="🫀", layout="wide")

# Стилізація інтерфейсу
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .reportview-container .main .block-container { padding-top: 2rem; }
    </style>
    """, unsafe_allow_html=True)

st.title("🫀 Асистент кодування: АКМІ + ДСГ + МКХ-10")
st.caption("Аналіз на основі НК 026:2021 та Наказу МОЗ №798 (групування)")

# 2. Безпечне підключення API Ключа
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
else:
    st.error("❌ API Ключ не знайдено в Secrets.")
    st.stop()

# 3. Функція зчитування PDF з кешуванням
@st.cache_data
def get_pdf_content(file_path):
    try:
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content += text + "\n"
        return content
    except Exception as e:
        return None

# 4. Основна логіка
try:
    # Завантажуємо обидві бази
    # ПЕРЕКОНАЙСЯ, ЩО НАЗВИ ФАЙЛІВ НА GITHUB ТАКІ САМІ
    akmi_base = get_pdf_content("nk-026_2021_.pdf")
    drg_base = get_pdf_content("36897-dn_798_12_05_2022_dod.pdf")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Протокол операції")
        protocol = st.text_area("Вставте текст протоколу тут:", height=500, placeholder="Наприклад: FET, Frozen elephant trunk...")
        
    if st.button("✨ Сформувати пакет документів для НСЗУ"):
        if protocol and akmi_base and drg_base:
            with st.spinner("Проводиться медичний аудит та групування..."):
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""
                Ти — професійний аудитор НСЗУ з кардіохірургії. 
                База АКМІ: {akmi_base}
                Наказ МОЗ №798 (Групування та МКХ-10): {drg_base}
                Протокол: {protocol}

                ЗАВДАННЯ: Сформувати оптимальний пакет кодів (АКМІ + МКХ-10).

                ЖОРСТКІ ПРАВИЛА:
                1. АНТИ-ДУБЛЮВАННЯ: Якщо два коди АКМІ (наприклад, заміна дуги та лікування розшарування) згідно з Наказом №798 належать до однієї медичної послуги/ДСГ — залиш лише ОДИН найскладніший код. 
                2. FET СПЕЦИФІКА: Якщо описано Frozen Elephant Trunk, обов'язково знайди код для ендоваскулярної частини (стенд-графт у низхідну аорту, зазвичай серія 33116-00).
                3. БЕЗ СМІТТЯ: Жодних кодів доступу (стернотомія), дренування чи закриття рани.
                4. ЗАХИСТ ТА КАНЮЛЯЦІЯ: Окремо кодуй Кардіоплегію (38588-00), Перфузію мозку (38577-00) та ШК з периферичною канюляцією (38603-00).
                5. ДІАГНОЗИ: На основі Наказу №798 підбери відповідні діагнози МКХ-10, що дозволяють згрупувати цей випадок у максимально релевантну ДСГ.

                ФОРМАТ ВІДПОВІДІ (JSON-подібний для структурування):
                Видай відповідь у трьох блоках:
                1. ТАБЛИЦЯ АКМІ: Код | Назва | Обґрунтування.
                2. ДІАГНОЗИ МКХ-10: Код | Назва.
                3. АУДИТОРСЬКА ПРИМІТКА: Пояснення щодо групування (чому певні коди були об'єднані або додані).
                """
                
                response = model.generate_content(prompt)
                
                with col2:
                    st.subheader("Результат аналізу")
                    
                    # Використовуємо вкладки для чистоти інтерфейсу
                    tab1, tab2, tab3 = st.tabs(["📋 Коди АКМІ", "🧬 Діагнози (МКХ-10)", "🔍 Аудит"])
                    
                    # Розбиваємо відповідь (ШІ зазвичай видає блоки тексту)
                    res_text = response.text
                    
                    with tab1:
                        st.markdown(res_text.split("2.")[0]) # Приблизне розбиття, Gemini зазвичай тримає структуру
                    
                    with tab2:
                        if "2." in res_text:
                            st.markdown(res_text.split("2.")[1].split("3.")[0])
                    
                    with tab3:
                        if "3." in res_text:
                            st.info(res_text.split("3.")[1])
                            
        elif not protocol:
            st.warning("Вставте текст протоколу.")
        else:
            st.error("Помилка завантаження баз знань (PDF файлів).")

except Exception as e:
    st.error(f"Виникла помилка: {str(e)}")
