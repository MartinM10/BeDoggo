# Generated by Django 5.1.5 on 2025-01-31 11:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('beDoggo', '0015_alter_user_managers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='medicalrecord',
            name='attachments',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='medicalrecord',
            name='images',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='pet',
            name='image',
            field=models.URLField(blank=True, null=True),
        ),
    ]
