from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0045_school_google_verification_code'),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan sana")),
                ('is_active', models.BooleanField(default=True, verbose_name='Faoligi')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
                ('slug', models.SlugField(max_length=100, verbose_name='Slug')),
                ('soato', models.CharField(blank=True, max_length=20, null=True, verbose_name='SOATO kodi')),
            ],
            options={
                'verbose_name': 'Viloyat ',
                'verbose_name_plural': 'Viloyatlar',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='District',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratilgan sana')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name="O'zgartirilgan sana")),
                ('is_active', models.BooleanField(default=True, verbose_name='Faoligi')),
                ('name', models.CharField(max_length=100, verbose_name='Nomi')),
                ('slug', models.SlugField(max_length=100, verbose_name='Slug')),
                ('soato', models.CharField(blank=True, max_length=20, null=True, verbose_name='SOATO kodi')),
                ('region', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='districts',
                    to='main.region',
                    verbose_name='Viloyat',
                )),
            ],
            options={
                'verbose_name': 'Tuman ',
                'verbose_name_plural': 'Tumanlar',
                'ordering': ['region__name', 'name'],
            },
        ),
        migrations.AddConstraint(
            model_name='region',
            constraint=models.UniqueConstraint(fields=('slug',), name='unique_region_slug'),
        ),
        migrations.AddConstraint(
            model_name='district',
            constraint=models.UniqueConstraint(fields=('region', 'slug'), name='unique_district_region_slug'),
        ),
        migrations.AddField(
            model_name='school',
            name='region',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='schools',
                to='main.region',
                verbose_name='Viloyat',
            ),
        ),
        migrations.AddField(
            model_name='school',
            name='district',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='schools',
                to='main.district',
                verbose_name='Tuman',
            ),
        ),
        migrations.AddField(
            model_name='school',
            name='is_online',
            field=models.BooleanField(default=True, verbose_name='Sayt javob berayapti'),
        ),
        migrations.AddField(
            model_name='school',
            name='last_checked_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi tekshirilgan vaqt'),
        ),
        migrations.AddField(
            model_name='school',
            name='last_online_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Oxirgi javob bergan vaqt'),
        ),
    ]
