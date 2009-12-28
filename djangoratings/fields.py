from django.db.models import IntegerField, PositiveIntegerField
from django.conf import settings

import forms
import itertools

from models import Vote, Score
from default_settings import RATINGS_VOTES_PER_IP
from exceptions import *

if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImportError("djangoratings requires django.contrib.contenttypes in your INSTALLED_APPS")

from django.contrib.contenttypes.models import ContentType

__all__ = ('Rating', 'RatingField', 'AnonymousRatingField')

try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5
    
def md5_hexdigest(value):
    return md5(value).hexdigest()

class Rating(object):
    def __init__(self, score, votes):
        self.score = score
        self.votes = votes

class RatingManager(object):
    def __init__(self, instance, field):
        self.content_type = None
        self.instance = instance
        self.field = field
        
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
    
    def get_percent(self):
        """get_percent()
        
        Returns the weighted percentage of the score from min-max values"""
        if not (self.votes and self.score):
            return 0
        return 100 * (self.get_rating() / self.field.range)
    
    def get_real_percent(self):
        """get_real_percent()
        
        Returns the unmodified percentage of the score based on a 0-point scale."""
        if not (self.votes and self.score):
            return 0
        return 100 * (self.get_real_rating() / self.field.range)
    
    def get_ratings(self):
        """get_ratings()
        
        Returns a Vote QuerySet for this rating field."""
        return Vote.objects.filter(content_type=self.get_content_type(), object_id=self.instance.pk, key=self.field.key)
        
    def get_rating(self):
        """get_rating()
        
        Returns the weighted average rating."""
        if not (self.votes and self.score):
            return 0
        return float(self.score)/(self.votes+self.field.weight)
    
    def get_opinion_percent(self):
        """get_opinion_percent()
        
        Returns a neutral-based percentage."""
        return (self.get_percent()+100)/2

    def get_real_rating(self):
        """get_rating()
        
        Returns the unmodified average rating."""
        if not (self.votes and self.score):
            return 0
        return float(self.score)/self.votes
    
    def get_rating_for_user(self, user, ip_address):
        """get_rating_for_user(user, ip_address)
        
        Returns the rating for a user or anonymous IP."""
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
        )

        if not (user and user.is_authenticated()):
            kwargs['user__isnull'] = True
            kwargs['ip_address'] = ip_address
        else:
            kwargs['user'] = user
        try:
            rating = Vote.objects.get(**kwargs)
            return rating.score
        except Vote.DoesNotExist:
            pass
        return
        
    def add(self, score, user, ip_address, commit=True):
        """add(score, user, ip_address)
        
        Used to add a rating to an object."""
        try:
            score = int(score)
        except (ValueError, TypeError):
            raise InvalidRating("%s is not a valid choice for %s" % (score, self.field.name))

        if score < 1 or score > self.field.range:
            raise InvalidRating("%s is not a valid choice for %s" % (score, self.field.name))

        is_anonymous = (user is None or not user.is_authenticated())
        if is_anonymous and not self.field.allow_anonymous:
            raise AuthRequired("user must be a user, not '%r'" % (user,))
        
        if is_anonymous:
            user = None

        defaults = dict(
            score = score,
            ip_address = ip_address,
        )
        
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
            user            = user,
        )
        if not user:
            kwargs['ip_address'] = ip_address

        try:
            rating, created = Vote.objects.get(**kwargs), False
        except Vote.DoesNotExist:
            if getattr(settings, 'RATINGS_VOTES_PER_IP', RATINGS_VOTES_PER_IP):
                num_votes = Vote.objects.filter(
                    content_type=kwargs['content_type'],
                    object_id=kwargs['object_id'],
                    key=kwargs['key'],
                    ip_address=ip_address,
                ).count()
                if num_votes >= getattr(settings, 'RATINGS_VOTES_PER_IP', RATINGS_VOTES_PER_IP):
                    raise IPLimitReached()
            kwargs.update(defaults)
            rating, created = Vote.objects.create(**kwargs), True
            
        has_changed = False
        if not created:
            if self.field.can_change_vote:
                has_changed = True
                self.score -= rating.score
                rating.score = score
                rating.save()
            else:
                raise CannotChangeVote()
        else:
            has_changed = True
            self.votes += 1
        if has_changed:
            self.score += rating.score
            if commit:
                self.instance.save()
            #setattr(self.instance, self.field.name, Rating(score=self.score, votes=self.votes))
            
            defaults = dict(
                score   = self.score,
                votes   = self.votes,
            )
            
            kwargs = dict(
                content_type    = self.get_content_type(),
                object_id       = self.instance.pk,
                key             = self.field.key,
            )
            
            try:
                score, created = Score.objects.get(**kwargs), False
            except Score.DoesNotExist:
                kwargs.update(defaults)
                score, created = Score.objects.create(**kwargs), True
            
            if not created:
                score.__dict__.update(defaults)
                score.save()

    def _get_votes(self, default=None):
        return getattr(self.instance, self.votes_field_name, default)
    
    def _set_votes(self, value):
        return setattr(self.instance, self.votes_field_name, value)
        
    votes = property(_get_votes, _set_votes)

    def _get_score(self, default=None):
        return getattr(self.instance, self.score_field_name, default)
    
    def _set_score(self, value):
        return setattr(self.instance, self.score_field_name, value)
        
    score = property(_get_score, _set_score)

    def get_content_type(self):
        if self.content_type is None:
            self.content_type = ContentType.objects.get_for_model(self.instance)
        return self.content_type
    
    def _update(self, commit=False):
        """Forces an update of this rating (useful for when Vote objects are removed)."""
        votes = Vote.objects.filter(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
        )
        obj_score = sum([v.score for v in votes])
        obj_votes = len(votes)

        score, created = Score.objects.get_or_create(
            content_type    = self.get_content_type(),
            object_id       = self.instance.pk,
            key             = self.field.key,
            defaults        = dict(
                score       = obj_score,
                votes       = obj_votes,
            )
        )
        if not created:
            score.score = obj_score
            score.votes = obj_votes
            score.save()
        self.score = obj_score
        self.votes = obj_votes
        if commit:
            self.instance.save()

class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
        # we need a unique key incase there are multiple ratings on a model
        self._rating_manager = None

    def __get__(self, instance, type=None):
        if instance is None:
            return self.field
            #raise AttributeError('Can only be accessed via an instance.')
        return RatingManager(instance, self.field)

    def __set__(self, instance, value):
        if isinstance(value, Rating):
            setattr(instance, self.votes_field_name, value.votes)
            setattr(instance, self.score_field_name, value.score)
        else:
            raise TypeError("%s value must be a Rating instance, not '%r'" % (self.field.name, value))

class RatingField(IntegerField):
    """
    A rating field contributes two columns to the model instead of the standard single column.
    """
    def __init__(self, *args, **kwargs):
        if 'choices' in kwargs:
            raise TypeError("%s invalid attribute 'choices'" % (self.__class__.__name__,))
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        self.weight = kwargs.pop('weight', 0)
        self.range = kwargs.pop('range', 2)
        self.allow_anonymous = kwargs.pop('allow_anonymous', False)
        kwargs['editable'] = False
        kwargs['default'] = 0
        kwargs['blank'] = True
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name):
        self.name = name

        # Votes tally field
        self.votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (self.name,), self.votes_field)

        # Score sum field
        self.score_field = IntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (self.name,), self.score_field)

        self.key = md5_hexdigest(self.name)

        field = RatingCreator(self)

        if not hasattr(cls, '_djangoratings'):
            cls._djangoratings = []
        cls._djangoratings.append(self)

        setattr(cls, name, field)

    def get_db_prep_save(self, value):
        # XXX: what happens here?
        pass

    def get_db_prep_lookup(self, lookup_type, value):
        # TODO: hack in support for __score and __votes
        # TODO: order_by on this field should use the weighted algorithm
        raise NotImplementedError(self.get_db_prep_lookup)
        # if lookup_type in ('score', 'votes'):
        #     lookup_type = 
        #     return self.score_field.get_db_prep_lookup()
        if lookup_type == 'exact':
            return [self.get_db_prep_save(value)]
        elif lookup_type == 'in':
            return [self.get_db_prep_save(v) for v in value]
        else:
            return super(RatingField, self).get_db_prep_lookup(lookup_type, value)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.RatingField}
        defaults.update(kwargs)
        return super(RatingField, self).formfield(**defaults)

    # TODO: flatten_data method


class AnonymousRatingField(RatingField):
    def __init__(self, *args, **kwargs):
        kwargs['allow_anonymous'] = True
        super(AnonymousRatingField, self).__init__(*args, **kwargs)
