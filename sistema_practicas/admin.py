from django import forms
from django.contrib import admin

from .models import Administrador, Empresa, Estudiante, Oferta, Postulacion


class PasswordAdminMixin:
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['password'].widget = forms.PasswordInput()
        form.base_fields['password'].required = obj is None
        if obj:
            form.base_fields['password'].help_text = 'Dejar vacío para conservar la contraseña actual.'
        return form

    def save_model(self, request, obj, form, change):
        raw_password = form.cleaned_data.get('password')
        if change and not raw_password:
            obj.password = type(obj).objects.get(pk=obj.pk).password
        elif raw_password:
            obj.set_password(raw_password)
        super().save_model(request, obj, form, change)


@admin.register(Administrador)
class AdministradorAdmin(PasswordAdminMixin, admin.ModelAdmin):
    list_display = ('administrador_id', 'nombre', 'correo')
    search_fields = ('nombre', 'correo')


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('empresa_id', 'nombre', 'correo', 'telefono', 'administrador')
    search_fields = ('nombre', 'correo', 'telefono')
    list_filter = ('administrador',)


@admin.register(Estudiante)
class EstudianteAdmin(PasswordAdminMixin, admin.ModelAdmin):
    list_display = ('estudiante_id', 'nombre', 'correo', 'carrera', 'administrador')
    search_fields = ('nombre', 'correo', 'carrera')
    list_filter = ('carrera', 'administrador')


@admin.register(Oferta)
class OfertaAdmin(admin.ModelAdmin):
    list_display = (
        'oferta_id',
        'titulo',
        'empresa',
        'vacantes',
        'tipo',
        'fecha_publicacion',
        'administrador',
    )
    search_fields = ('titulo', 'descripcion')
    list_filter = ('tipo', 'empresa', 'fecha_publicacion')


@admin.register(Postulacion)
class PostulacionAdmin(admin.ModelAdmin):
    list_display = (
        'postulacion_id',
        'estudiante',
        'oferta',
        'estado',
        'fecha_postulacion',
    )
    search_fields = ('estudiante__nombre', 'oferta__titulo', 'estado')
    list_filter = ('estado', 'fecha_postulacion')
