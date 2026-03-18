import streamlit as st
import google.generativeai as genai
import time

# 1. Налаштування сторінки
st.set_page_config(page_title="AKMI Surgeon Precision", page_icon="🫀", layout="wide")

st.title("🫀 Клінічний асистент кардіохірурга: АКМІ")
st.caption("Версія 2.2: Логіка максимальної комбінації кодів")

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
    protocol = st.text_area("Вставте текст протоколу:", height=600)
    
if st.button("🚀 Виконати клінічний аналіз"):
    if protocol:
        medical_files = upload_medical_bases()
        
        if "akmi" in medical_files:
            try:
                # Використовуємо актуальну модель для складних логічних зв'язків
                model = genai.GenerativeModel('gemini-3-flash-preview')
                
                complex_markers = ["пухлин", "зоб", "уламк", "стороннє тіло", "міксома", "тератома"]
                needs_dsg = any(marker in protocol.lower() for marker in complex_markers)
                
                with st.spinner("Пошук оптимальної комбінації кодів..."):
                    akmi_prompt = f"""
                    Ти — експерт з медичного кодування в кардіохірургії. Твоє завдання — описати операцію МІНІМАЛЬНОЮ кількістю кодів АКМІ, використовуючи максимально комплексні коди.

                    ПРАВИЛА ПОШУКУ (ІЄРАРХІЯ):
                    1. ЛОГІКА КОМБІНАЦІЇ: Завжди шукай один код, що покриває найбільшу кількість етапів. 
                       - Наприклад: якщо є (висхідна + дуга + клапан + коронари), спочатку шукай код, де є всі 4 елементи. Якщо немає — шукай код на 3 елементи + 1 окремий код на залишок. 
                       - НЕ став окремо "заміну аорти" і "відновлення клапана", якщо існує комбінований код.

                    2. АОРТА ТА FET:
                       - FET (Frozen Elephant Trunk): Протезування низхідної аорти (стенд-графт) ЗАВЖДИ кодуй окремо як 38568-01. Всі інші етапи (дуга, висхідна, клапан) комбінуй у максимально об'ємний код.

                    3. АОРТО-КОРОНАРНЕ ШУНТУВАННЯ (АКШ):
                       - Якщо використовується ЛВГА (мамарія) та ВПВ (вена) — це ДВА окремі коди: один для артеріального шунта, один для венозного.
                       - ОБОВ'ЯЗКОВО додай код "Забір вени для шунтування" (saphenous vein graft harvest), якщо в тексті вказано використання вени.

                    4. МІТРАЛЬНИЙ КЛАПАН:
                       - Якщо вказана "шовна пластика" (ДеВега, за Радовановичем) або "пластика по кільцю" БЕЗ імплантації штучного опорного кільця — використовуй код пластики БЕЗ протезування/кільця. Наявність цифри (30 мм) у шовній пластиці не означає використання кільця.

                    5. КАНЮЛЯЦІЯ ТА ПЕРФУЗІЯ:
                       - Кодуй окремо ПЕРИФЕРИЧНУ канюляцію (стегнова, підключична), якщо вона була. Центральну — ігноруй.
                       - Окремо кодуй "Антеградну перфузію мозку", якщо була канюляція брахіоцефальних артерій.

                    6. СТОП-ЛИСТ (ІГНОРУВАТИ ВЗАГАЛІ):
                       - Тимчасові епікардіальні електроди (2 дроти).
                       - Анестезія (інтубація, катетеризація вен анестезіологом).
                       - Гемотрансфузія, CellSaver, інфузійна терапія.

                    Використовуй тільки файл АКМІ.
                    ПРОТОКОЛ:
                    {protocol}
                    """
                    response_akmi = model.generate_content([medical_files["akmi"], akmi_prompt])
                    extracted_data = response_akmi.text

                final_output = extracted_data
                if needs_dsg and "dsg" in medical_files:
                    with st.spinner("Аналіз ДСГ для складного випадку..."):
                        dsg_prompt = f"Знайди ДСГ для цих процедур: {extracted_data}"
                        response_dsg = model.generate_content([medical_files["dsg"], dsg_prompt])
                        final_output += "\n\n---\n### АУДИТ ДСГ\n" + response_dsg.text

                with col2:
                    st.subheader("Результат")
                    st.markdown(final_output)
                        
            except Exception as e:
                st.error(f"Помилка: {e}")
    else:
        st.warning("Вставте текст протоколу.")
