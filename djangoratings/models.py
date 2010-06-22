from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User

import datetime

from managers import VoteManager

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

# Thanks ruby guys: http://www.trampolinesystems.com/calculating-pearsons-corellation-coefficient-in-sql/uncategorized

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
    mean            = models.FloatField(default=0.0)
    stddev          = models.FloatField(default=0.0)
    
    content_object  = generic.GenericForeignKey()

    class Meta:
        unique_together = (('content_type', 'object_id', 'key'),)

    def __unicode__(self):
        return "%s scored %s with %s votes" % (self.content_object, self.score, self.votes)

"""
insert into djangoratings_scorecorrelation (
    content_type_id,
    object_id,
    to_content_type_id,
    to_object_id,
    rank
  )
  select sf.content_type_id,
         sf.object_id,
         sf.to_content_type_id,
         sf.to_object_id,
         (sf.sum / (select count(1) from auth_user where is_active = 1)
          - stats1.mean * stats2.mean
         ) -- covariance
         / (stats1.stddev * stats2.stddev)
  from (
    select r1.content_type_id content_type_id,
           r1.object_id object_id,
           r2.content_type_id to_content_type_id,
           r2.object_id to_object_id,
           sum(r1.score * r2.score) sum
    from djangoratings_vote r1
    join djangoratings_vote r2
    on r1.user_id = r2.user_id
        and r1.user_id is not null
    group by content_type_id, object_id, to_content_type_id, to_object_id
  ) sf
  join djangoratings_score stats1
    on stats1.content_type_id = sf.content_type_id
        and stats1.object_id = sf.object_id
  join djangoratings_score stats2
      on stats2.content_type_id = sf.to_content_type_id
          and stats2.object_id = sf.to_object_id;
 """
class ScoreCorrelation(models.Model):
    content_type    = models.ForeignKey(ContentType, related_name="djr_sc_1")
    object_id       = models.PositiveIntegerField()
    to_content_type = models.ForeignKey(ContentType, related_name="djr_sc_2")
    to_object_id    = models.PositiveIntegerField()
    rank            = models.FloatField()
    
    class Meta:
        unique_together = (('content_type', 'object_id', 'to_content_type', 'to_object_id'),)
    
    