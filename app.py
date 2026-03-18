import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# 1. Налаштування сторінки
st.set_page_config(page_title="AKMI AI Assistant", page_icon="🫀", layout="wide")

# Стилізація інтерфейсу
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🫀 Інтелектуальний помічник кодування АКМІ")
st.caption("Аналіз кардіохірургічних протоколів на основі бази НСЗУ")

# 2. Безпечне підключення API Ключа
# Програма шукатиме ключ GEMINI_API_KEY у налаштуваннях Secrets на Streamlit Cloud
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
else:
    st.error("❌ Помилка: API Ключ не знайдено! Додайте GEMINI_API_KEY у налаштування Secrets на Streamlit.")
    st.stop()

# 3. Функція зчитування PDF з кешуванням (щоб не перевантажувати пам'ять)
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
    # Завантажуємо базу кодів із файлу database.pdf
    knowledge_base = get_pdf_content("nk-026_2021_.pdf")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Протокол операції")
        protocol = st.text_area("Вставте текст протоколу тут:", height=400, placeholder="Наприклад: Проведено операцію Бенталла...")
        
    if st.button("✨ Проаналізувати та знайти оптимальний код"):
        if protocol and knowledge_base:
            with st.spinner("Gemini аналізує складність втручання..."):
                # Використовуємо модель Flash — вона ідеальна для таких завдань
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                prompt = f"""
                Ти — експерт з медичного кодування НСЗУ, що спеціалізується виключно на кардіохірургії. 
                Твоя база знань: {knowledge_base}
                Протокол для аналізу: {protocol}

                ТВОЄ ЗАВДАННЯ: 
                Сформувати мінімально необхідний, але клінічно повний набір кодів АКМІ.

                ПРАВИЛА КОДУВАННЯ (ЖОРСТКО):
                1. ПРІОРИТЕТ КОМБІНОВАНИХ КОДІВ: Якщо операція включає протезування висхідної аорти, дуги та маніпуляції на клапані — шукай ОДИН код, який описує все це разом (наприклад, серія 38562 або 38565). Не розбивай це на три різні коди.
                2. ЗАБОРОНА НА КОДУВАННЯ ДОСТУПУ ТА ЗАВЕРШЕННЯ: Ніколи не видавай коди на стернотомію, дренування, зашивання шкіри або металеві шви на грудину. Це вважається частиною основної процедури.
                3. ЛОГІКА КАНЮЛЯЦІЇ: Якщо канюляція периферична (стегнова), використовуй код серії 38603 (ШК з периферичною канюляцією). Не дай системі розділити ШК і канюляцію судини на два коди.
                4. ЗАХИСТ: Обов'язково виділяй Кардіоплегію (38588-00) та Церебральну перфузію (38577-00), якщо вони описані, бо це окремі послуги.
                5. НІЯКИХ АНАЛОГІВ: Якщо для герметика, клею або CellSaver немає прямого коду в АКМІ — ПРОСТО ІГНОРУЙ ЇХ. Не використовуй коди з гінекології чи загальної хірургії.
                6. ВІДСУТНІСТЬ ДОМИСЛІВ: Не кодуй реімплантацію коронарних артерій, якщо в тексті не вказано прямо "reimplantation" або "Carrel button technique".

                ФОРМАТ ВІДПОВІДІ:
                Код АКМІ | Назва | Клінічне обґрунтування
                """
                
                response = model.generate_content(prompt)
                
                with col2:
                    st.subheader("Рекомендація")
                    st.success(response.text)
        elif not protocol:
            st.warning("Спочатку вставте текст протоколу.")
        else:
            st.error("Файл 'database.pdf' не знайдено у папці з програмою.")

except Exception as e:
    st.error(f"Виникла помилка: {str(e)}")
