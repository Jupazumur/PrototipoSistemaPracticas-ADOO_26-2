from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.db import IntegrityError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import Administrador, Estudiante, Oferta, Postulacion

User = get_user_model()


def _estudiante_sesion(request):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return None
    return Estudiante.objects.filter(pk=estudiante_id).first()


def _usuario_admin_django(administrador, raw_password):
    user, _created = User.objects.get_or_create(
        username=administrador.correo,
        defaults={
            'email': administrador.correo,
            'first_name': administrador.nombre,
        },
    )
    user.email = administrador.correo
    user.first_name = administrador.nombre
    user.is_staff = True
    user.is_superuser = True
    user.set_password(raw_password)
    user.save()
    return user


def _redirigir_si_sesion(request):
    if _estudiante_sesion(request):
        return redirect('ofertas_disponibles')
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')
    return None


@require_http_methods(['GET', 'POST'])
def login_view(request):
    redireccion = _redirigir_si_sesion(request)
    if redireccion:
        return redireccion

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip()
        password = request.POST.get('password', '')

        administrador = Administrador.objects.filter(correo__iexact=correo).first()
        if administrador and administrador.check_password(password):
            user = _usuario_admin_django(administrador, password)
            auth_login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            request.session.pop('estudiante_id', None)
            return redirect('admin:index')

        estudiante = Estudiante.objects.filter(correo__iexact=correo).first()
        if estudiante and estudiante.check_password(password):
            auth_logout(request)
            request.session['estudiante_id'] = estudiante.estudiante_id
            return redirect('ofertas_disponibles')

        messages.error(request, 'Correo o contraseña incorrectos.')

    return render(request, 'sistema_practicas/login.html')


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('login')


def ofertas_disponibles(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('admin:index')

    estudiante = _estudiante_sesion(request)
    if not estudiante:
        messages.error(request, 'Inicia sesión para ver las ofertas.')
        return redirect('login')

    ofertas = (
        Oferta.objects.filter(vacantes__gt=0)
        .select_related('empresa')
        .order_by('-fecha_publicacion', 'titulo')
    )
    ofertas_postuladas = set(
        Postulacion.objects.filter(estudiante=estudiante).values_list(
            'oferta_id', flat=True
        )
    )
    return render(
        request,
        'sistema_practicas/ofertas_disponibles.html',
        {
            'estudiante': estudiante,
            'ofertas': ofertas,
            'ofertas_postuladas': ofertas_postuladas,
        },
    )


@require_POST
def postularse(request, oferta_id):
    estudiante = _estudiante_sesion(request)
    if not estudiante:
        messages.error(request, 'Inicia sesión para postularte.')
        return redirect('login')

    oferta = get_object_or_404(Oferta, pk=oferta_id)
    if oferta.vacantes <= 0:
        messages.error(request, 'Esta oferta ya no tiene vacantes disponibles.')
        return redirect('ofertas_disponibles')

    try:
        Postulacion.objects.create(
            fecha_postulacion=timezone.now().date(),
            estado='Pendiente',
            estudiante=estudiante,
            oferta=oferta,
        )
    except IntegrityError:
        messages.warning(request, 'Ya te postulaste a esta oferta.')
    else:
        messages.success(request, f'Te postulaste a "{oferta.titulo}".')

    return redirect('ofertas_disponibles')
