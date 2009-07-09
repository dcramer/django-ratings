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
        # hackish
        return float(self.score)/(self.votes*self.field.choices[-1][0])*100
    
    def get_ratings(self):
        """Returns a Vote QuerySet for this rating field."""
        return Vote.objects.filter(content_type=self.get_content_type(), object_idself.instance.id, key=self.field.key)
    
    def get_rating(self, user, ip_address):
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.id,
            key             = self.field.key,
        )

        if user and not user.is_authenticated():
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
        
    def add(self, score, user, ip_address):
        """Used to add a rating to an object."""
        if score not in dict(self.field.choices).keys():
            raise ValueError("%s is not a valid choice for %s" % (score, self.field.name))
        is_anonymous = (user is None or not user.is_authenticated())
        if is_anonymous and not self.field.allow_anonymous:
            raise TypeError("user must be a user, not '%r'" % (user,))
        
        if is_anonymous:
            user = None
        
        defaults = dict(
            score = score,
            ip_address = ip_address,
        )
        
        kwargs = dict(
            content_type    = self.get_content_type(),
            object_id       = self.instance.id,
            key             = self.field.key,
            user            = user,
        )
        if not user:
            kwargs['ip_address'] = ip_address

        try:
            rating, created = Vote.objects.get(**kwargs), False
        except Vote.DoesNotExist:
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
            
            kwargs = dict(
                content_type    = self.get_content_type(),
                object_id       = self.instance.id,
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
            self.content_type = ContentType.objects.get_for_model(self.instance,)
        return self.content_type

class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)
        # we need a unique key incase there are multiple ratings on a model
        self._rating_manager = None

    def __get__(self, instance, type=None):
        if instance is None:
            raise AttributeError('Can only be accessed via an instance.')
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
        if 'choices' not in kwargs:
            raise TypeError("%s missing required attribute 'choices'" % (self.__class__.__name__,))
        self.can_change_vote = kwargs.pop('can_change_vote', False)
        self.allow_anonymous = kwargs.pop('allow_anonymous', False)
        kwargs['editable'] = False
        kwargs['default'] = 0
        kwargs['blank'] = True
        super(RatingField, self).__init__(*args, **kwargs)
    
    def contribute_to_class(self, cls, name):
        self.name = name

        # Votes tally field
        votes_field = PositiveIntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_votes" % (self.name,), votes_field)

        # Score sum field
        score_field = IntegerField(
            editable=False, default=0, blank=True)
        cls.add_to_class("%s_score" % (self.name,), score_field)


        self.key = md5_hexdigest(self.name)

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