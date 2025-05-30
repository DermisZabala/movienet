import json
import requests
from django.shortcuts import render, Http404
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import os
import logging # Para un mejor logging de errores

logger = logging.getLogger(__name__)

# --- Funciones para cargar datos desde JSON ---

def load_json_from_url(url):
    if not url or url == 'URL_RAW_DE_TU_PELICULAS.JSON_EN_GITHUB': # Evitar errores si la URL no está configurada
        logger.error(f"URL de JSON no configurada o es un placeholder: {url}")
        return None
    try:
        response = requests.get(url, timeout=10) # Timeout para evitar bloqueos indefinidos
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"Timeout al cargar JSON desde {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error de red cargando JSON desde {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON desde {url}: {e}")
        return None

def load_json_from_file(file_path):
    try:
        abs_file_path = os.path.join(settings.BASE_DIR, 'data', file_path)
        with open(abs_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Archivo JSON local no encontrado: {abs_file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON local desde: {abs_file_path} - {e}")
        return None

# --- Selecciona cómo cargar los JSON ---
# Decide si cargar desde local o GitHub. Este es un ejemplo, puedes hacerlo más dinámico.
USE_LOCAL_JSON = False # Cambia a False para usar GitHub (y configura las URLs en settings.py)

if USE_LOCAL_JSON:
    PELICULAS_DATA = load_json_from_file('peliculas.json') or []
    SERIES_DATA = load_json_from_file('series.json') or []
    ANIME_DATA = load_json_from_file('anime.json') or []
else:
    PELICULAS_DATA = load_json_from_url(settings.JSON_PELICULAS_URL) or []
    SERIES_DATA = load_json_from_url(settings.JSON_SERIES_URL) or []
    ANIME_DATA = load_json_from_url(settings.JSON_ANIME_URL) or []


# --- Vistas ---

def index_view(request):
    context = {
        'peliculas_count': len(PELICULAS_DATA),
        'series_count': len(SERIES_DATA),
        'anime_count': len(ANIME_DATA),
    }
    return render(request, 'catalogo/index.html', context)

def section_view(request, tipo_contenido):
    data = []
    titulo_seccion = ""
    query = request.GET.get('q', '')

    if tipo_contenido == 'peliculas':
        data_source = PELICULAS_DATA
        titulo_seccion = "Películas"
    elif tipo_contenido == 'series':
        data_source = SERIES_DATA
        titulo_seccion = "Series"
    elif tipo_contenido == 'anime':
        data_source = ANIME_DATA
        titulo_seccion = "Anime"
    else:
        raise Http404("Tipo de contenido no válido")

    # Si la fuente de datos está vacía (error de carga o JSON vacío), data seguirá siendo []
    if data_source:
        data = data_source
        if query: # Si hay búsqueda dentro de la sección
            data = [
                item for item in data_source 
                if query.lower() in item.get('titulo', '').lower()
            ]
            titulo_seccion = f"Resultados para '{query}' en {titulo_seccion}"

    context = {
        'items': data, # 'items' siempre existirá, podría ser una lista vacía
        'titulo_seccion': titulo_seccion,
        'tipo_contenido': tipo_contenido,
        'query': query,
        'resultados': None, # Para que la plantilla no falle
        'error_carga': not data_source and not query # Mostrar error si no hay datos y no es una búsqueda vacía
    }
    return render(request, 'catalogo/section_page.html', context)

def movie_detail_view(request, item_id):
    pelicula = next((p for p in PELICULAS_DATA if p.get('id') == item_id), None)
    if not pelicula:
        raise Http404("Película no encontrada")
    
    iframe_principal = pelicula.get('iframes', [None])[0]

    context = {
        'item': pelicula,
        'iframe_principal': iframe_principal,
        'tipo_contenido': 'pelicula' # Para el botón de reporte y JS
    }
    return render(request, 'catalogo/movie_detail.html', context)

def series_anime_detail_view(request, item_id, tipo_contenido):
    data_source = SERIES_DATA if tipo_contenido == 'series' else ANIME_DATA
    item = next((s for s in data_source if s.get('id') == item_id), None)

    if not item:
        raise Http404(f"{tipo_contenido.capitalize()} no encontrado")
    
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

            if not all([content_id, content_title, reported_link]):
                return JsonResponse({'status': 'error', 'message': 'Datos incompletos.'}, status=400)

            subject = f"Reporte de Enlace Caído: {content_title}"
            message_body_parts = [
                "Se ha reportado un enlace caído:\n",
                f"Tipo: {item_type.capitalize()}",
                f"ID: {content_id}",
                f"Título: {content_title}",
            ]
            if episode_title:
                 message_body_parts.append(f"Episodio: {episode_title}")
            
            message_body_parts.append(f"Enlace Reportado: {reported_link}")
            message_body_parts.append(f"Fecha y Hora del Reporte (servidor): {timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')}") # Necesita import timezone
            
            message = "\n".join(message_body_parts)
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.EMAIL_HOST_USER],
                    fail_silently=False,
                )
                logger.info(f"Email de reporte enviado para: {content_title} - {reported_link}")
                return JsonResponse({'status': 'success', 'message': 'Reporte enviado con éxito.'})
            except Exception as e:
                logger.error(f"Error al enviar email de reporte: {e}")
                return JsonResponse({'status': 'error', 'message': f'Error interno al procesar el reporte.'}, status=500)

        except json.JSONDecodeError:
            logger.warning("Reporte de enlace recibido con JSON inválido.")
            return JsonResponse({'status': 'error', 'message': 'JSON inválido.'}, status=400)
        except Exception as e:
            logger.error(f"Error inesperado en report_link_view: {e}")
            return JsonResponse({'status': 'error', 'message': 'Error inesperado en el servidor.'}, status=500)
            
    return JsonResponse({'status': 'error', 'message': 'Método no permitido.'}, status=405)

# Para la función de reporte con timezone
from django.utils import timezone

# catalogo/views.py
# ... (resto del código sin cambios) ...

def search_view(request):
    query_original = request.GET.get('q', '') 
    query_lower = query_original.lower()
    resultados_list = []

    # LOGS IMPORTANTES - DESCOMENTA TODOS SI ES NECESARIO
    logger.info(f"Search: Buscando '{query_original}' (procesado como '{query_lower}')")
    
    if not PELICULAS_DATA and not SERIES_DATA and not ANIME_DATA:
        logger.warning("Search: ¡ALERTA! Todas las fuentes de datos (PELICULAS_DATA, etc.) están vacías o son None.")
    else: # Para ver un ejemplo de los datos cargados
        if PELICULAS_DATA: logger.debug(f"Search: Ejemplo Películas[0]: {PELICULAS_DATA[0].get('titulo') if PELICULAS_DATA else 'Vacío'}")
        if SERIES_DATA: logger.debug(f"Search: Ejemplo Series[0]: {SERIES_DATA[0].get('titulo') if SERIES_DATA else 'Vacío'}")
        if ANIME_DATA: logger.debug(f"Search: Ejemplo Anime[0]: {ANIME_DATA[0].get('titulo') if ANIME_DATA else 'Vacío'}")

    if query_lower: 
        def add_if_match(item_list, item_type_str, list_name_for_log): # Añadido list_name_for_log
            if item_list:
                logger.debug(f"Search: Revisando lista '{list_name_for_log}' (tiene {len(item_list)} items)")
                for item in item_list:
                    item_titulo = item.get('titulo', '')
                    item_titulo_lower = item_titulo.lower()
                    
                    logger.debug(f"Search: Comparando query '{query_lower}' con título '{item_titulo_lower}' (original: '{item_titulo}')")
                    
                    if query_lower in item_titulo_lower:
                        logger.info(f"Search: ¡COINCIDENCIA ENCONTRADA en {list_name_for_log}! Añadiendo '{item_titulo}' a resultados.")
                        resultados_list.append({**item, 'tipo': item_type_str})
                    else: # Descomentar para MÁXIMO detalle
                        logger.debug(f"Search: No coincide '{query_lower}' con '{item_titulo_lower}'")
            else:
                logger.warning(f"Search: La lista '{list_name_for_log}' está vacía o es None, no se puede buscar en ella.")
        
        add_if_match(PELICULAS_DATA, 'pelicula', 'PELICULAS_DATA')
        add_if_match(SERIES_DATA, 'serie', 'SERIES_DATA')
        add_if_match(ANIME_DATA, 'anime', 'ANIME_DATA')
    
    logger.info(f"Search: Resultados finales para '{query_original}': {len(resultados_list)} items. Lista: {resultados_list}")

    context = {
        'query': query_original,
        'resultados': resultados_list, 
        'titulo_seccion': f"Resultados para: '{query_original}'" if query_original else "Realiza una búsqueda",
        'items': None, 
        'tipo_contenido': 'search' 
    }
    return render(request, 'catalogo/section_page.html', context)