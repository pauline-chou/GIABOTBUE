# Generated by Django 4.1.13 on 2024-06-02 04:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0008_user_info_created_at_user_info_updated_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserPlaceMapping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_id', models.CharField(max_length=50)),
                ('place_id', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('user_id', 'place_id')},
            },
        ),
    ]
