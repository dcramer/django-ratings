from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class Vote(models.Model):
    content_type    = models.ForeignKey(ContentType)
    object_id       = models.PositiveIntegerField()
    score           = models.IntegerField()
    user            = models.ForeignKey(User, blank=True, null=True)
    ip_address      = models.IPAddressField()

    class Meta:
        unique_together = (('content_type', 'object_id', 'user', 'ip_address'))

class Score(models.Model):
    content_type    = models.ForeignKey(ContentType)
    object_id       = models.PositiveIntegerField()
    score           = models.IntegerField()
    votes           = models.PositiveIntegerField()
    
    class Meta:
        unique_together = (('content_type', 'object_id'),)