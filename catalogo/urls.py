from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('peliculas/', views.section_view, {'tipo_contenido': 'peliculas'}, name='peliculas'),
    path('series/', views.section_view, {'tipo_contenido': 'series'}, name='series'),
    path('anime/', views.section_view, {'tipo_contenido': 'anime'}, name='anime'),
    path('pelicula/<str:item_id>/', views.movie_detail_view, name='movie_detail'),
    # Detalle de Serie (donde se listan las temporadas y episodios)
    path('serie/<str:item_id>/', views.series_anime_detail_view, {'tipo_contenido': 'serie'}, name='serie_detail'),
    # Detalle de Anime (donde se listan las temporadas y episodios)
    path('anime/<str:item_id>/', views.series_anime_detail_view, {'tipo_contenido': 'anime'}, name='anime_detail'),
    
    # NUEVA URL para la página de reproducción del episodio
    # Asegúrate de que 'tipo_contenido' en la URL coincida con 'serie' o 'anime'
    path('<str:tipo_contenido>/<str:item_id>/temporada/<int:num_temporada>/episodio/<int:num_episodio_en_temporada>/play/', 
         views.episodio_player_view, 
         name='episodio_player'),
    path('reportar-enlace/', views.report_link_view, name='report_link'),
    path('buscar/', views.search_view, name='search'),
]