from django.urls import path
from . import views

urlpatterns = [
    path('score/',        views.score_geometry,  name='score-geometry'),
    path('zones/',        views.list_zones,       name='list-zones'),
    path('zones/<int:pk>/', views.zone_detail,   name='zone-detail'),
    path('stats/',        views.risk_stats,       name='risk-stats'),
    path('model-info/',   views.model_info,       name='model-info'),
]