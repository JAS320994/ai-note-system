from django.db import models

from django.db import models



class Note(models.Model):


    text=models.TextField(
        blank=True
    )


    audio=models.FileField(
        upload_to="audio/",
        blank=True
    )


    image=models.FileField(
        upload_to="image/",
        blank=True
    )


    result=models.TextField(
        blank=True
    )


    create_time=models.DateTimeField(
        auto_now_add=True
    )# Create your models here.
