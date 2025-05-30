from django.urls import path
from . import views

app_name = 'catalogo'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('peliculas/', views.section_view, {'tipo_contenido': 'peliculas'}, name='peliculas'),
    path('series/', views.section_view, {'tipo_contenido': 'series'}, name='series'),
    path('anime/', views.section_view, {'tipo_contenido': 'anime'}, name='anime'),
    path('pelicula/<str:item_id>/', views.movie_detail_view, name='movie_detail'),
    path('serie/<str:item_id>/', views.series_anime_detail_view, {'tipo_contenido': 'series'}, name='serie_detail'),
    path('anime/<str:item_id>/', views.series_anime_detail_view, {'tipo_contenido': 'anime'}, name='anime_detail'),
    path('reportar-enlace/', views.report_link_view, name='report_link'),
    path('buscar/', views.search_view, name='search'),
]