# Generated by Django 5.2.3 on 2025-06-20 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_seekerfeedback'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobseekerprofile',
            name='profile_updated',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='recruiterprofile',
            name='profile_updated',
            field=models.BooleanField(default=False),
        ),
    ]
