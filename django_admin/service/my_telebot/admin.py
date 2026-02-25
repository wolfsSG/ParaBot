from django.contrib import admin
from my_telebot.models import User, Cities, Spots

# Register your models here.

class SpotsAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'flight_type', 'wind_min', 'wind_max')
    list_filter = ('city', 'flight_type')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Основная информация', {
            'fields': ('city', 'name', 'description', 'flight_type')
        }),
        ('Координаты и ссылки', {
            'fields': ('lat', 'lon', 'url_map', 'url_forecast')
        }),
        ('Параметры ветра', {
            'fields': ('wind_degree_l', 'wind_degree_r', 'wind_min', 'wind_max')
        }),
    )


class CitiesAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_spots')


admin.site.register(User)
admin.site.register(Cities, CitiesAdmin)
admin.site.register(Spots, SpotsAdmin)

admin.site.site_title = 'bot'
admin.site.site_header = 'bot'