from django.db import migrations, models
import pgvector.django

class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_attendance_department_employee_leave_salary_and_more'),
    ]

    operations = [
        pgvector.django.VectorExtension(),
        migrations.CreateModel(
            name='MetadataVector',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('metadata_key', models.CharField(max_length=255)),
                ('embedding', pgvector.django.VectorField(dimensions=384)),
            ],
        ),
    ]
