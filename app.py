import os
import base64
import streamlit as st
from groq import Groq

# 1. Configuración de la Página de Streamlit
st.set_page_config(
    page_title="Historia y Cultura Dominicana - IA",
    page_icon="🇩🇴",
    layout="centered"
)

# Función para convertir la imagen local a Base64 y usarla en CSS
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

# Reemplaza 'fondo_marca_agua.png' por el nombre exacto de tu archivo de imagen en el repositorio
img_base64 = get_base64_image("trinitaria.jpeg")

# 2. Inyección de CSS para la marca de agua y legibilidad
if img_base64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.40)), 
                              url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .custom-box {{
            background-color: rgba(255, 255, 255, 0.60);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #1e3a8a;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 3. Configuración de la API Key de Groq
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

if not GROQ_API_KEY:
    st.error("⚠️ No se ha configurado la `GROQ_API_KEY`. Por favor, añádela en los Secrets de Streamlit.")
    st.stop()

# 4. Prompt del Sistema (Restricción estricta al dominio dominicano)
SYSTEM_PROMPT = """
Eres un asistente virtual experto e historiador especializado exclusivamente en la República Dominicana. 
Tu ámbito de conocimiento y respuesta se limita de forma estricta a los siguientes aspectos de la República Dominicana:
- Historia política, económica, cultural, popular, académica, sanitaria, deportiva, artística, tecnológica y urbanística.

Reglas obligatorias:
1. Si la consulta NO está relacionada con la República Dominicana o con las áreas temáticas mencionadas, recházala amablemente en español indicando que solo atiende preguntas relativas al tema.
2. Mantén un tono académico, riguroso y respetuoso.
3. Proporciona datos precisos y contexto histórico.
"""

# 5. Inicialización de Estados en Session State
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "current_response" not in st.session_state:
    st.session_state.current_response = ""

# --- ORDEN VISUAL DE LA INTERFAZ ---

# A. TÍTULO PRINCIPAL
st.title("🇩🇴 Asistente Histórico y Cultural de la República Dominicana")

# B. SUBTÍTULO
st.markdown("Consulta un tema a la vez sobre historia, economía, cultura, deporte, urbanismo y más. Impulsado por Groq.")

# C. CAJA DE TEXTO DE LA PREGUNTA
user_input = st.text_input("Escribe tu pregunta sobre la República Dominicana:", value="", key="input_pregunta")

if st.button("Consultar", type="primary"):
    if user_input.strip():
        st.session_state.current_question = user_input
        with st.spinner("Consultando con Groq..."):
            try:
                client = Groq(api_key=GROQ_API_KEY)
                chat_completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ],
                    model="openai/gpt-oss-20b",
                    temperature=0.3,
                    max_tokens=2048
                )
                st.session_state.current_response = chat_completion.choices[0].message.content
            except Exception as e:
                st.session_state.current_response = f"❌ Ocurrió un error al procesar tu solicitud con Groq: {e}"
    else:
        st.warning("Por favor, escribe una pregunta antes de consultar.")

# D. RESPUESTA ABAJO (Si ya fue consultada)
if st.session_state.current_response:
    st.markdown("---")
    st.subheader("📌 Pregunta realizada:")
    st.markdown(f'<div class="custom-box"><b>{st.session_state.current_question}</b></div>', unsafe_allow_html=True)
    
    st.subheader("🇩🇴 Respuesta:")
    st.markdown(f'<div class="custom-box">{st.session_state.current_response}</div>', unsafe_allow_html=True)
    st.caption("⚡ Estos es una IA y puede cometer errores. *Generado mediante Groq (openai/gpt-oss-20b)*")
   
    st.markdown("---")
    
    # E. BOTÓN DE PRÓXIMA PREGUNTA (Abajo de todo)
    if st.button("🔄 Próxima pregunta", type="secondary"):
        st.session_state.current_question = ""
        st.session_state.current_response = ""
    #    st.session_state.input_pregunta = ""
        st.rerun()
