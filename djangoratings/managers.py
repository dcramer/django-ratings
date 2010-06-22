from django.db.models import Manager
from django.db.models.query import QuerySet

from django.contrib.contenttypes.models import ContentType
import itertools

class VoteQuerySet(QuerySet):
    def delete(self, *args, **kwargs):
        """Handles updating the related `votes` and `score` fields attached to the model."""
        # XXX: circular import
        from fields import RatingField

        qs = self.distinct().values_list('content_type', 'object_id').order_by('content_type')
    
        to_update = []
        for content_type, objects in itertools.groupby(qs, key=lambda x: x[0]):
            model_class = ContentType.objects.get(pk=content_type).model_class()
            if model_class:
                to_update.extend(list(model_class.objects.filter(pk__in=list(objects)[0])))
        
        retval = super(VoteQuerySet, self).delete(*args, **kwargs)
        
        # TODO: this could be improved
        for obj in to_update:
            for field in getattr(obj, '_djangoratings', []):
                getattr(obj, field.name)._update(commit=False)
            obj.save()
        
        return retval
        
class VoteManager(Manager):
    def get_query_set(self):
        return VoteQuerySet(self.model)

    def get_for_user_in_bulk(self, objects, user):
        objects = list(objects)
        if len(objects) > 0:
            ctype = ContentType.objects.get_for_model(objects[0])
            votes = list(self.filter(content_type__pk=ctype.id,
                                     object_id__in=[obj._get_pk_val() \
                                                    for obj in objects],
                                     user__pk=user.id))
            vote_dict = dict([(vote.object_id, vote) for vote in votes])
        else:
            vote_dict = {}
        return vote_dict

class SimilarUserManager(Manager):
    def get_recommendations(self, user, model_class, offset=0, limit=10):
        content_type = ContentType.objects.get_for_model(model_class)

        votes = content_type.votes.extra(
            where = ['user_id IN (select from_user_id from %s where to_user_id = %%d)' % (self.model._meta.db_table,)],
            params = [user.id],
        ).filter(score__gte=4).distinct().values_list('object_id', flat=True)[offset:limit]

        # Thank you Django, for not working.. ever
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute(str(votes.query))
        object_ids = list(r[0] for r in cursor.fetchall())

        objects = model_class._default_manager.filter(pk__in=object_ids)
        
        return objects