import json
import requests
from django.shortcuts import render, Http404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import logging
from django.utils import timezone # Importar timezone para la función de reporte

logger = logging.getLogger(__name__)

# --- Funciones para cargar datos desde JSON ---

def load_json_from_url(url):
    # Ya no se necesita la comprobación de placeholder específica si siempre se usa la URL de settings
    if not url:
        logger.error(f"URL de JSON no configurada.")
        return None
    try:
        logger.info(f"Intentando cargar JSON desde URL: {url}")
        response = requests.get(url, timeout=15) # Aumentado un poco el timeout por si acaso
        response.raise_for_status() # Lanza una excepción para códigos de error HTTP (4xx o 5xx)
        data = response.json()
        logger.info(f"JSON cargado exitosamente desde {url}. Items: {len(data) if isinstance(data, list) else 'No es una lista'}")
        return data
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al cargar JSON desde {url}")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error HTTP al cargar JSON desde {url}: {e.response.status_code} - {e.response.text}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red cargando JSON desde {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON desde {url}: {e}. Respuesta recibida: {response.text[:500]}...") # Muestra parte de la respuesta
        return None

def load_json_from_file(file_path):
    try:
        # Asume que 'data' está en el mismo nivel que la carpeta de la app 'catalogo' o el proyecto
        abs_file_path = os.path.join(settings.BASE_DIR, 'data', file_path)
        logger.info(f"Intentando cargar JSON desde archivo local: {abs_file_path}")
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"JSON cargado exitosamente desde {abs_file_path}. Items: {len(data) if isinstance(data, list) else 'No es una lista'}")
            return data
    except FileNotFoundError:
        logger.error(f"Archivo JSON local no encontrado: {abs_file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON local desde: {abs_file_path} - {e}")
        return None
    except Exception as e:
        logger.error(f"Error inesperado cargando JSON local desde {abs_file_path}: {e}")
        return None

# --- Funciones para la API de TMDb ---

def search_tmdb_by_name_year(query, year, item_type_for_tmdb):
    """
    Busca en TMDb por nombre y año.
    item_type_for_tmdb debe ser 'movie' o 'tv'.
    Retorna el tmdb_id si se encuentra, de lo contrario None.
    """
    api_key = settings.TMDB_API_KEY
    base_url = settings.TMDB_BASE_URL

    if not api_key:
        logger.warning("TMDB_API_KEY no está configurada en settings.")
        return None

    if item_type_for_tmdb not in ['movie', 'tv']:
        logger.error(f"Tipo de item inválido para búsqueda TMDb: {item_type_for_tmdb}")
        return None

    endpoint = f'search/{item_type_for_tmdb}'
    params = {'api_key': api_key, 'query': query, 'language': 'es-ES'} # Cambiado a es-ES

    if item_type_for_tmdb == 'movie' and year:
        params['year'] = year
    elif item_type_for_tmdb == 'tv' and year:
        params['first_air_date_year'] = year

    url = f"{base_url}/{endpoint}"
    logger.debug(f"Buscando en TMDb: {url} con params: {params}")

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        search_results = response.json()

        if search_results and search_results.get('results'):
            # Podríamos añadir lógica para seleccionar el mejor resultado si hay varios
            # Por ahora, tomamos el primero
            first_result = search_results['results'][0]
            logger.info(f"TMDb encontró ID: {first_result.get('id')} para '{query}' ({year})")
            return first_result.get('id')
        logger.debug(f"No se encontraron resultados de TMDb para '{query}' ({year}) como {item_type_for_tmdb}.")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al buscar en TMDb por nombre/año: '{query}' ({year})")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red o API de TMDb al buscar por nombre/año: {e} para '{query}' ({year})")
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON de búsqueda TMDb para '{query}' ({year}): {e}")
    except IndexError:
        logger.debug(f"Resultados de TMDb vacíos para '{query}' ({year}) como {item_type_for_tmdb}.")
    return None


def get_tmdb_details_by_id(tmdb_id, item_type_for_tmdb):
    """
    Obtiene detalles de TMDb (incluyendo póster) por ID.
    item_type_for_tmdb debe ser 'movie' o 'tv'.
    """
    api_key = settings.TMDB_API_KEY
    base_url = settings.TMDB_BASE_URL
    image_base_url = settings.TMDB_IMAGE_BASE_URL
    poster_size = settings.TMDB_POSTER_SIZE

    if not api_key:
        logger.warning("TMDB_API_KEY no está configurada en settings.")
        return {}
    
    if item_type_for_tmdb not in ['movie', 'tv']:
        logger.error(f"Tipo de item inválido para obtener detalles TMDb: {item_type_for_tmdb}")
        return {}

    endpoint = f'{item_type_for_tmdb}/{tmdb_id}'
    url = f"{base_url}/{endpoint}?api_key={api_key}&language=es-ES" # Cambiado a es-ES
    logger.debug(f"Obteniendo detalles de TMDb: {url}")

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        tmdb_data = response.json()

        poster_path = tmdb_data.get('poster_path')
        if poster_path:
            tmdb_data['full_poster_url'] = f"{image_base_url}{poster_size}{poster_path}"
            logger.info(f"Póster encontrado para TMDb ID {tmdb_id}: {tmdb_data['full_poster_url']}")
        else:
            tmdb_data['full_poster_url'] = None
            logger.debug(f"No se encontró poster_path para TMDb ID {tmdb_id}")
        return tmdb_data
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al obtener detalles de TMDb para {item_type_for_tmdb} ID {tmdb_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red o API de TMDb: {e} para {item_type_for_tmdb} ID {tmdb_id}")
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON de detalles TMDb para {item_type_for_tmdb} ID {tmdb_id}: {e}")
    return {}


def process_content_data(content_list, item_type_app):
    """
    Procesa una lista de contenido, intentando obtener el póster de TMDb
    buscando por título y año.
    item_type_app es 'pelicula', 'serie', o 'anime' (como lo usas en tu app).
    """
    if not content_list:
        logger.info(f"Lista de contenido para '{item_type_app}' está vacía. Nada que procesar.")
        return []

    processed_list = []
    # Mapeo de tipos de tu app a tipos de TMDb
    tmdb_type_mapping = {
        'pelicula': 'movie',
        'serie': 'tv',
        'anime': 'tv' # TMDb trata anime como series de TV
    }
    item_type_for_tmdb = tmdb_type_mapping.get(item_type_app)

    if not item_type_for_tmdb:
        logger.error(f"Tipo de contenido de app desconocido '{item_type_app}' para mapeo a TMDb.")
        # Devolver la lista original sin procesar si el tipo no es mapeable
        return content_list


    for item_index, item in enumerate(content_list):
        title = item.get('titulo')
        # Asegúrate de que el campo 'anio' exista y sea un entero o string que represente un año
        year_str = str(item.get('anio', '')) # Convertir a string para asegurar consistencia
        year = None
        if year_str.isdigit() and len(year_str) == 4:
            year = int(year_str)
        else:
            logger.warning(f"Item '{title}' (índice {item_index}) no tiene un campo 'anio' válido ('{item.get('anio')}'). No se buscará póster por año.")


        poster_found_on_tmdb = False
        if title: # Necesitamos al menos el título
            # El año es opcional para la búsqueda pero muy recomendado para precisión
            found_tmdb_id = search_tmdb_by_name_year(title, year, item_type_for_tmdb)
            if found_tmdb_id:
                tmdb_info = get_tmdb_details_by_id(found_tmdb_id, item_type_for_tmdb)
                if tmdb_info.get('full_poster_url'):
                    item['poster'] = tmdb_info['full_poster_url']
                    poster_found_on_tmdb = True
                    # Opcional: Guardar el ID de TMDb encontrado si quieres usarlo después
                    item['tmdb_id_found'] = found_tmdb_id
                else:
                    logger.debug(f"TMDb ID {found_tmdb_id} (para '{title}') no devolvió URL de póster.")
            else:
                logger.debug(f"No se encontró TMDb ID para '{title}' ({year if year else 'Sin año'}).")
        else:
            logger.warning(f"Item en índice {item_index} de tipo '{item_type_app}' no tiene 'titulo'. No se puede buscar en TMDb.")

        if not poster_found_on_tmdb:
            # Si no se encontró póster de TMDb, o no se pudo buscar
            # se usará el campo 'poster' original si existe en el JSON, o un default.
            if 'poster' not in item or not item['poster']: # Si no hay poster en el JSON o está vacío
                logger.warning(f"No se pudo obtener póster de TMDb para '{title}'. Usando póster por defecto.")
                item['poster'] = settings.STATIC_URL + 'images/default_poster.jpg'
            else:
                logger.info(f"Usando póster existente del JSON para '{title}' ya que no se encontró en TMDb o no se pudo buscar.")
        
        processed_list.append(item)
    
    logger.info(f"Procesamiento de {len(processed_list)} items de tipo '{item_type_app}' completado.")
    return processed_list


# --- Cargar y procesar datos globalmente al iniciar el servidor ---
logger.info("Iniciando carga y procesamiento de datos global...")

# Cargar desde URL
raw_peliculas_data = load_json_from_url(settings.JSON_PELICULAS_URL)
raw_series_data = load_json_from_url(settings.JSON_SERIES_URL)
raw_anime_data = load_json_from_url(settings.JSON_ANIME_URL)

# Procesar datos cargados para obtener pósters
PELICULAS_DATA = process_content_data(raw_peliculas_data, 'pelicula') if raw_peliculas_data else []
SERIES_DATA = process_content_data(raw_series_data, 'serie') if raw_series_data else []
ANIME_DATA = process_content_data(raw_anime_data, 'anime') if raw_anime_data else []


# Fallback a archivos locales si la carga desde URL falló Y NO estamos en producción Vercel
if not PELICULAS_DATA and not settings.IS_VERCEL_PRODUCTION:
    logger.warning("Datos de PELÍCULAS no cargados desde URL. Intentando desde archivo local...")
    local_raw_peliculas = load_json_from_file('peliculas.json')
    PELICULAS_DATA = process_content_data(local_raw_peliculas, 'pelicula') if local_raw_peliculas else []

if not SERIES_DATA and not settings.IS_VERCEL_PRODUCTION:
    logger.warning("Datos de SERIES no cargados desde URL. Intentando desde archivo local...")
    local_raw_series = load_json_from_file('series.json')
    SERIES_DATA = process_content_data(local_raw_series, 'serie') if local_raw_series else []

if not ANIME_DATA and not settings.IS_VERCEL_PRODUCTION:
    logger.warning("Datos de ANIME no cargados desde URL. Intentando desde archivo local...")
    local_raw_anime = load_json_from_file('anime.json')
    ANIME_DATA = process_content_data(local_raw_anime, 'anime') if local_raw_anime else []

logger.info(f"Carga global de datos completada. Películas: {len(PELICULAS_DATA)}, Series: {len(SERIES_DATA)}, Anime: {len(ANIME_DATA)}")

# --- Vistas ---

def get_item_by_id(item_id, data_list):
    """Función auxiliar para encontrar un ítem por su ID en una lista."""
    if data_list:
        for item in data_list:
            # Asegurarse de que la comparación de IDs sea robusta (ej. string con string)
            if str(item.get('id')) == str(item_id):
                return item
    return None

def index_view(request):
    context = {
        'peliculas_count': len(PELICULAS_DATA),
        'series_count': len(SERIES_DATA),
        'anime_count': len(ANIME_DATA),
    }
    return render(request, 'catalogo/index.html', context)

def section_view(request, tipo_contenido):
    items_data = []
    titulo_seccion = ""
    query = request.GET.get('q', '') # Obtener query de búsqueda

    if tipo_contenido == 'peliculas':
        items_data_source = PELICULAS_DATA
        titulo_seccion = "Películas"
    elif tipo_contenido == 'series':
        items_data_source = SERIES_DATA
        titulo_seccion = "Series"
    elif tipo_contenido == 'anime':
        items_data_source = ANIME_DATA
        titulo_seccion = "Anime"
    else:
        raise Http404("Tipo de contenido no válido.")

    # Aplicar filtro de búsqueda si hay query
    if query:
        items_data = [
            item for item in items_data_source
            if query.lower() in item.get('titulo', '').lower()
        ]
        titulo_seccion = f"Resultados para '{query}' en {titulo_seccion.lower()}"
    else:
        items_data = items_data_source # Sin query, mostrar todo

    context = {
        'items': items_data,
        'titulo_seccion': titulo_seccion,
        'tipo_contenido': tipo_contenido,
        'query': query,
        # 'error_carga' es True si la fuente original estaba vacía Y no es una búsqueda
        'error_carga': not items_data_source and not query
    }
    return render(request, 'catalogo/section_page.html', context)

def movie_detail_view(request, item_id):
    item = get_item_by_id(item_id, PELICULAS_DATA)
    if not item:
        raise Http404("Película no encontrada.")
    
    # Asegúrate de que 'iframes' sea una lista, incluso si está vacío o no existe
    iframe_principal = item.get('iframes', [None])[0] if isinstance(item.get('iframes'), list) and item.get('iframes') else None


    context = {
        'item': item,
        'iframe_principal': iframe_principal,
        'tipo_contenido': 'pelicula'
    }
    return render(request, 'catalogo/movie_detail.html', context)


def series_anime_detail_view(request, item_id, tipo_contenido):
    data_list_source = []
    if tipo_contenido == 'series':
        data_list_source = SERIES_DATA
    elif tipo_contenido == 'anime':
        data_list_source = ANIME_DATA
    else:
        # Esto no debería ocurrir si las URLs están bien configuradas
        raise Http404("Tipo de contenido no válido para detalle.")

    item = get_item_by_id(item_id, data_list_source)

    if not item:
        raise Http404(f"{tipo_contenido.capitalize()} no encontrada.")

    # Asegura que las estructuras de temporadas y episodios existan para evitar errores de plantilla
    if 'temporadas' in item and isinstance(item['temporadas'], list):
        for season in item['temporadas']:
            if isinstance(season, dict) and 'episodios' in season and isinstance(season['episodios'], list):
                for episode in season['episodios']:
                    if isinstance(episode, dict):
                        episode.setdefault('iframes', []) # Asegura que iframes sea una lista
    
    context = {
        'item': item,
        'tipo_contenido': tipo_contenido
    }
    return render(request, 'catalogo/series_anime_detail.html', context)

@csrf_exempt
def report_link_view(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            content_id = payload.get('content_id')
            content_title = payload.get('content_title')
            reported_link = payload.get('reported_link')
            item_type = payload.get('item_type', 'Contenido')
            episode_title = payload.get('episode_title', '') # Puede estar vacío
            active_server_label = payload.get('active_server_label', 'Desconocido')

            if not all([content_id, content_title, reported_link]):
                return JsonResponse({'status': 'error', 'message': 'Datos incompletos para el reporte.'}, status=400)

            subject = f"Reporte de Enlace Caído: {content_title}"
            message_body_parts = [
                "Se ha reportado un enlace caído:",
                f"Tipo: {item_type.capitalize()}",
                f"ID: {content_id}",
                f"Título: {content_title}",
            ]
            if episode_title: # Solo añadir si tiene valor
                message_body_parts.append(f"Episodio: {episode_title}")
            
            message_body_parts.append(f"Servidor Reportado: {active_server_label}")
            message_body_parts.append(f"Enlace Reportado: {reported_link}")
            message_body_parts.append(f"Fecha y Hora del Reporte (servidor UTC): {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            message = "\n".join(message_body_parts)
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER], # O la lista de correos a donde enviar reportes
                    fail_silently=False,
                )
                logger.info(f"Email de reporte enviado para: {content_title} - Enlace: {reported_link}")
                return JsonResponse({'status': 'success', 'message': 'Reporte enviado con éxito.'})
            except Exception as e:
                logger.error(f"Error al enviar email de reporte ({content_title}): {e}")
                return JsonResponse({'status': 'error', 'message': f'Error interno al procesar el reporte. Intenta más tarde.'}, status=500)

        except json.JSONDecodeError:
            logger.warning("Reporte de enlace recibido con JSON inválido.")
            return JsonResponse({'status': 'error', 'message': 'Formato de datos inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado en report_link_view: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error inesperado en el servidor.'}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)


def search_view(request):
    query_original = request.GET.get('q', '').strip()
    query_lower = query_original.lower()
    
    search_results_items = [] 
    
    logger.info(f"Búsqueda global iniciada para: '{query_original}'")

    if not any([PELICULAS_DATA, SERIES_DATA, ANIME_DATA]): # Si todas las listas están vacías
        logger.warning("Search: Todas las fuentes de datos (PELICULAS_DATA, etc.) están vacías. No se puede buscar.")
    
    if query_lower: # Solo buscar si hay una query
        # Función interna para no repetir código
        def find_matches_in_list(data_list, item_type_str, list_name_for_log):
            if data_list: # Solo procesar si la lista tiene datos
                for item in data_list:
                    item_titulo = item.get('titulo', '')
                    if query_lower in item_titulo.lower():
                        logger.debug(f"Search: Coincidencia encontrada en {list_name_for_log} para '{query_original}': '{item_titulo}'")
                        # Añadir una copia del item con el 'tipo' para la plantilla
                        search_results_items.append({**item, 'tipo': item_type_str})
            else:
                logger.debug(f"Search: Lista '{list_name_for_log}' está vacía, omitiendo búsqueda en ella.")
        
        find_matches_in_list(PELICULAS_DATA, 'pelicula', 'PELICULAS_DATA')
        find_matches_in_list(SERIES_DATA, 'serie', 'SERIES_DATA')
        find_matches_in_list(ANIME_DATA, 'anime', 'ANIME_DATA')
    
    logger.info(f"Search: Se encontraron {len(search_results_items)} resultados para '{query_original}'.")

    context = {
        'query': query_original,
        'items': search_results_items, # Usar 'items' consistentemente
        'titulo_seccion': f"Resultados para: '{query_original}'" if query_original else "Realiza una búsqueda",
        'tipo_contenido': 'search', # Para diferenciar en la plantilla si es necesario
        'error_carga': False # La búsqueda no tiene 'error_carga' en el mismo sentido que una sección
    }
    return render(request, 'catalogo/section_page.html', context)