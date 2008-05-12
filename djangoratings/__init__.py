from django.db import models

import forms

# The following code is based on the FuzzyDate snippet
# http://blog.elsdoerfer.name/2008/01/08/fuzzydates-or-one-django-model-field-multiple-database-columns/

class Rating(object):
    def __init__(self, score, votes):
        self.score = score
        self.votes = votes
    
    def add(self, **kwargs):
        # TODO
        pass

class RatingCreator(object):
    def __init__(self, field):
        self.field = field
        self.votes_field_name = "%s_votes" % (self.field.name,)
        self.score_field_name = "%s_score" % (self.field.name,)

    def __get__(self, obj, type=None):
        if obj is None:
            raise AttributeError('Can only be accessed via an instance.')

        score = obj.__dict__[self.score_field_name]
        if score is None: return None
        else:
            return Rating(score=score, votes=getattr(obj, self.votes_field_name))

    def __set__(self, obj, value):
        if isinstance(value, Rating):
            setattr(obj, self.votes_field_name, value.votes)
            setattr(obj, self.score_field_name, value.score)
        else:
            raise TypeError("%s value must be a Rating instance, not '%r'" % (self.field.name, value))

class RatingField(models.IntegerField):
    """
    A rating field contributes two columns to the model instead of the standard single column.
    """
    allow_anonymous = False
    
    def __init__(self, **kwargs):
        if 'choices' not in kwargs:
            raise TypeError("%s missing required attribute 'choices'" % (self.__class__.__name__,))
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