from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='search_page'),
    path('api/search/', views.search_api, name='search_api'),
    path('api/track/<str:product_id>/', views.track_product_api, name='track_product_api'),
    path('dashboard/<str:product_id>/', views.dashboard_view, name='product_dashboard'),
]
