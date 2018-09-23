from django.contrib.auth.models import User
from django.db import models


from .serverclient import *

# Create your models here.


class BrowserClient(models.Model):

    cid = models.IntegerField()
    user = models.OneToOneField(User, null=True, on_delete=models.CASCADE)
    csv_file = models.FileField(default='')

