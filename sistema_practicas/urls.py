from django.urls import path

from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('cerrar-sesion/', views.logout_view, name='logout'),
    path('panel/', views.panel_admin, name='panel_admin'),
    path('ofertas/', views.ofertas_disponibles, name='ofertas_disponibles'),
    path(
        'ofertas/<int:oferta_id>/postularse/',
        views.postularse,
        name='postularse',
    ),
]
