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
    if not url:
        logger.error(f"URL de JSON no configurada.")
        return None
    try:
        logger.info(f"Intentando cargar JSON desde URL: {url}")
        response = requests.get(url, timeout=15)
        response.raise_for_status()
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
        logger.error(f"Error decodificando JSON desde {url}: {e}. Respuesta recibida: {response.text[:500]}...")
        return None

def load_json_from_file(file_path):
    try:
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
    api_key = settings.TMDB_API_KEY
    base_url = settings.TMDB_BASE_URL

    if not api_key:
        logger.warning("TMDB_API_KEY no está configurada en settings.")
        return None
    if item_type_for_tmdb not in ['movie', 'tv']:
        logger.error(f"Tipo de item inválido para búsqueda TMDb: {item_type_for_tmdb}")
        return None

    endpoint = f'search/{item_type_for_tmdb}'
    params = {'api_key': api_key, 'query': query, 'language': 'es-ES'}
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
    url = f"{base_url}/{endpoint}?api_key={api_key}&language=es-ES"
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
    if not content_list:
        logger.info(f"Lista de contenido para '{item_type_app}' está vacía. Nada que procesar.")
        return []

    processed_list = []
    tmdb_type_mapping = {'pelicula': 'movie', 'serie': 'tv', 'anime': 'tv'}
    item_type_for_tmdb = tmdb_type_mapping.get(item_type_app)

    if not item_type_for_tmdb:
        logger.error(f"Tipo de contenido de app desconocido '{item_type_app}' para mapeo a TMDb.")
        return content_list

    for item_index, item in enumerate(content_list):
        title = item.get('titulo')
        # El campo 'anio' debe ser un entero para la ordenación y búsqueda en TMDb
        # Si no es un entero o no existe, se usa None para la búsqueda en TMDb
        # y la función de ordenación lo manejará.
        year = None
        try:
            year_val = item.get('anio')
            if year_val is not None: # Solo intentar convertir si no es None
                year_str = str(year_val)
                if year_str.isdigit() and len(year_str) == 4:
                    year = int(year_str)
                    item['anio'] = year # Asegurar que 'anio' en el item sea un entero si es válido
                else:
                    logger.warning(f"Item '{title}' (índice {item_index}) tiene 'anio' no numérico o no de 4 dígitos: '{year_val}'. Se tratará como sin año.")
                    item['anio'] = None # Marcar como None para la ordenación
        except Exception as e:
            logger.warning(f"Error procesando 'anio' para '{title}': {e}. Se tratará como sin año.")
            item['anio'] = None

        poster_found_on_tmdb = False
        if title:
            found_tmdb_id = search_tmdb_by_name_year(title, year, item_type_for_tmdb)
            if found_tmdb_id:
                tmdb_info = get_tmdb_details_by_id(found_tmdb_id, item_type_for_tmdb)
                if tmdb_info.get('full_poster_url'):
                    item['poster'] = tmdb_info['full_poster_url']
                    poster_found_on_tmdb = True
                    item['tmdb_id_found'] = found_tmdb_id
                else:
                    logger.debug(f"TMDb ID {found_tmdb_id} (para '{title}') no devolvió URL de póster.")
            else:
                logger.debug(f"No se encontró TMDb ID para '{title}' ({year if year else 'Sin año'}).")
        else:
            logger.warning(f"Item en índice {item_index} de tipo '{item_type_app}' no tiene 'titulo'. No se puede buscar en TMDb.")

        if not poster_found_on_tmdb:
            if 'poster' not in item or not item['poster']:
                logger.warning(f"No se pudo obtener póster de TMDb para '{title}'. Usando póster por defecto.")
                item['poster'] = settings.STATIC_URL + 'images/default_poster.jpg'
            else:
                logger.info(f"Usando póster existente del JSON para '{title}' ya que no se encontró en TMDb o no se pudo buscar.")
        
        processed_list.append(item)
    
    logger.info(f"Procesamiento de {len(processed_list)} items de tipo '{item_type_app}' completado.")
    return processed_list

# --- Cargar y procesar datos globalmente al iniciar el servidor ---
logger.info("Iniciando carga y procesamiento de datos global...")

raw_peliculas_data = load_json_from_url(settings.JSON_PELICULAS_URL)
raw_series_data = load_json_from_url(settings.JSON_SERIES_URL)
raw_anime_data = load_json_from_url(settings.JSON_ANIME_URL)

PELICULAS_DATA = process_content_data(raw_peliculas_data, 'pelicula') if raw_peliculas_data else []
SERIES_DATA = process_content_data(raw_series_data, 'serie') if raw_series_data else []
ANIME_DATA = process_content_data(raw_anime_data, 'anime') if raw_anime_data else []

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

logger.info(f"Carga global de datos completada ANTES de ordenar. Películas: {len(PELICULAS_DATA)}, Series: {len(SERIES_DATA)}, Anime: {len(ANIME_DATA)}")

# --- ORDENAR LOS DATOS POR AÑO (MÁS RECIENTES PRIMERO) ---
def sort_key_year_robust(item):
    year_val = item.get('anio') # 'anio' debería ser int o None después de process_content_data
    if isinstance(year_val, int):
        return year_val
    return -1 # Ítems sin año válido van al final (para orden descendente)

if PELICULAS_DATA:
    PELICULAS_DATA.sort(key=sort_key_year_robust, reverse=True)
    logger.info("PELICULAS_DATA ordenado por año descendente.")
if SERIES_DATA:
    SERIES_DATA.sort(key=sort_key_year_robust, reverse=True)
    logger.info("SERIES_DATA ordenado por año descendente.")
if ANIME_DATA:
    ANIME_DATA.sort(key=sort_key_year_robust, reverse=True)
    logger.info("ANIME_DATA ordenado por año descendente.")

logger.info(f"Carga global de datos completada DESPUÉS de ordenar. Películas: {len(PELICULAS_DATA)}, Series: {len(SERIES_DATA)}, Anime: {len(ANIME_DATA)}")
# logger.debug(f"Primeras películas después de ordenar: {PELICULAS_DATA[:3] if PELICULAS_DATA else 'Ninguna'}")

# --- Vistas ---

def get_item_by_id(item_id, data_list):
    if data_list:
        for item in data_list:
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
    items_data_source = [] # Fuente original antes de filtrar por query
    items_to_display = []  # Lista final a mostrar
    titulo_seccion = ""
    query = request.GET.get('q', '').strip()

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

    if query:
        items_to_display = [
            item for item in items_data_source
            if query.lower() in item.get('titulo', '').lower()
        ]
        titulo_seccion = f"Resultados para '{query}' en {titulo_seccion.lower()}"
    else:
        items_to_display = items_data_source

    context = {
        'items': items_to_display,
        'titulo_seccion': titulo_seccion,
        'tipo_contenido': tipo_contenido,
        'query': query,
        'error_carga': not items_data_source and not query
    }
    return render(request, 'catalogo/section_page.html', context)

def movie_detail_view(request, item_id):
    item = get_item_by_id(item_id, PELICULAS_DATA)
    if not item:
        raise Http404("Película no encontrada.")
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
        raise Http404("Tipo de contenido no válido para detalle.")
    item = get_item_by_id(item_id, data_list_source)
    if not item:
        raise Http404(f"{tipo_contenido.capitalize()} no encontrada.")
    if 'temporadas' in item and isinstance(item['temporadas'], list):
        for season in item['temporadas']:
            if isinstance(season, dict) and 'episodios' in season and isinstance(season['episodios'], list):
                for episode in season['episodios']:
                    if isinstance(episode, dict):
                        episode.setdefault('iframes', [])
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
            episode_title = payload.get('episode_title', '')
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
            if episode_title:
                message_body_parts.append(f"Episodio: {episode_title}")
            message_body_parts.append(f"Servidor Reportado: {active_server_label}")
            message_body_parts.append(f"Enlace Reportado: {reported_link}")
            message_body_parts.append(f"Fecha y Hora del Reporte (servidor UTC): {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}")
            message = "\n".join(message_body_parts)
            
            send_mail(
                subject, message, settings.DEFAULT_FROM_EMAIL,
                [settings.EMAIL_HOST_USER], fail_silently=False,
            )
            logger.info(f"Email de reporte enviado para: {content_title} - Enlace: {reported_link}")
            return JsonResponse({'status': 'success', 'message': 'Reporte enviado con éxito.'})
        except json.JSONDecodeError:
            logger.warning("Reporte de enlace recibido con JSON inválido.")
            return JsonResponse({'status': 'error', 'message': 'Formato de datos inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Error en report_link_view ({content_title if 'content_title' in locals() else 'N/A'}): {e}")
            return JsonResponse({'status': 'error', 'message': f'Error interno al procesar el reporte. Intenta más tarde.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def search_view(request):
    query_original = request.GET.get('q', '').strip()
    query_lower = query_original.lower()
    search_results_items = [] 
    logger.info(f"Búsqueda global iniciada para: '{query_original}'")

    if not any([PELICULAS_DATA, SERIES_DATA, ANIME_DATA]):
        logger.warning("Search: Todas las fuentes de datos están vacías. No se puede buscar.")
    
    if query_lower:
        def find_matches_in_list(data_list, item_type_str, list_name_for_log):
            if data_list:
                for item in data_list:
                    item_titulo = item.get('titulo', '')
                    if query_lower in item_titulo.lower():
                        logger.debug(f"Search: Coincidencia encontrada en {list_name_for_log} para '{query_original}': '{item_titulo}'")
                        search_results_items.append({**item, 'tipo': item_type_str})
            else:
                logger.debug(f"Search: Lista '{list_name_for_log}' está vacía, omitiendo búsqueda en ella.")
        
        find_matches_in_list(PELICULAS_DATA, 'pelicula', 'PELICULAS_DATA')
        find_matches_in_list(SERIES_DATA, 'serie', 'SERIES_DATA')
        find_matches_in_list(ANIME_DATA, 'anime', 'ANIME_DATA')
    
    # OPCIONAL: Ordenar los resultados de la búsqueda también por año si se desea
    # if search_results_items:
    # search_results_items.sort(key=sort_key_year_robust, reverse=True)
    # logger.info(f"Resultados de búsqueda ordenados por año descendente.")

    logger.info(f"Search: Se encontraron {len(search_results_items)} resultados para '{query_original}'.")
    context = {
        'query': query_original,
        'items': search_results_items,
        'titulo_seccion': f"Resultados para: '{query_original}'" if query_original else "Realiza una búsqueda",
        'tipo_contenido': 'search',
        'error_carga': False
    }
    return render(request, 'catalogo/section_page.html', context)