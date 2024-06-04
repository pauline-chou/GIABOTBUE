# Generated by Django 4.1.13 on 2024-06-02 06:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testapp', '0009_userplacemapping'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userplacemapping',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='userplacemapping',
            name='place_1',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userplacemapping',
            name='place_2',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userplacemapping',
            name='place_3',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userplacemapping',
            name='place_4',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='userplacemapping',
            name='place_5',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
        migrations.RemoveField(
            model_name='userplacemapping',
            name='place_id',
        ),
    ]