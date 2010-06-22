from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

import datetime

from managers import VoteManager, SimilarUserManager

class Vote(models.Model):
    content_type    = models.ForeignKey(ContentType, related_name="votes")
    object_id       = models.PositiveIntegerField()
    key             = models.CharField(max_length=32)
    score           = models.IntegerField()
    user            = models.ForeignKey(User, blank=True, null=True, related_name="votes")
    ip_address      = models.IPAddressField()
    date_added      = models.DateTimeField(default=datetime.datetime.now, editable=False)
    date_changed    = models.DateTimeField(default=datetime.datetime.now, editable=False)

    objects         = VoteManager()

    content_object  = generic.GenericForeignKey()

    class Meta:
        unique_together = (('content_type', 'object_id', 'key', 'user', 'ip_address'))

    def __unicode__(self):
        return "%s voted %s on %s" % (self.user_display, self.score, self.content_object)

    def save(self, *args, **kwargs):
        self.date_changed = datetime.datetime.now()
        super(Vote, self).save(*args, **kwargs)

    def user_display(self):
        if self.user:
            return "%s (%s)" % (self.user.username, self.ip_address)
        return self.ip_address
    user_display = property(user_display)

    def partial_ip_address(self):
        ip = self.ip_address.split('.')
        ip[-1] = 'xxx'
        return '.'.join(ip)
    partial_ip_address = property(partial_ip_address)

"""
insert into djangoratings_score (content_type_id, object_id, mean)
  select content_type_id, object_id, sum(score) / (select count(distinct user_id) from djangoratings_vote) mean
  from djangoratings_vote
  group by content_type_id, object_id
  on duplicate key update mean = values(mean);
 
update djangoratings_score
  set stddev = (
    select sqrt(
            sum(score * score) / (select count(1) from auth_user where is_active = 1)
            - mean * mean
           ) stddev
    from djangoratings_vote
    where djangoratings_vote.object_id = djangoratings_score.object_id
    and djangoratings_vote.content_type_id = djangoratings_score.content_type_id
    group by djangoratings_vote.content_type_id, djangoratings_vote.object_id);
"""
class Score(models.Model):
    content_type    = models.ForeignKey(ContentType)
    object_id       = models.PositiveIntegerField()
    key             = models.CharField(max_length=32)
    score           = models.IntegerField()
    votes           = models.PositiveIntegerField()
    
    content_object  = generic.GenericForeignKey()

    class Meta:
        unique_together = (('content_type', 'object_id', 'key'),)

    def __unicode__(self):
        return "%s scored %s with %s votes" % (self.content_object, self.score, self.votes)

"""
insert into djangoratings_similaruser
  (to_user_id, from_user_id, agrees, disagrees)
  select v1.user_id, v2.user_id,
         sum(if(v2.score != v1.score, 1, 0)) as agrees,
         sum(if(v2.score = v1.score, 1, 0)) as disagrees
    from djangoratings_vote as v1
      inner join djangoratings_vote as v2
        on v1.user_id != v2.user_id
        and v1.object_id = v2.object_id
        and v1.content_type_id = v2.content_type_id
    group by v1.user_id, v2.user_id
    having agrees / disagrees > 3
  on duplicate key update agrees = values(agrees), disagrees = values(disagrees);
"""
class SimilarUser(models.Model):
    from_user       = models.ForeignKey(User, related_name="similar_users")
    to_user         = models.ForeignKey(User, related_name="similar_users_from")
    agrees          = models.PositiveIntegerField(default=0)
    disagrees       = models.PositiveIntegerField(default=0)
    
    objects         = SimilarUserManager()
    
    class Meta:
        unique_together = (('from_user', 'to_user'),)