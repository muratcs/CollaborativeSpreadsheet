# Generated by Django 2.0 on 2017-12-31 11:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spreadsheet', '0002_auto_20171231_1343'),
    ]

    operations = [
        migrations.AlterField(
            model_name='browserclient',
            name='cid',
            field=models.IntegerField(),
        ),
    ]