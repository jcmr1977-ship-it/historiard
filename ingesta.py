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
        "https://ayuntamientosanpedro.gob.do/historia/",
        "https://es.wikipedia.org/wiki/Independencia_de_la_Rep%C3%BAblica_Dominicana",
        "https://es.wikipedia.org/wiki/Guerra_de_la_Restauraci%C3%B3n",
        "https://es.wikipedia.org/wiki/Juan_Pablo_Duarte",
        "https://es.wikipedia.org/wiki/Himno_nacional_de_la_Rep%C3%BAblica_Dominicana",
        "https://www.elaviador.do/texto-diario/mostrar/5772740/43-anos-record-guinness-tirso-garcia-cabra-loca-sigue-volando-historia-dominicana",
        "https://isr.mirex.gob.do/historia-rd/",
        "https://isr.mirex.gob.do/informacion-general/",
        "https://isr.mirex.gob.do/simbolos-patrios/",
        "https://www.lainformacion.com.do/opinion/articulos/la-dramatica",
        "https://elnacional.com.do/fama-y-vida/el-teatro-por-la-causa-la-filantropica_67495.html",
        "https://es.wikipedia.org/wiki/La_Trinitaria",
        "https://vanguardiadelpueblo.do/1916/11/29/estados-unidos-proclama-gobierno-de-ocupacion-en-republica-dominicana/",
        "https://vanguardiadelpueblo.do/1899/07/26/matan-balazos-al-dictador-ulises-lilis-heureaux/",
        "https://vanguardiadelpueblo.do/1861/03/18/el-presidente-pedro-santana-proclama-la-anexion-de-la-republica-dominicana-espana/",
        "https://vanguardiadelpueblo.do/1930/09/03/el-ciclon-san-zenon-deja-su-paso-muertes-y-destruccion/",
        "https://vanguardiadelpueblo.do/1857/07/07/estalla-la-revolucion-del-7-de-julio-de-1857/",
        "https://vanguardiadelpueblo.do/2026/05/12/12-mayo-1865-orden-de-retiro-de-las-tropas-espanola/",
        "https://vanguardiadelpueblo.do/1885/10/23/gregorio-luperon-recibe-maximo-gomez/",
        "https://vanguardiadelpueblo.do/1884/09/28/eugenio-maria-de-hostos-dice-desarrollar-en-los-ninos-la-razon-es-desenvolver-en-ellos-el-principio-mismo-de-la-moral-y-la-virtud/",
        "https://vanguardiadelpueblo.do/1883/06/24/nace-juan-bautista-perez-rancier/",
        "https://quod.lib.umich.edu/l/lacs/12338892.0002.001/--un-mundo-destruido-una-nacion-impuesta-la-masacre-haitiana?rgn=main;view=fulltext",
        "https://es.wikipedia.org/wiki/Masacre_del_perejil",
        "https://www.swissinfo.ch/spa/raza-y-frontera-motivaciones-de-trujillo-para-masacrar-a-miles-de-haitianos/47947576",
        "https://juanbosch.org/biografia/",
        "https://es.wikipedia.org/wiki/Constituci%C3%B3n_dominicana_de_1844",
        "https://es.wikipedia.org/wiki/Historia_de_la_Rep%C3%BAblica_Dominicana",
        "https://ayuntamientoelcercado.gob.do/la-revolucion-de-abril-de-1965",
        "https://elprofeyovanny.blogspot.com/p/la-guer.html",
        "https://unev.edu.do/republica-dominicana-conmemora-58-anos-de-la-revolucion-de-1965/",
        "https://es.wikipedia.org/wiki/Jos%C3%A9_Antonio_Salcedo",
        "https://es.wikipedia.org/wiki/Ulises_Espaillat",
        "https://lainformacion.com.do/ciudad/santiago-de-los-caballeros/ulises-francisco-espaillat-el-presidente-martir",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/palacio-virreinal-alcazar-de-colon",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/iglesia-y-hospital-de-san-lazaro",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/casa-de-las-gargolas",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/reloj-de-sol",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/casa-de-juan-viloria",
        "https://zonacolonial.org/principales-monumentos-zona-colonial/iglesia-convento-regina-angelorum",
        "https://zonacolonial.org/museos-zona-colonial/museo-de-las-casas-reales",
        "https://zonacolonial.org/museos-zona-colonial/faro-a-colon-museo-y-monumento",
        "https://zonacolonial.org/museos-zona-colonial/museo-de-las-atarazanas-reales",
        "https://zonacolonial.org/museos-zona-colonial/museo-memorial-de-la-resistencia-dominicana",
        "https://academia.org.do/institucional/fundadores/mons-dr-adolfo-alejandro-nouel/",
        "https://es.wikipedia.org/wiki/Adolfo_Alejandro_Nouel",
        "https://arquidiocesisd.org/catedral-santa-maria-de-la-encarnacion/",
        "https://www.diariolibre.com/opinion/columnistas/2024/03/26/notas-para-una-historia-del-panteon-de-la-patria/2655356",
        "https://www.diariolibre.com/opinion/editorial/2026/08/30/frank-moya-pons-es-reconocido/3643612",
        "https://www.diariolibre.com/planeta/historia/2026/08/16/la-restauracion-de-la-republica-dominicana-y-su-historia/3629458",
        "https://ayuntamientosanpedro.gob.do/historia/",
        "https://hoy.com.do/vivir/san-pedro-macoris-historia-nacio-provincias-importantes-rd_1101872.html",
        "https://acento.com.do/opinion/san-pedro-de-macoris-143-anos-de-historia-cultura-y-aportes-al-pais-9548403.html",
        "https://alcaldialaromana.gob.do/historia/",
        "https://elnacional.com.do/fama-y-vida/conoce-el-origen-de-tu-pueblo-la-romana_453006.html",
        "https://hoy.com.do/vivir/romana-historia-detras-provincia-creada-1944_1102327.html",
        "https://ayuntamientoazua.gob.do/historia/",
        "https://n.com.do/2026/08/08/descubriendo-rd-azua-un-recorrido-por-la-provincia-que-cambio-la-historia-dominicana/",
        "https://hoy.com.do/suplementos/areito/origen-gallego-nombre-azua-compostela_1084804.html",
        "https://acento.com.do/cultura/una-historia-local-pueblo-viejo-en-la-provincia-de-azua-9256516.html",
        "https://ayuntamientosantiago.gob.do/el-municipio/historia",
        "https://draarlenisguzman.com.do/historia-de-santiago-de-los-caballeros",
        "https://lainformacion.com.do/tendencias/reflejos/santiago-de-los-caballeros-memoria-fundacional-y-simbolo-de-permanencia",
        "https://hotelplatino.com/historia-santiago-de-los-caballeros-republica-dominicana/",
        "https://listindiario.com/la-republica/2022/07/26/731711/historia-y-evolucion-del-santiago-que-fundo-cristobal-colon-hace-527-anos.html",
        "https://ayuntamientodajabon.gob.do/historia/",
        "https://hoy.com.do/el-pais/grano-a-grano/dajabon-historia-rica-simbiosis-culturas_1091229.html",
        "https://www.britannica.com/place/Dajabon",
        "https://ayuntamientopuertoplata.gob.do/historia/",
        "https://revistas.uasd.edu.do/index.php/ecos/article/download/288/431?inline=1",
        "https://acento.com.do/opinion/breve-historia-puerto-plata-8405700.html",
        "https://ayuntamientobarahona.gob.do/historia/",
        "https://elnacional.com.do/fama-y-vida/conoce-el-origen-de-tu-pueblo-barahona_479877.html",
        "https://revistas.uasd.edu.do/index.php/ecos/article/view/320/474",
        "https://barahonarepublicadominicana.blogspot.com/2018/03/nuestra-historia.html",
        "https://www.argentina.gob.ar/noticias/mariposas-la-historia-de-las-hermanas-mirabal-en-el-museo-evita",
        "https://mujeresbacanas.com/las-hermanas-mirabal/",
        "https://www.gaceta.unam.mx/quienes-eran-las-hermanas-mirabal/",
        "https://www.cervantes.es/bibliotecas_documentacion_espanol/creadores/henriquez_urena_pedro.htm",
        "https://www.embajadadominicana.com.ar/novedades/pedrohenriquezurena",
        "https://uasd.edu.do/historia/",
        "https://hoy.com.do/vivir/uasd-conozca-la-historia-de-la-primada-de-america_921713.html",
        "https://www.biografiasyvidas.com/biografia/g/gomez_maximo.htm",
        "https://historia-hispanica.rah.es/biografias/20529-maximo-gomez",
        "https://vanguardiadelpueblo.do/1836/11/18/maximo-gomez-nacio-en-bani/",
        "https://www.mlb.com/es/news/featured/la-historia-del-beisbol-en-la-republica-dominicana",
        "https://colimdo.org/pagina/historia-del-beisbol-profesional-en-rd/",
        "https://www.cayolevantadoresort.com/es/blog/beisbol-dominincano/",
        "https://sabr.org/research/article/early-history-of-baseball-in-the-dominican-republic/",
        "https://cpep.gob.do/PersonajesDetalle?IdNoticia=3",
        "https://acento.com.do/especiales/las-madres-que-hicieron-la-patria-mama-tingo-9683862.html",
        "https://www.lopesan.com/blog/historia-de-punta-cana/",
        "https://avpc.gob.do/historia/",
        "https://inmenseclub.com/es/post/historia-inofmracion-punta-cana/",
        "https://www.infobae.com/inhouse/2019/11/25/el-particular-origen-de-punta-cana-asi-nacio-una-de-las-joyas-turisticas-del-caribe/",
        "https://esendom.com/deportes-2/jack-veneno",
        "https://luchalibrerd.wordpress.com/tag/dominicana-de-espectaculos/",
        "https://elnacional.com.do/fama-y-vida/conoce-el-origen-de-tu-pueblo-san-cristobal_494260.html",
        "https://ayuntamientocristobal.gob.do/historia/",
        "https://hoy.com.do/el-pais/grano-a-grano/san-cristobal-tierra-llena-historia-dominicanidad_1078215.html",
        "https://elgraficodelsur.com/san-cristobal-historia-viva-y-evolucion-constante-de-una-provincia-clave-del-sur/",
    ]
    
    ingestar_urls(urls_a_procesar)
    print(f"\n🎉 Ingesta completada. Total de registros en la base de datos: {collection.count()}")
