# Generated by Django 5.2.3 on 2025-06-27 07:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0007_alter_recruiterprofile_industry'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SeekerFeedback',
        ),
    ]
