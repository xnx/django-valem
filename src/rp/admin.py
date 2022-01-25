from django.contrib import admin
from .models import Species, RP, State

# Register your models here.
admin.site.register(Species)
admin.site.register(RP)
admin.site.register(State)
