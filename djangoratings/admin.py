from django.contrib import admin
from models import Vote, Score

class VoteAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'user', 'ip_address', 'cookie', 'score', 'date_changed')
    list_filter = ('score', 'content_type', 'date_changed')
    search_fields = ('ip_address',)
    raw_id_fields = ('user',)

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'score', 'votes')
    list_filter = ('content_type',)

admin.site.register(Vote, VoteAdmin)
admin.site.register(Score, ScoreAdmin)
