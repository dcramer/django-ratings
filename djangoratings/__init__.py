from models import Vote, Score
from django.db.models import IntegerField, PositiveIntegerField

import forms

from django.contrib.contenttypes.models import ContentType

from django.conf import settings

if 'django.contrib.contenttypes' not in settings.INSTALLED_APPS:
    raise ImportError("djangoratings requires django.contrib.contenttypes in your INSTALLED_APPS")

__all__ = ('Rating', 'RatingField', 'AnonymousRatingField')

# The following code is based on the FuzzyDate snippet
# http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

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
        
    def add(self, score, user, ip_address):
        if score not in dict(self.field.choices).keys():
            raise ValueError("%s is not a valid choice for %s" % (score, self.field.name))
        is_anonymous = (user is None or not user.is_authenticated())
        if is_anonymous and not self.field.allow_anonymous:
            raise TypeError("user must be a user, not '%r'" % (self.field.name, user))
        
        defaults = dict(
            score = score,
            ip_address = ip_address,
            user = is_anonymous and None or user,
        )
        
        if is_anonymous:
            rating, created = Vote.objects.get_or_create(
                content_type    = self.get_content_type(),
                object_id       = self.instance.id,
                user            = None,
                ip_addresss     = ip_address,
                defaults        = defaults,
            )
        else:
            rating, created = Vote.objects.get_or_create(
                content_type    = self.get_content_type(),
                object_id       = self.instance.id,
                user            = user,
                defaults        = defaults,
            )
        has_changed = False
        if not created:
            if self.field.can_change_vote:
                has_changed = True
                self.score -= rating.score
                rating.score = score
                rating.save()
            else:
                return
        else:
            has_changed = True
            self.votes += 1
        if has_changed:
            self.score += rating.score
            self.instance.save()
            #setattr(self.instance, self.field.name, Rating(score=self.score, votes=self.votes))
        
            defaults = dict(
                score   = self.score,
                votes   = self.votes,
            )
        
            score, created = Score.objects.get_or_create(
                content_type    = self.get_content_type(),
                object_id       = self.instance.id,
                defaults        = defaults,
            )
            
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
            self.content_type = ContentType.objects.get_for_model(self.instance,)
        return self.content_type

class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
        self._rating_manager = None

    def __get__(self, instance, type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
        if self._rating_manager is None:
            self._rating_manager = RatingManager(instance, self.field)
        return self._rating_manager

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
    allow_anonymous = False
    
    def __init__(self, *args, **kwargs):
        if 'choices' not in kwargs:
            raise TypeError("%s missing required attribute 'choices'" % (self.__class__.__name__,))
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        kwargs['editable'] = False
        kwargs['default'] = 0
        kwargs['blank'] = True
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name):
        # Votes tally field
        votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (name,), votes_field)

        # Score sum field
        #super(RatingField, self).contribute_to_class(cls, name)
        self.name = name

        score_field = IntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (name,), score_field)

        setattr(cls, name, RatingCreator(self))

    def get_db_prep_save(self, value):
        # XXX: what happens here?
        pass

    def get_db_prep_lookup(self, lookup_type, value):
        # TODO: hack in support for __score and __votes
        raise NotImplementedError(self.get_db_prep_lookup)
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