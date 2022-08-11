from django.contrib import admin
from .models import Card, Collection, CardEntry, Profile

class CardAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name', 'short_description', 'long_description']


class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name']
    list_display_links = ['name']
    search_fields = ['name', 'description']
    filter_horizontal = ['cards']


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['get_username', 'get_email']
    search_fields = ['user__username', 'user__email']
    filter_horizontal = ['cards', 'collections']
    
    @admin.display(ordering='user__username', description='Username')
    def get_username(self, obj):
        return obj.user.username

    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email


class CardEntryAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_username']
    search_fields = ['user__username']

    @admin.display(ordering='id', description='Username')
    def get_username(self, obj):
        return obj.user.username


admin.site.register(Card, CardAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(CardEntry, CardEntryAdmin)
