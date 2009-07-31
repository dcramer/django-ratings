from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

class Vote(models.Model):
    content_type    = models.ForeignKey(ContentType, related_name="votes")
    object_id       = models.PositiveIntegerField()
    key             = models.CharField(max_length=32)
    score           = models.IntegerField()
    user            = models.ForeignKey(User, blank=True, null=True, related_name="votes")
    ip_address      = models.IPAddressField()

    class Meta:
        unique_together = (('content_type', 'object_id', 'key', 'user', 'ip_address'))

    def partial_ip_address(self):
        ip = self.ip_address.split('.')
        ip[-1] = 'xxx'
        return '.'.join(ip)
    partial_ip_address = property(partial_ip_address)

class Score(models.Model):
    content_type    = models.ForeignKey(ContentType)
    object_id       = models.PositiveIntegerField()
    key             = models.CharField(max_length=32)
    score           = models.IntegerField()
    votes           = models.PositiveIntegerField()
    
    class Meta:
        unique_together = (('content_type', 'object_id', 'key'),)
