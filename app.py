import os
import base64
import streamlit as st
import google.generativeai as genai

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

# Reemplaza 'fondo_marca_agua.png' por el nombre exacto de tu archivo de imagen
img_base64 = get_base64_image("trinitaria.jpeg")

# 2. Inyección de CSS para la marca de agua y legibilidad del chat
if img_base64:
    st.markdown(
        f"""
        <style>
        /* Imagen de fondo en marca de agua fija */
        .stApp {{
            background-image: linear-gradient(rgba(255, 255, 255, 0.90), rgba(255, 255, 255, 0.40)), 
                              url("data:image/png;base64,{img_base64}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        
        /* Fondo translúcido para los contenedores del chat para asegurar excelente legibilidad */
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.60) !important;
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 3. Configuración de la API Key de Gemini
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    st.error("⚠️ No se ha configurado la `GOOGLE_API_KEY`. Por favor, añádelá en los Secrets de Streamlit o en tu entorno local.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 4. Definición del Prompt del Sistema
SYSTEM_PROMPT = """
Eres un asistente virtual experto e historiador especializado exclusivamente en la República Dominicana. 
Tu ámbito de conocimiento y respuesta se limita de forma estricta a los siguientes aspectos de la República Dominicana:
- Historia política, económica, cultural, popular, académica, sanitaria, deportiva, artística, tecnológica y urbanística.

Reglas obligatorias:
1. Si el usuario hace una pregunta que NO está relacionada con la República Dominicana o con las áreas temáticas mencionadas anteriormente, debes rechazar amablemente la consulta indicando que tu enfoque es exclusivamente la historia, cultura y desarrollo dominicano.
2. Mantén un tono académico, respetuoso, riguroso y amigable.
3. Proporciona contexto histórico y datos precisos cuando respondas.
"""

# 5. Interfaz Gráfica de Usuario (UI)
st.title("🇩🇴 Asistente Histórico y Cultural de la República Dominicana")
st.markdown("Pregúntame sobre la historia política, economía, cultura, deporte, urbanismo y más de la República Dominicana.")

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "model", 
            "content": "¡Saludos! Estoy a tu disposición para conversar sobre la historia, la cultura, la economía, el arte y los hitos de la República Dominicana. ¿Qué te gustaría explorar hoy?"
        }
    ]

# Mostrar mensajes anteriores
for message in st.session_state.messages:
    avatar = "🇩🇴" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 6. Manejo de Entrada y Llamada a Gemini
if prompt := st.chat_input("Escribe tu pregunta sobre la República Dominicana..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("model", avatar="🇩🇴"):
        with st.spinner("Consultando archivos históricos..."):
            try:
                # Usar el modelo estable actual (ej. gemini-3.8-flash)
                model = genai.GenerativeModel(
                    model_name="gemini-3.8-flash",
                    system_instruction=SYSTEM_PROMPT
                )
                
                chat_history_formatted = [
                    {"role": m["role"], "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]
                ]
                
                chat_session = model.start_chat(history=chat_history_formatted)
                response = chat_session.send_message(prompt)
                bot_response = response.text

                st.markdown(bot_response)
                st.session_state.messages.append({"role": "model", "content": bot_response})
                
            except Exception as e:
                st.error(f"❌ Ocurrió un error al procesar tu solicitud: {e}")
