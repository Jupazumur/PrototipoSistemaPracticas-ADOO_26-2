from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def hash_default_passwords(apps, schema_editor):
    Administrador = apps.get_model('sistema_practicas', 'Administrador')
    Estudiante = apps.get_model('sistema_practicas', 'Estudiante')
    for modelo in (Administrador, Estudiante):
        for obj in modelo.objects.filter(password='cambiar'):
            obj.password = make_password('cambiar')
            obj.save(update_fields=['password'])


class Migration(migrations.Migration):

    dependencies = [
        ('sistema_practicas', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='administrador',
            name='password',
            field=models.CharField(default='cambiar', max_length=128),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='estudiante',
            name='password',
            field=models.CharField(default='cambiar', max_length=128),
            preserve_default=False,
        ),
        migrations.RunPython(hash_default_passwords, migrations.RunPython.noop),
    ]
