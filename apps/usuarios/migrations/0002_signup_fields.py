from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='nome',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='usuario',
            name='sobrenome',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='usuario',
            name='data_nascimento',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='email_verificado',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='codigo_verificacao',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='codigo_expira_em',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='usuario',
            name='codigo_usado',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='usuario',
            name='criado_em',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
