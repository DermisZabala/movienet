# catalogo/views.py
import json
import requests
from django.shortcuts import render, Http404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse # Importar reverse
import os
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)

# --- Funciones para cargar datos desde JSON (TU CÓDIGO) ---
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
        logger.error(f"Error decodificando JSON desde {url}: {e}. Respuesta recibida: {response.text[:500] if response else 'No response'}...")
        return None

def load_json_from_file(file_path):
    try:
        abs_file_path = os.path.join(settings.BASE_DIR, 'data', file_path) # Asumiendo que tus JSON locales están en una carpeta 'data'
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

# --- Funciones para la API de TMDb (TU CÓDIGO) ---
def search_tmdb_by_name_year(query, year, item_type_for_tmdb):
    api_key = settings.TMDB_API_KEY
    base_url = settings.TMDB_BASE_URL
    if not api_key: logger.warning("TMDB_API_KEY no está configurada."); return None
    if item_type_for_tmdb not in ['movie', 'tv']: logger.error(f"Tipo inválido TMDb: {item_type_for_tmdb}"); return None
    endpoint = f'search/{item_type_for_tmdb}'
    params = {'api_key': api_key, 'query': query, 'language': 'es-ES'}
    if item_type_for_tmdb == 'movie' and year: params['year'] = year
    elif item_type_for_tmdb == 'tv' and year: params['first_air_date_year'] = year
    url = f"{base_url}/{endpoint}"
    try:
        response = requests.get(url, params=params, timeout=5); response.raise_for_status()
        results = response.json()
        if results and results.get('results'): return results['results'][0].get('id')
    except Exception as e: logger.error(f"Error TMDb search '{query}' ({year}): {e}")
    return None

def get_tmdb_details_by_id(tmdb_id, item_type_for_tmdb):
    api_key = settings.TMDB_API_KEY; base_url = settings.TMDB_BASE_URL
    image_base_url = settings.TMDB_IMAGE_BASE_URL; poster_size = settings.TMDB_POSTER_SIZE
    if not api_key: logger.warning("TMDB_API_KEY no configurada."); return {}
    if item_type_for_tmdb not in ['movie', 'tv']: logger.error(f"Tipo inválido TMDb details: {item_type_for_tmdb}"); return {}
    endpoint = f'{item_type_for_tmdb}/{tmdb_id}'
    url = f"{base_url}/{endpoint}?api_key={api_key}&language=es-ES"
    try:
        response = requests.get(url, timeout=5); response.raise_for_status()
        data = response.json()
        if data.get('poster_path'): data['full_poster_url'] = f"{image_base_url}{poster_size}{data['poster_path']}"
        else: data['full_poster_url'] = None
        return data
    except Exception as e: logger.error(f"Error TMDb details ID {tmdb_id}: {e}")
    return {}

def process_content_data(content_list, item_type_app):
    if not content_list: return []
    processed_list = []
    tmdb_type_map = {'pelicula': 'movie', 'serie': 'tv', 'anime': 'tv'}
    item_type_tmdb = tmdb_type_map.get(item_type_app)
    if not item_type_tmdb: return content_list

    for item in content_list:
        title = item.get('titulo'); year_val = item.get('anio'); year = None
        try:
            if year_val is not None and str(year_val).isdigit() and len(str(year_val)) == 4:
                year = int(year_val); item['anio'] = year
            else: item['anio'] = None
        except: item['anio'] = None
        
        poster_found = False
        if title:
            tmdb_id = search_tmdb_by_name_year(title, year, item_type_tmdb)
            if tmdb_id:
                tmdb_info = get_tmdb_details_by_id(tmdb_id, item_type_tmdb)
                if tmdb_info.get('full_poster_url'):
                    item['poster'] = tmdb_info['full_poster_url']; poster_found = True
        
        if not poster_found and ('poster' not in item or not item['poster']):
            item['poster'] = os.path.join(settings.STATIC_URL, 'images', 'default_poster.jpg') # Usar os.path.join para STATIC_URL
        processed_list.append(item)
    return processed_list

# --- Carga y procesamiento global de datos (TU CÓDIGO AJUSTADO LIGERAMENTE) ---
logger.info("Iniciando carga y procesamiento de datos global...")
raw_peliculas_data = load_json_from_url(settings.JSON_PELICULAS_URL)
raw_series_data = load_json_from_url(settings.JSON_SERIES_URL)
raw_anime_data = load_json_from_url(settings.JSON_ANIME_URL)

PELICULAS_DATA = process_content_data(raw_peliculas_data, 'pelicula') if raw_peliculas_data else []
SERIES_DATA = process_content_data(raw_series_data, 'serie') if raw_series_data else []
ANIME_DATA = process_content_data(raw_anime_data, 'anime') if raw_anime_data else []

# Fallback a locales si la carga de URL falla y no estamos en producción Vercel
# (Ajusta la condición IS_VERCEL_PRODUCTION según tu entorno, ej. para Render podría ser diferente)
IS_PRODUCTION_ENV = os.environ.get('RENDER') == 'true' # Ejemplo para Render

if not PELICULAS_DATA and not IS_PRODUCTION_ENV:
    logger.warning("Datos de PELÍCULAS no cargados desde URL. Intentando desde archivo local...")
    local_raw_peliculas = load_json_from_file('peliculas.json')
    PELICULAS_DATA = process_content_data(local_raw_peliculas, 'pelicula') if local_raw_peliculas else []
# ... (similar para SERIES_DATA y ANIME_DATA) ...
if not SERIES_DATA and not IS_PRODUCTION_ENV:
    logger.warning("Datos de SERIES no cargados desde URL. Intentando desde archivo local...")
    local_raw_series = load_json_from_file('series.json')
    SERIES_DATA = process_content_data(local_raw_series, 'serie') if local_raw_series else []
if not ANIME_DATA and not IS_PRODUCTION_ENV:
    logger.warning("Datos de ANIME no cargados desde URL. Intentando desde archivo local...")
    local_raw_anime = load_json_from_file('anime.json')
    ANIME_DATA = process_content_data(local_raw_anime, 'anime') if local_raw_anime else []


def sort_key_year_robust(item):
    year_val = item.get('anio')
    return year_val if isinstance(year_val, int) else -1

if PELICULAS_DATA: PELICULAS_DATA.sort(key=sort_key_year_robust, reverse=True)
if SERIES_DATA: SERIES_DATA.sort(key=sort_key_year_robust, reverse=True)
if ANIME_DATA: ANIME_DATA.sort(key=sort_key_year_robust, reverse=True)
logger.info(f"Carga global completa. Películas: {len(PELICULAS_DATA)}, Series: {len(SERIES_DATA)}, Anime: {len(ANIME_DATA)}")

# --- Vistas (TU CÓDIGO CON LA NUEVA VISTA) ---
def get_item_by_id_from_global(item_id, tipo_contenido): # Renombrada para evitar conflicto
    data_list = []
    if tipo_contenido == 'pelicula': data_list = PELICULAS_DATA
    elif tipo_contenido == 'serie': data_list = SERIES_DATA
    elif tipo_contenido == 'anime': data_list = ANIME_DATA
    
    if data_list:
        for item in data_list:
            if str(item.get('id')) == str(item_id):
                return item
    return None

def index_view(request):
    context = {'peliculas_count': len(PELICULAS_DATA), 'series_count': len(SERIES_DATA), 'anime_count': len(ANIME_DATA)}
    return render(request, 'catalogo/index.html', context)

def section_view(request, tipo_contenido):
    items_data_source, titulo_seccion = [], ""
    if tipo_contenido == 'peliculas': items_data_source, titulo_seccion = PELICULAS_DATA, "Películas"
    elif tipo_contenido == 'series': items_data_source, titulo_seccion = SERIES_DATA, "Series"
    elif tipo_contenido == 'anime': items_data_source, titulo_seccion = ANIME_DATA, "Anime"
    else: raise Http404("Tipo no válido.")
    
    query = request.GET.get('q', '').strip()
    items_to_display = [item for item in items_data_source if query.lower() in item.get('titulo', '').lower()] if query else items_data_source
    if query: titulo_seccion = f"Resultados para '{query}' en {titulo_seccion.lower()}"
    
    context = {'items': items_to_display, 'titulo_seccion': titulo_seccion, 'tipo_contenido': tipo_contenido, 'query': query, 'error_carga': not items_data_source and not query}
    return render(request, 'catalogo/section_page.html', context)

def movie_detail_view(request, item_id):
    item = get_item_by_id_from_global(item_id, 'pelicula')
    if not item: raise Http404("Película no encontrada.")
    iframe_principal = item.get('iframes', [None])[0] if isinstance(item.get('iframes'), list) and item.get('iframes') else None
    context = {'item': item, 'iframe_principal': iframe_principal, 'tipo_contenido': 'pelicula'}
    return render(request, 'catalogo/movie_detail.html', context)

def series_anime_detail_view(request, item_id, tipo_contenido):
    item = get_item_by_id_from_global(item_id, tipo_contenido)
    if not item: raise Http404(f"{tipo_contenido.capitalize()} no encontrada.")
    # Asegurar que iframes exista en episodios (como en tu código original)
    if 'temporadas' in item and isinstance(item['temporadas'], list):
        for season in item['temporadas']:
            if isinstance(season, dict) and 'episodios' in season and isinstance(season['episodios'], list):
                for episode_idx, episode in enumerate(season['episodios']):
                    if isinstance(episode, dict):
                        episode.setdefault('iframes', [])
                        # Añadir número de episodio basado en el índice si no existe (para la URL)
                        episode.setdefault('numero_en_temporada', episode_idx + 1) 
    context = {'item': item, 'tipo_contenido': tipo_contenido}
    return render(request, 'catalogo/series_anime_detail.html', context)

# --- NUEVA VISTA PARA LA PÁGINA DE REPRODUCTOR DE EPISODIOS ---
def episodio_player_view(request, tipo_contenido, item_id, num_temporada, num_episodio_en_temporada):
    item_general = get_item_by_id_from_global(item_id, tipo_contenido)
    if not item_general:
        raise Http404(f"{tipo_contenido.capitalize()} no encontrado")

    episodio_actual = None
    temporada_actual_obj = None # Para tener el objeto temporada

    # Encontrar la temporada y el episodio actual
    if item_general.get('temporadas'):
        for temp_obj in item_general['temporadas']:
            if temp_obj.get('numero') == num_temporada:
                temporada_actual_obj = temp_obj
                if temp_obj.get('episodios'):
                    # Asumimos que num_episodio_en_temporada es 1-basado
                    if 0 < num_episodio_en_temporada <= len(temp_obj['episodios']):
                        episodio_actual = temp_obj['episodios'][num_episodio_en_temporada - 1]
                        episodio_actual.setdefault('numero_en_temporada', num_episodio_en_temporada) # Asegurar que lo tiene
                break 
    
    if not episodio_actual:
        raise Http404("Episodio no encontrado.")

    # Lógica para episodio anterior y siguiente
    # Construir una lista plana de todos los episodios para facilitar la navegación
    todos_los_episodios_flat = []
    if item_general.get('temporadas'):
        for temp in item_general['temporadas']:
            if temp.get('episodios'):
                for idx, ep in enumerate(temp['episodios']):
                    todos_los_episodios_flat.append({
                        'item_id': item_id,
                        'tipo_contenido': tipo_contenido,
                        'num_temporada': temp.get('numero'),
                        'num_episodio_en_temporada': ep.get('numero_en_temporada', idx + 1), # Usar el número si existe, sino el índice
                        'titulo': ep.get('titulo')
                    })
    
    enlace_anterior = None
    enlace_siguiente = None
    indice_global_actual = -1

    for i, ep_flat in enumerate(todos_los_episodios_flat):
        if ep_flat['num_temporada'] == num_temporada and ep_flat['num_episodio_en_temporada'] == num_episodio_en_temporada:
            indice_global_actual = i
            break
            
    if indice_global_actual > 0:
        ep_anterior_info = todos_los_episodios_flat[indice_global_actual - 1]
        enlace_anterior = reverse('catalogo:episodio_player', args=[
            ep_anterior_info['tipo_contenido'], 
            ep_anterior_info['item_id'], 
            ep_anterior_info['num_temporada'], 
            ep_anterior_info['num_episodio_en_temporada']
        ])

    if 0 <= indice_global_actual < len(todos_los_episodios_flat) - 1:
        ep_siguiente_info = todos_los_episodios_flat[indice_global_actual + 1]
        enlace_siguiente = reverse('catalogo:episodio_player', args=[
            ep_siguiente_info['tipo_contenido'], 
            ep_siguiente_info['item_id'], 
            ep_siguiente_info['num_temporada'], 
            ep_siguiente_info['num_episodio_en_temporada']
        ])

    enlace_lista_episodios = reverse(f'catalogo:{tipo_contenido}_detail', args=[item_id])

    context = {
        'item_general': item_general, 
        'episodio': episodio_actual,   
        'num_temporada': num_temporada,
        'num_episodio': num_episodio_en_temporada, # Nombre consistente en contexto
        'tipo_contenido': tipo_contenido,
        'page_title': f"{item_general.get('titulo')} - T{num_temporada}:E{num_episodio_en_temporada} {episodio_actual.get('titulo', '')}",
        'enlace_anterior': enlace_anterior,
        'enlace_lista_episodios': enlace_lista_episodios,
        'enlace_siguiente': enlace_siguiente,
    }
    return render(request, 'catalogo/episodio_player.html', context)


@csrf_exempt # (TU CÓDIGO)
def report_link_view(request):
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            content_id = payload.get('content_id'); content_title = payload.get('content_title')
            reported_link = payload.get('reported_link'); item_type = payload.get('item_type', 'Contenido')
            episode_title = payload.get('episode_title', ''); active_server_label = payload.get('active_server_label', 'Desconocido')
            if not all([content_id, content_title, reported_link]): return JsonResponse({'status': 'error', 'message': 'Datos incompletos.'}, status=400)
            subject = f"Reporte Enlace Caído: {content_title}"
            msg_parts = [
                "Reporte de enlace caído:", f"Tipo: {item_type.capitalize()}", f"ID: {content_id}", f"Título: {content_title}",
                (f"Episodio: {episode_title}" if episode_title else ""), f"Servidor: {active_server_label}",
                f"Enlace: {reported_link}", f"Fecha (UTC): {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
            ]
            message = "\n".join(filter(None, msg_parts))
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.EMAIL_HOST_USER], fail_silently=False)
            logger.info(f"Email reporte enviado: {content_title} - {reported_link}")
            return JsonResponse({'status': 'success', 'message': 'Reporte enviado.'})
        except json.JSONDecodeError: return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)
        except Exception as e: logger.error(f"Error report_link_view: {e}"); return JsonResponse({'status': 'error', 'message': 'Error interno.'}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

def search_view(request): # (TU CÓDIGO)
    query_original = request.GET.get('q', '').strip(); query_lower = query_original.lower()
    search_results_items = [] 
    if not any([PELICULAS_DATA, SERIES_DATA, ANIME_DATA]): logger.warning("Search: No hay datos.")
    if query_lower:
        def find_matches(data_list, item_type_str):
            if data_list:
                for item in data_list:
                    if query_lower in item.get('titulo', '').lower(): search_results_items.append({**item, 'tipo': item_type_str})
        find_matches(PELICULAS_DATA, 'pelicula'); find_matches(SERIES_DATA, 'serie'); find_matches(ANIME_DATA, 'anime')
    context = {'query': query_original, 'items': search_results_items, 'titulo_seccion': f"Resultados para: '{query_original}'" if query_original else "Realiza una búsqueda", 'tipo_contenido': 'search', 'error_carga': False}
    return render(request, 'catalogo/section_page.html', context)