import os
import streamlit as st
import google.generativeai as genai

# 1. Configuración de la Página de Streamlit
st.set_page_config(
    page_title="Historia y Cultura Dominicana - IA",
    page_icon="🇩🇴",
    layout="centered"
)

# 2. Configuración de la API Key de Gemini
# Intenta leer desde st.secrets (para Streamlit Cloud) o de variables de entorno locales
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
except Exception:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    st.error("⚠️ No se ha configurado la `GOOGLE_API_KEY`. Por favor, añádela en los Secrets de Streamlit o en tu entorno local.")
    st.stop()

genai.configure(api_key=GOOGLE_API_KEY)

# 3. Definición del Prompt del Sistema (Restricción temática estricta)
SYSTEM_PROMPT = """
Eres un asistente virtual experto e historiador especializado exclusivamente en la República Dominicana. 
Tu ámbito de conocimiento y respuesta se limita de forma estricta a los siguientes aspectos de la República Dominicana:
- Historia política, económica, cultural, popular, académica, sanitaria, deportiva, artística, tecnológica y urbanística.

Reglas obligatorias:
1. Si el usuario hace una pregunta que NO está relacionada con la República Dominicana o con las áreas temáticas mencionadas anteriormente, debes rechazar amablemente la consulta indicando que tu enfoque es exclusivamente la historia, cultura y desarrollo dominicano.
2. Mantén un tono académico, respetuoso, riguroso y amigable.
3. Proporciona contexto histórico y datos precisos cuando respondas.
"""

# 4. Inicialización del Modelo Gemini (Usando gemini-3.8-flash por velocidad y eficiencia)
@st.cache_resource
def load_gemini_model():
    # Configuramos el modelo con instrucciones de sistema incorporadas en el prompt inicial o rol
    model = genai.GenerativeModel(
        model_name="gemini-3.8-flash",
        system_instruction=SYSTEM_PROMPT
    )
    return model

model = load_gemini_model()

# 5. Interfaz Gráfica de Usuario (UI)
st.title("🇩🇴 Asistente Histórico y Cultural de la República Dominicana")
st.markdown("Pregúntame sobre la historia política, economía, cultura, deporte, urbanismo y más de la República Dominicana.")

# Inicializar historial de chat en el session_state de Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "model", 
            "content": "¡Saludos! Estoy a tu disposición para conversar sobre la historia, la cultura, la economía, el arte y los hitos de la República Dominicana. ¿Qué te gustaría explorar hoy?"
        }
    ]

# Mostrar mensajes anteriores en pantalla
for message in st.session_state.messages:
    avatar = "🇩🇴" if message["role"] == "model" else "👤"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 6. Manejo de la Entrada del Usuario y Comunicación con la API
if prompt := st.chat_input("Escribe tu pregunta sobre la República Dominicana..."):
    # Agregar y mostrar mensaje del usuario
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    # Generar respuesta del asistente utilizando el historial de chat para mantener contexto
    with st.chat_message("model", avatar="🇩🇴"):
        with st.spinner("Consultando archivos históricos..."):
            try:
                # Formatear el historial para el SDK de Gemini
                chat_history_formatted = [
                    {"role": m["role"], "parts": [m["content"]]} 
                    for m in st.session_state.messages[:-1]
                ]
                
                chat_session = model.start_chat(history=chat_history_formatted)
                response = chat_session.send_message(prompt)
                bot_response = response.text

                st.markdown(bot_response)
                
                # Guardar la respuesta en el historial
                st.session_state.messages.append({"role": "model", "content": bot_response})
                
            except Exception as e:
                error_msg = f"Ocurrió un error al procesar tu solicitud con la API de Gemini: {e}"
                st.error(error_msg)
