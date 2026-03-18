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
Ти — старший аудитор з медичного кодування АКМІ (НК 026:2021). 
Твоя задача: не просто знайти основний код, а провести повну деконструкцію протоколу на окремі оплачувані маніпуляції.

ПРОТОКОЛ: {protocol}
БАЗА КОДІВ: {knowledge_base}

ВИКОНУЙ АНАЛІЗ ЗА ТАКИМИ КАТЕГОРІЯМИ (ОБОВ'ЯЗКОВО):

1. ДОСТУП: (Стернотомія, торакотомія, повторна стернотомія тощо).
2. КАНЮЛЯЦІЯ ТА ШК: (Центральна, периферична, селективна АЦП, ретроградна кардіоплегія — перевір кожну згадану судину).
3. ОСНОВНИЙ ЕТАП: (Протезування, пластика, шунтування).
4. СУПУТНІ МАНІПУЛЯЦІЇ: (Забір вени/артерії, ресуспензія клапана, пластика вушка передсердя, лімфодисекція).
5. МЕТОДИ ЗАХИСТУ ТА ЗАБЕЗПЕЧЕННЯ: (Глибока гіпотермія, CellSaver, використання складних герметиків/клеїв).

ПРАВИЛА УНІВЕРСАЛЬНОСТІ:
- Якщо в протоколі є дія (дієслово), вона МАЄ отримати код. 
- Наприклад: "виділено вену" = код забору вени. "виконано лімфодисекцію" = код лімфодисекції за анатомічною ділянкою.
- "Метод Радовановича" vs "Кільце": Якщо в протоколі описано шовну пластику без згадки кільця — шукай код "Пластика клапана без використання протезного кільця". Не узагальнюй.
- Якщо ти бачиш маніпуляцію, якої немає в базі — знайди найближчий за складністю аналог за анатомічним принципом і зроби примітку "Потребує ручної перевірки".

ВИДАЙ РЕЗУЛЬТАТ У ВИГЛЯДІ ТАБЛИЦІ:
| Етап операції | Дія з протоколу | Код АКМІ | Офіційна назва | Складність/Важливість |
| :--- | :--- | :--- | :--- | :--- |

Наприкінці додай розділ "ПЕРЕВІРКА НА ВТРАТИ": Чи є в протоколі згадки про канюляцію стегна, гіпотермію або забір графтів, які не увійшли в основний код?
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
