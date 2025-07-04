# Generated by Django 5.2 on 2025-05-31 06:00

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('attendance', '0001_initial'),
        ('institution', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='attendance',
            name='created_by',
            field=models.ForeignKey(limit_choices_to={'is_teacher': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_attendances', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='attendance',
            name='institution',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='institution.institutioninfo'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='section',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='institution.section'),
        ),
        migrations.AddField(
            model_name='attendance',
            name='student',
            field=models.ForeignKey(limit_choices_to={'is_student': True}, on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='attendance',
            name='subject',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attendances', to='institution.subject'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['institution', 'date'], name='attendance__institu_d4fd32_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['student', 'date'], name='attendance__student_76a8d7_idx'),
        ),
        migrations.AddIndex(
            model_name='attendance',
            index=models.Index(fields=['section', 'subject', 'date'], name='attendance__section_e091e9_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='attendance',
            unique_together={('student', 'section', 'subject', 'date')},
        ),
    ]
