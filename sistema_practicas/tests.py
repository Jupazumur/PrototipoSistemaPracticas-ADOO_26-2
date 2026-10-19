from datetime import date

from django.test import TestCase
from django.urls import reverse

from .models import Administrador, Empresa, Estudiante, Oferta, Postulacion


class PanelAdminTests(TestCase):
    def setUp(self):
        self.admin = Administrador.objects.create(
            nombre='Ana Admin',
            correo='ana@uam.mx',
            password='admin123',
        )
        self.empresa_a = Empresa.objects.create(
            nombre='Empresa Alfa',
            descripcion='Consultora',
            telefono='5551111111',
            correo='alfa@empresa.com',
            administrador=self.admin,
        )
        self.empresa_b = Empresa.objects.create(
            nombre='Empresa Beta',
            descripcion='Fintech',
            telefono='5552222222',
            correo='beta@empresa.com',
            administrador=self.admin,
        )
        self.oferta_a = Oferta.objects.create(
            titulo='Prácticas backend',
            descripcion='API en Django',
            requisitos='Python',
            vacantes=2,
            fecha_publicacion=date(2026, 1, 10),
            tipo='Tiempo completo',
            administrador=self.admin,
            empresa=self.empresa_a,
        )
        self.oferta_b = Oferta.objects.create(
            titulo='Prácticas frontend',
            descripcion='UI en React',
            requisitos='JavaScript',
            vacantes=1,
            fecha_publicacion=date(2026, 3, 5),
            tipo='Medio tiempo',
            administrador=self.admin,
            empresa=self.empresa_b,
        )
        self.estudiante = Estudiante.objects.create(
            nombre='Luis Estudiante',
            correo='luis@uam.mx',
            password='alumno123',
            carrera='Computación',
            administrador=self.admin,
        )
        Postulacion.objects.create(
            fecha_postulacion=date(2026, 1, 15),
            estado='Pendiente',
            estudiante=self.estudiante,
            oferta=self.oferta_a,
        )

    def _login_admin(self):
        return self.client.post(
            reverse('login'),
            {'correo': 'ana@uam.mx', 'password': 'admin123'},
        )

    def test_login_admin_redirige_al_panel(self):
        respuesta = self._login_admin()
        self.assertRedirects(respuesta, reverse('panel_admin'))

    def test_panel_muestra_ofertas_y_postulantes(self):
        self._login_admin()
        respuesta = self.client.get(reverse('panel_admin'))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Prácticas backend')
        self.assertContains(respuesta, 'Luis Estudiante')
        self.assertContains(respuesta, 'Prácticas frontend')
        self.assertContains(respuesta, 'Nadie se ha postulado')

    def test_filtro_por_empresa(self):
        self._login_admin()
        respuesta = self.client.get(
            reverse('panel_admin'),
            {'empresa': self.empresa_b.empresa_id},
        )
        self.assertContains(respuesta, 'Prácticas frontend')
        self.assertNotContains(respuesta, 'Prácticas backend')

    def test_filtro_por_fecha(self):
        self._login_admin()
        respuesta = self.client.get(
            reverse('panel_admin'),
            {'fecha_desde': '2026-03-01', 'fecha_hasta': '2026-03-31'},
        )
        self.assertContains(respuesta, 'Prácticas frontend')
        self.assertNotContains(respuesta, 'Prácticas backend')

    def test_estudiante_no_accede_al_panel(self):
        self.client.post(
            reverse('login'),
            {'correo': 'luis@uam.mx', 'password': 'alumno123'},
        )
        respuesta = self.client.get(reverse('panel_admin'))
        self.assertRedirects(respuesta, reverse('ofertas_disponibles'))
