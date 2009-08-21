from django.contrib import admin
from models import Vote, Score

class VoteAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'user', 'ip_address', 'score')
    list_filter = ('score', 'content_type')
    search_fields = ('ip_address',)

class ScoreAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'score', 'votes')
    list_filter = ('score', 'content_type')

admin.site.register(Vote, VoteAdmin)
admin.site.register(Score, ScoreAdmin)
