from django.db import migrations, models
import django.db.models.deletion


def forwards(apps, schema_editor):
    ServiceType = apps.get_model('accounts', 'ServiceType')
    TechnicianProfile = apps.get_model('accounts', 'TechnicianProfile')

    plumbing, _ = ServiceType.objects.get_or_create(name='سباكة', slug='plumbing')
    electrical, _ = ServiceType.objects.get_or_create(name='كهرباء', slug='electrical')
    carpentry, _ = ServiceType.objects.get_or_create(name='نجارة', slug='carpentry')

    mapping = {
        'سباك': plumbing.id, 'سباكة': plumbing.id, 'plumbing': plumbing.id,
        'كهرباء': electrical.id, 'كهربائي': electrical.id, 'electrical': electrical.id,
        'نجار': carpentry.id, 'نجارة': carpentry.id, 'carpentry': carpentry.id,
    }

    for profile in TechnicianProfile.objects.all():
        old = str(profile.service_type) if profile.service_type is not None else ''
        try:
            new_id = int(old)
        except (ValueError, TypeError):
            new_id = mapping.get(old, plumbing.id)
        profile.service_type = str(new_id)
        profile.save(update_fields=['service_type'])


def backwards(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50, unique=True)),
                ('slug', models.SlugField(unique=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={'ordering': ['name']},
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='technicianprofile',
            name='service_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='technicians',
                to='accounts.servicetype',
            ),
        ),
    ]