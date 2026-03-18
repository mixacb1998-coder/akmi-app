import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader

# Налаштування сторінки
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

# Твій API Ключ (поки що в коді для тесту, потім перенесемо в Secrets)
API_KEY = "ТВІЙ_КЛЮЧ_ЯКИЙ_ТИ_СКИНУВ" 
genai.configure(api_key=API_KEY)

# Функція зчитування PDF
def get_pdf_content(file_path):
    try:
        reader = PdfReader(file_path)
        content = ""
        for page in reader.pages:
            content += page.extract_text()
        return content
    except:
        return None

# Основна логіка
try:
    # Завантажуємо базу кодів (має лежати в тій же папці)
    knowledge_base = get_pdf_content("database.pdf")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Протокол операції")
        protocol = st.text_area("Вставте текст протоколу тут:", height=400, placeholder="Наприклад: Проведено операцію Бенталла...")
        
    if st.button("✨ Проаналізувати та знайти оптимальний код"):
        if protocol and knowledge_base:
            with st.spinner("Gemini аналізує складність втручання..."):
                # Використовуємо ту модель, яку ти вибрав (або flash для швидкості)
                model = genai.GenerativeModel('gemini-1.5-flash') # або 'gemini-1.5-pro'
                
                prompt = f"""
                Твоя база знань з кодами АКМІ: {knowledge_base}
                
                Проаналізуй цей протокол операції: {protocol}
                
                Твоя мета:
                1. Визначити найбільш відповідний код АКМІ з бази.
                2. ПРІОРИТЕТ: Якщо втручання складне (наприклад, розшарування аорти тип А), обирай коди, що включають реконструкцію клапана або складніші маніпуляції, оскільки вони краще відображають обсяг роботи та вартість.
                3. Надай відповідь чітко:
                   - КОД: [номер]
                   - НАЗВА: [офіційна назва]
                   - ЧОМУ ОБРАНО: [коротке клінічне пояснення]
                """
                
                response = model.generate_content(prompt)
                
                with col2:
                    st.subheader("Рекомендація")
                    st.success(response.text)
        elif not protocol:
            st.warning("Спочатку вставте текст протоколу.")
        else:
            st.error("Файл database.pdf не знайдено.")

except Exception as e:
    st.error(f"Виникла помилка: {str(e)}")
