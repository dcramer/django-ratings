from django.db import models
from django.contrib.contenttypes.models import ContentType

from django.conf import settings

from models import Vote, Score

import forms

if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImportError("djangoratings requires django.contrib.contenttypes in your INSTALLED_APPS")

# The following code is based on the FuzzyDate snippet
# http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

class Rating(object):
    def __init__(self, score, votes):
        self.score = score
        self.votes = votes

class RatingManager(object):
    def __init__(self, instance, field, score, votes):
        self.score = score
        self.votes = votes
        self.instance = instance
        self.field = field
        
    def add(self, score, user, ip_address):
        if score not in self.field.choices:
            raise ValueError("%s is not a valid choice for %s" % (score, self.field.name))
        is_anonymous = (request.user is None or not request.user.is_authenticated())
        if is_anonymous and not self.field.allow_anonymous:
            raise TypeError("%s must be a user, not '%r'" % (self.field.name, user))
        
        defaults = dict(
            score = score,
            ip_address = ip_address,
            user = is_anonymous and None or user,
        )
        
        if is_anonymous:
            rating, created = Vote.objects.get_or_create(
                content_type    = self.field.get_content_type(),
                object_id       = self.instance.id,
                ip_addresss     = ip_address,
                defaults        = defaults,
            )
        else:
            rating, created = Vote.objects.get_or_create(
                content_type    = self.field.get_content_type(),
                object_id       = self.instance.id,
                user            = user,
                defaults        = defaults,
            )
        if not created and self.field.can_change_vote:
            rating.score = score
            rating.save()
            

class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
        self.content_type = None
        self._rating_manager = None

    def __get__(self, instance, type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        if self._rating_manager is None:
            self._rating_manager = RatingManager(instance, field, score=getattr(instance, self.score_field_name), votes=getattr(instance, self.votes_field_name))
        return self._rating_manager

    def __set__(self, instance, value):
        if isinstance(value, Rating):
            setattr(instance, self.votes_field_name, value.votes)
            setattr(instance, self.score_field_name, value.score)
        else:
            raise TypeError("%s value must be a Rating instance, not '%r'" % (self.field.name, value))

    def get_content_type(self):
        if self.content_type is None:
            self.content_type = ContentType.objects.get_for_model(self.instance,)
        return self.content_type

class RatingField(models.IntegerField):
    """
    A rating field contributes two columns to the model instead of the standard single column.
    """
    allow_anonymous = False
    
    def __init__(self, **kwargs):
        if 'choices' not in kwargs:
            raise TypeError("%s missing required attribute 'choices'" % (self.__class__.__name__,))
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        super(RatingField, self).__init__(verbose_name, name, **kwargs)
    
    def contribute_to_class(self, cls, name):
        # Votes tally field
        votes_field = models.PositiveIntegerField(
            editable=False, default=0)
        votes_field.creation_counter = self.creation_counter
        cls.add_to_class"%_votes" % (name,), votes_field)

        # Score sum field
        score_field = models.IntegerField(
            editable=False, default=0)
        score_field.creation_counter = self.creation_counter
        cls.add_to_class("%_score" % (name,), score_field)

        setattr(cls, self.name, RatingCreator(self))

    def get_db_prep_save(self, value):
        # XXX: what happens here?
        pass

    def get_db_prep_lookup(self, lookup_type, value):
        # TODO: hack in support for __score and __votes
        raise NotImplementedError, self.get_db_prep_lookup
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
    allow_anonymous = True