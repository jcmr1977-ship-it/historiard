import os
import base64
import streamlit as st
import google.generativeai as genai
from groq import Groq

# 1. Configuración de la Página
st.set_page_config(
    page_title="Historia y Cultura Dominicana - IA",
    page_icon="🇩🇴",
    layout="centered"
)

# 2. Carga de la Marca de Agua
def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return ""

img_base64 = get_base64_image("fondo_marca_agua.png")

if img_base64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.70), rgba(255, 255, 255, 0.70)), 
                              url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        .custom-box {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            border-left: 5px solid #1e3a8a;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 3. Lectura de API Keys
GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", os.getenv("GOOGLE_API_KEY", ""))
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

# 4. Prompt del Sistema
SYSTEM_PROMPT = """
Eres un asistente virtual experto e historiador especializado exclusivamente en la República Dominicana. 
Tu ámbito de conocimiento y respuesta se limita de forma estricta a los siguientes aspectos de la República Dominicana:
- Historia política, económica, cultural, popular, académica, sanitaria, deportiva, artística, tecnológica y urbanística.

Reglas obligatorias:
1. Si la consulta NO está relacionada con la República Dominicana o con las áreas temáticas mencionadas, recházala amablemente indicando tu enfoque exclusivo.
2. Mantén un tono académico, riguroso y respetuoso.
3. Proporciona datos precisos y contexto histórico.
"""

# 5. Función con Estrategia Fallback (Gemini -> Groq)
def generar_respuesta(prompt_usuario):
    # --- Intento 1: Gemini ---
    if GOOGLE_API_KEY:
        try:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            response = model.generate_content(prompt_usuario)
            return response.text, "Gemini 2.5 Flash"
        except Exception as e_gemini:
            st.warning(f"⚠️ Gemini no disponible o cuota agotada. Conectando con servidor de respaldo (Groq)...")

    # --- Intento 2: Groq (Respaldo) ---
    if GROQ_API_KEY:
        try:
            client = Groq(api_key=GROQ_API_KEY)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_usuario}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3
            )
            return chat_completion.choices[0].message.content, "Groq (Llama 3.3 70B)"
        except Exception as e_groq:
            raise Exception(f"Fallo en Gemini y en Groq: {e_groq}")
    else:
        raise Exception("No se ha configurado la API Key de Groq para el respaldo.")

# 6. Inicialización de Estado
if "current_question" not in st.session_state:
    st.session_state.current_question = ""
if "current_response" not in st.session_state:
    st.session_state.current_response = ""
if "used_provider" not in st.session_state:
    st.session_state.used_provider = ""

# --- INTERFAZ DE USUARIO ---
st.title("🇩🇴 Asistente Histórico y Cultural de la República Dominicana")
st.markdown("Consulta un tema a la vez sobre historia, economía, cultura, deporte, urbanismo y más.")

user_input = st.text_input("Escribe tu pregunta sobre la República Dominicana:", value="", key="input_pregunta")

if st.button("Consultar", type="primary"):
    if user_input.strip():
        st.session_state.current_question = user_input
        with st.spinner("Consultando archivos históricos..."):
            try:
                respuesta, proveedor = generar_respuesta(user_input)
                st.session_state.current_response = respuesta
                st.session_state.used_provider = proveedor
            except Exception as e:
                st.session_state.current_response = f"❌ Ocurrió un error en ambos servicios: {e}"
                st.session_state.used_provider = "Error"
    else:
        st.warning("Por favor, escribe una pregunta antes de consultar.")

# Mostrar Respuesta
if st.session_state.current_response:
    st.markdown("---")
    st.subheader("📌 Pregunta realizada:")
    st.markdown(f'<div class="custom-box"><b>{st.session_state.current_question}</b></div>', unsafe_allow_html=True)
    
    st.subheader("🇩🇴 Respuesta:")
    st.markdown(f'<div class="custom-box">{st.session_state.current_response}</div>', unsafe_allow_html=True)
    st.caption(f"⚡ *Respuesta generada vía: {st.session_state.used_provider}*")
    
    col1, col2 = st.columns(2)
    with col1:
        st.code(st.session_state.current_question, language="text")
        st.caption("👆 Copiar pregunta")
    with col2:
        st.code(st.session_state.current_response, language="text")
        st.caption("👆 Copiar respuesta")

    st.markdown("---")
    if st.button("🔄 Próxima pregunta", type="secondary"):
        st.session_state.current_question = ""
        st.session_state.current_response = ""
        st.session_state.used_provider = ""
        st.rerun()
