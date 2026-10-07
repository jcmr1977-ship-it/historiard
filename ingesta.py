import re
import requests
from bs4 import BeautifulSoup
import chromadb
from chromadb.utils import embedding_functions

# Configuración de ruta y cliente de ChromaDB
CHROMA_PATH = "chromadb_data"
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Usamos el modelo nativo por defecto (SentenceTransformers / all-MiniLM-L6-v2)
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Se obtiene o crea la colección respetando los datos previamente guardados
collection = client.get_or_create_collection(
    name="historia_rd",
    embedding_function=embedding_fn
)

def extraer_texto_url(url: str) -> str:
    """Realiza la petición HTTP y extrae el texto de los párrafos (<p>)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Extraer todo el texto contenido en párrafos <p>
        parrafos = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 50]
        
        texto_completo = "\n\n".join(parrafos)
        return texto_completo
    except Exception as e:
        print(f"❌ Error al extraer contenido de {url}: {e}")
        return ""

def fragmentar_texto(texto: str, tamano_chunk: int = 700) -> list[str]:
    """Divide un texto largo en fragmentos más pequeños para mejorar la búsqueda semántica."""
    # Limpieza básica de espacios
    texto_limpio = re.sub(r'\s+', ' ', texto).strip()
    palabras = texto_limpio.split()
    
    chunks = []
    chunk_actual = []
    longitud_actual = 0
    
    for palabra in palabras:
        chunk_actual.append(palabra)
        longitud_actual += len(palabra) + 1
        if longitud_actual >= tamano_chunk:
            chunks.append(" ".join(chunk_actual))
            chunk_actual = []
            longitud_actual = 0
            
    if chunk_actual:
        chunks.append(" ".join(chunk_actual))
        
    return chunks

def ingestar_urls(urls: list[str]):
    """Procesa una lista de URLs, extrae texto, fragmenta y guarda en ChromaDB."""
    for url in urls:
        print(f"\n🌐 Procesando URL: {url}")
        texto = extraer_texto_url(url)
        
        if not texto:
            print(f"⚠️ No se pudo obtener texto de {url}")
            continue
            
        chunks = fragmentar_texto(texto)
        print(f"📄 Se generaron {len(chunks)} fragmentos del artículo.")
        
        docs = []
        metas = []
        ids = []
        
        # Crear un ID único basado en el hash del enlace y el índice
        url_clean = re.sub(r'\W+', '_', url)[-30:]
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"web_{url_clean}_{i}"
            docs.append(chunk)
            metas.append({
                "fuente": url,
                "tipo": "web_scraping"
            })
            ids.append(chunk_id)
            
        if docs:
            # Upsert inserta o actualiza registros sin borrar los anteriores
            collection.upsert(
                documents=docs,
                metadatas=metas,
                ids=ids
            )
            print(f"✅ Se guardaron {len(docs)} fragmentos en ChromaDB.")

# ------------------------------------------------------------------
# EJECUCIÓN DEL SCRAPING
# Agregar las URLs que se deseen procesar
# ------------------------------------------------------------------
if __name__ == "__main__":
    urls_a_procesar = [
        "https://es.wikipedia.org/wiki/Ocupaci%C3%B3n_estadounidense_de_la_Rep%C3%BAblica_Dominicana_(1916-1924)",
        "https://es.wikipedia.org/wiki/Guerra_de_la_Restauraci%C3%B3n",
        "https://es.wikipedia.org/wiki/Historia_de_la_Rep%C3%BAblica_Dominicana",
    ]
    
    ingestar_urls(urls_a_procesar)
    print(f"\n🎉 Ingesta completada. Total de registros en la base de datos: {collection.count()}")
