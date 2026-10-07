import os
import streamlit as st
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq

CHROMA_PATH = "chromadb_data"

st.set_page_config(page_title="TrinitarIA - Historia RD", page_icon="🇩🇴", layout="centered")
st.title("🇩🇴 TrinitarIA: Asistente de Historia Dominicana")
st.caption("Sistema RAG Nube (ChromaDB + SentenceTransformers + Groq API)")

# 1. Autenticación con Groq
groq_api_key = st.secrets.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")

if not groq_api_key:
    st.error("🔑 Falta la `GROQ_API_KEY`. Por favor, agrégala en los Secrets de Streamlit Cloud.")
    st.stop()

client_groq = Groq(api_key=groq_api_key)

# 2. Conexión a ChromaDB usando la misma función por defecto
@st.cache_resource
def get_chroma_collection():
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    return client.get_collection(name="historia_rd", embedding_function=embedding_fn)

try:
    collection = get_chroma_collection()
except Exception as e:
    st.error("No se encontró la base de datos `chromadb_data/`. Ejecuta `ingesta.py` primero.")
    st.stop()

# 3. Historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy TrinitarIA. ¿Qué deseas consultar sobre la historia dominicana?"}
    ]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 4. Procesamiento de la consulta
if prompt := st.chat_input("Ej: ¿Cuándo comenzó la ocupación de 1916?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Búsqueda semántica en ChromaDB
    results = collection.query(
        query_texts=[prompt],
        n_results=2
    )

    docs = results["documents"][0] if results and results.get("documents") else []
    metas = results["metadatas"][0] if results and results.get("metadatas") else []
    contexto = "\n\n".join(docs).strip()

    system_prompt = f"""
Eres TrinitarIA, un historiador experto en la República Dominicana.

REGLAS:
1. Responde a la pregunta del usuario utilizando de forma estricta la información del CONTEXTO RECUPERADO.
2. Si la respuesta se encuentra en el contexto en inglés, tradúcela al español de forma fluida.
3. Si la pregunta no está relacionada con la Historia Dominicana o no hay suficiente contexto, di amablemente que no dispones de esa información en la base de datos.

CONTEXTO RECUPERADO:
{contexto if contexto else "NO HAY CONTEXTO DISPONIBLE."}
"""

    with st.chat_message("assistant"):
        if docs:
            with st.expander("📚 Fuentes consultadas"):
                for i, (doc, meta) in enumerate(zip(docs, metas), 1):
                    st.markdown(f"**Fuente {i}:** {meta.get('fuente', 'Desconocido')}")
                    st.caption(doc)
        
        response_placeholder = st.empty()
        full_response = ""

        if not contexto:
            full_response = "No dispongo de suficiente información en la base de datos para responder a esta pregunta."
            response_placeholder.markdown(full_response)
        else:
            try:
                stream = client_groq.chat.completions.create(
                    model="llama-3.3-70b-instant",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                response_placeholder.markdown(full_response)
            except Exception as e:
                st.error(f"Error con la API de Groq: {e}")
                full_response = "Ocurrió un error al procesar la solicitud."

    st.session_state.messages.append({"role": "assistant", "content": full_response})
