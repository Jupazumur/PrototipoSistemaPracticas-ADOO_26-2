from datetime import datetime

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login, logout as auth_logout
from django.db import IntegrityError
from django.db.models import Count, Prefetch, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .models import Administrador, Empresa, Estudiante, Oferta, Postulacion

User = get_user_model()


def _estudiante_sesion(request):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return None
    return Estudiante.objects.filter(pk=estudiante_id).first()


def _administrador_sesion(request):
    administrador_id = request.session.get('administrador_id')
    if administrador_id:
        administrador = Administrador.objects.filter(pk=administrador_id).first()
        if administrador:
            return administrador
    if request.user.is_authenticated and request.user.is_staff:
        return Administrador.objects.filter(correo__iexact=request.user.username).first()
    return None


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


def _parse_fecha(valor):
    try:
        return datetime.strptime(valor, '%Y-%m-%d').date()
    except (TypeError, ValueError):
        return None


def _redirigir_si_sesion(request):
    if _estudiante_sesion(request):
        return redirect('ofertas_disponibles')
    if _administrador_sesion(request):
        return redirect('panel_admin')
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
            request.session['administrador_id'] = administrador.administrador_id
            return redirect('panel_admin')

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
    if _administrador_sesion(request):
        return redirect('panel_admin')

    estudiante = _estudiante_sesion(request)
    if not estudiante:
        messages.error(request, 'Inicia sesión para ver las ofertas.')
        return redirect('login')

    ofertas = (
        Oferta.objects.filter(vacantes__gt=0)
        .select_related('empresa')
        .prefetch_related('carreras')
        .order_by('-fecha_publicacion', 'titulo')
    )
    ofertas_postuladas = set(
        Postulacion.objects.filter(estudiante=estudiante).values_list(
            'oferta_id', flat=True
        )
    )

    context = {
        'estudiante': estudiante,
        'ofertas': ofertas,
        'ofertas_postuladas': ofertas_postuladas,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'sistema_practicas/partials/lista_ofertas.html', context)

    return render(request, 'sistema_practicas/ofertas_disponibles.html', context)


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
        messages.success(request, f'Te postulaste a "{oferta.titulo}".')    # ... (código previo) ...

    if request.headers.get('HX-Request'):
        ofertas = (
            Oferta.objects.filter(vacantes__gt=0)
            .select_related('empresa')
            .prefetch_related('carreras')
            .order_by('-fecha_publicacion', 'titulo')
        )
        ofertas_postuladas = set(
            Postulacion.objects.filter(estudiante=estudiante).values_list(
                'oferta_id', flat=True
            )
        )
        return render(
            request,
            'sistema_practicas/partials/lista_ofertas.html',
            {
                'estudiante': estudiante,
                'ofertas': ofertas,
                'ofertas_postuladas': ofertas_postuladas,
            },
        )

    return redirect('ofertas_disponibles')


def panel_admin(request):
    if _estudiante_sesion(request) and not _administrador_sesion(request):
        return redirect('ofertas_disponibles')

    administrador = _administrador_sesion(request)
    if not administrador:
        messages.error(request, 'Inicia sesión como administrador para ver el panel.')
        return redirect('login')

    empresas = Empresa.objects.order_by('nombre')
    tipos = (
        Oferta.objects.exclude(tipo='')
        .order_by('tipo')
        .values_list('tipo', flat=True)
        .distinct()
    )
    estados = (
        Postulacion.objects.exclude(estado='')
        .order_by('estado')
        .values_list('estado', flat=True)
        .distinct()
    )

    filtros = {
        'empresa': request.GET.get('empresa', '').strip(),
        'tipo': request.GET.get('tipo', '').strip(),
        'estado': request.GET.get('estado', '').strip(),
        'fecha_desde': request.GET.get('fecha_desde', '').strip(),
        'fecha_hasta': request.GET.get('fecha_hasta', '').strip(),
        'q': request.GET.get('q', '').strip(),
    }

    postulaciones_qs = Postulacion.objects.select_related('estudiante__carrera').order_by(
        '-fecha_postulacion', 'estudiante__nombre'
    )
    if filtros['estado']:
        postulaciones_qs = postulaciones_qs.filter(estado=filtros['estado'])

    ofertas = (
        Oferta.objects.select_related('empresa')
        .annotate(num_postulaciones=Count('postulaciones', distinct=True))
        .prefetch_related('carreras', Prefetch('postulaciones', queryset=postulaciones_qs))
        .order_by('-fecha_publicacion', 'titulo')
    )

    if filtros['empresa']:
        ofertas = ofertas.filter(empresa_id=filtros['empresa'])
    if filtros['tipo']:
        ofertas = ofertas.filter(tipo=filtros['tipo'])
    if filtros['estado']:
        ofertas = ofertas.filter(postulaciones__estado=filtros['estado']).distinct()
    fecha_desde = _parse_fecha(filtros['fecha_desde'])
    fecha_hasta = _parse_fecha(filtros['fecha_hasta'])
    if fecha_desde:
        ofertas = ofertas.filter(fecha_publicacion__gte=fecha_desde)
    if fecha_hasta:
        ofertas = ofertas.filter(fecha_publicacion__lte=fecha_hasta)
    if filtros['q']:
        ofertas = ofertas.filter(
            Q(titulo__icontains=filtros['q'])
            | Q(descripcion__icontains=filtros['q'])
            | Q(empresa__nombre__icontains=filtros['q'])
        )

    context = {
        'administrador': administrador,
        'ofertas': ofertas,
        'empresas': empresas,
        'tipos': tipos,
        'estados': estados,
        'filtros': filtros,
    }

    if request.headers.get('HX-Request'):
        return render(request, 'sistema_practicas/partials/tabla_admin.html', context)

    return render(request, 'sistema_practicas/panel_admin.html', context)