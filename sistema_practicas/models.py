from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.db import models


class PasswordMixin:
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        if self.password:
            try:
                identify_hasher(self.password)
            except ValueError:
                self.password = make_password(self.password)
        super().save(*args, **kwargs)


class Administrador(PasswordMixin, models.Model):
    administrador_id = models.AutoField(primary_key=True, db_column='Administrador_ID')
    nombre = models.CharField(max_length=100)
    correo = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)

    class Meta:
        db_table = 'Administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'

    def __str__(self):
        return self.nombre


class Empresa(models.Model):
    empresa_id = models.AutoField(primary_key=True, db_column='Empresa_ID')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    telefono = models.CharField(max_length=15, unique=True)
    correo = models.CharField(max_length=100, unique=True)
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.CASCADE,
        db_column='Administrador_ID',
        related_name='empresas',
    )

    class Meta:
        db_table = 'Empresa'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    carrera_id = models.AutoField(primary_key=True, db_column='Carrera_ID')
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'Carrera'
        verbose_name = 'Carrera'
        verbose_name_plural = 'Carreras'

    def __str__(self):
        return self.nombre


class Estudiante(PasswordMixin, models.Model):
    estudiante_id = models.AutoField(primary_key=True, db_column='Estudiante_ID')
    nombre = models.CharField(max_length=100)
    correo = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=128)
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='estudiantes',
    )
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.CASCADE,
        db_column='Administrador_ID',
        related_name='estudiantes',
    )

    class Meta:
        db_table = 'Estudiante'
        verbose_name = 'Estudiante'
        verbose_name_plural = 'Estudiantes'

    def __str__(self):
        return self.nombre


class Oferta(models.Model):
    class TipoOferta(models.TextChoices):
        PRACTICAS = 'Prácticas', 'Prácticas'
        SERVICIO_SOCIAL = 'Servicio Social', 'Servicio Social'

    oferta_id = models.AutoField(primary_key=True, db_column='Oferta_ID')
    titulo = models.CharField(max_length=100)
    descripcion = models.TextField()
    requisitos = models.TextField()
    vacantes = models.IntegerField()
    fecha_publicacion = models.DateField()
    tipo = models.CharField(
        max_length=30,
        choices=TipoOferta.choices,
    )
    carreras = models.ManyToManyField(
        Carrera,
        related_name='ofertas',
        blank=True,
    )
    administrador = models.ForeignKey(
        Administrador,
        on_delete=models.CASCADE,
        db_column='Administrador_ID',
        related_name='ofertas',
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        db_column='Empresa_ID',
        related_name='ofertas',
    )

    class Meta:
        db_table = 'Oferta'
        verbose_name = 'Oferta'
        verbose_name_plural = 'Ofertas'

    def __str__(self):
        return self.titulo


class Postulacion(models.Model):
    class EstadoPostulacion(models.TextChoices):
        PENDIENTE = 'Pendiente', 'Pendiente'
        ACEPTADO = 'Aceptado', 'Aceptado'
        RECHAZADO = 'Rechazado', 'Rechazado'

    postulacion_id = models.AutoField(primary_key=True, db_column='Postulacion_ID')
    fecha_postulacion = models.DateField()
    estado = models.CharField(
        max_length=30,
        choices=EstadoPostulacion.choices,
        default=EstadoPostulacion.PENDIENTE,
    )
    estudiante = models.ForeignKey(
        Estudiante,
        on_delete=models.CASCADE,
        db_column='Estudiante_ID',
        related_name='postulaciones',
    )
    oferta = models.ForeignKey(
        Oferta,
        on_delete=models.CASCADE,
        db_column='Oferta_ID',
        related_name='postulaciones',
    )

    class Meta:
        db_table = 'Postulacion'
        verbose_name = 'Postulación'
        verbose_name_plural = 'Postulaciones'
        constraints = [
            models.UniqueConstraint(
                fields=['estudiante', 'oferta'],
                name='unique_estudiante_oferta',
            ),
        ]

    def __str__(self):
        return f'{self.estudiante} - {self.oferta}'