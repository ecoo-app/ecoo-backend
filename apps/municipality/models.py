from django.db import models

class Municipality(models.Model):
    name = models.CharField(max_length=32)

    def __str__(self):
        return self.name