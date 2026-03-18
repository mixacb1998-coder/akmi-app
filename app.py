import streamlit as st
import google.generativeai as genai
import time

# 1. Налаштування сторінки
st.set_page_config(page_title="AKMI Precision Tool", page_icon="🫀", layout="wide")

st.title("🫀 Кардіохірургічний асистент: АКМІ та Спец-Аудит")
st.caption("Версія 2.0: Оптимізація токенів та фокус на складних втручаннях")

# 2. API Ключ
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
else:
    st.error("❌ Додайте GEMINI_API_KEY у Secrets.")
    st.stop()

# 3. Функція завантаження файлів
@st.cache_resource
def upload_medical_bases():
    files = {}
    file_configs = {
        "akmi": "nk-026_2021_.pdf",
        "dsg": "36897-dn_798_12_05_2022_dod.pdf"
    }
    
    for key, name in file_configs.items():
        try:
            uploaded_file = genai.upload_file(path=name)
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(1)
                uploaded_file = genai.get_file(uploaded_file.name)
            files[key] = uploaded_file
        except Exception as e:
            st.error(f"Помилка завантаження {name}: {e}")
    return files

# 4. Основний інтерфейс
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Протокол операції")
    protocol = st.text_area("Текст протоколу:", height=500)
    
if st.button("🚀 Аналізувати"):
    if protocol:
        medical_files = upload_medical_bases()
        
        if "akmi" in medical_files:
            try:
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                # ЛОГІКА: Перевірка на потребу в ДСГ
                complex_markers = ["пухлин", "зоб", "уламк", "стороннє тіло", "міксома", "тератома"]
                needs_dsg = any(marker in protocol.lower() for marker in complex_markers)
                
                # КРОК 1: Клінічний аналіз АКМІ (Максимальний фокус)
                with st.spinner("Аналіз АКМІ та технічних нюансів..."):
                    akmi_prompt = f"""
                    Ти — вузькоспеціалізований кардіохірургічний аудитор. 
                    ВИМОГИ ДО ТОЧНОСТІ:
                    1. Гібридна дуга (FET): Це НЕ 33116-00. Це протезування низхідної аорти — 38568-01 + коди на дугу/висхідну.
                    2. Канюляція: Чітко диференціюй центральну та периферичну (a.femoralis, a.subclavia). Якщо вказано доступ через судину — це периферична.
                    3. Перфузія: "Глибока гіпотермія" — це температурний режим. Якщо вказана канюляція брахіоцефальних стовбурів — це "Антеградна перфузія мозку". Кодуй її окремо.
                    4. Використовуй ТІЛЬКИ файл АКМІ.
                    
                    ПРОТОКОЛ:
                    {protocol}
                    """
                    response_akmi = model.generate_content([medical_files["akmi"], akmi_prompt])
                    extracted_data = response_akmi.text

                # КРОК 2: Селективний ДСГ (тільки якщо потрібно)
                final_output = extracted_data
                if needs_dsg and "dsg" in medical_files:
                    with st.spinner("Специфічний випадок: Пошук у ДСГ..."):
                        dsg_prompt = f"""
                        Виявлено специфічне втручання (пухлина/зоб/уламок). 
                        Знайди відповідну групу ДСГ у файлі Наказу №798 для цих кодів:
                        {extracted_data}
                        """
                        response_dsg = model.generate_content([medical_files["dsg"], dsg_prompt])
                        final_output += "\n\n### АУДИТ ДСГ (Специфічний випадок)\n" + response_dsg.text
                else:
                    final_output += "\n\n*Аналіз ДСГ пропущено: стандартне кардіохірургічне втручання.*"

                with col2:
                    st.subheader("Результат")
                    st.markdown(final_output)
                        
            except Exception as e:
                st.error(f"Помилка: {e}")
