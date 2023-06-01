from django.contrib import admin
from . import models
# Register your models here.

admin.site.register(models.ParkingManagers)
admin.site.register(models.User)
admin.site.register(models.ParkingsLists)
admin.site.register(models.Logins)
admin.site.register(models.Exits)
admin.site.register(models.Pays)
admin.site.register(models.Requests)
