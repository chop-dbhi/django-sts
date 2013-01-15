from django.contrib import admin
from .models import System, State, Event, Transition


admin.site.register(System)
admin.site.register(State)
admin.site.register(Event)
admin.site.register(Transition)
