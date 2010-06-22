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
    def get_recommendations(self, user, model_class, min_score=1):
        from djangoratings.models import Vote, IgnoredObject
        
        content_type = ContentType.objects.get_for_model(model_class)
        
        params = dict(
            v=Vote._meta.db_table,
            sm=self.model._meta.db_table,
            m=model_class._meta.db_table,
            io=IgnoredObject._meta.db_table,
        )
        
        objects = model_class._default_manager.extra(
            tables=[params['v']],
            where=[
                '%(v)s.object_id = %(m)s.id and %(v)s.content_type_id = %%s' % params,
                '%(v)s.user_id IN (select to_user_id from %(sm)s where from_user_id = %%s and exclude = 0)' % params,
                '%(v)s.score >= %%s' % params,
                # Exclude already rated maps
                '%(v)s.object_id NOT IN (select object_id from %(v)s where content_type_id = %(v)s.content_type_id and user_id = %%s)' % params,
                # IgnoredObject exclusions
                '%(v)s.object_id NOT IN (select object_id from %(io)s where content_type_id = %(v)s.content_type_id and user_id = %%s)' % params,
            ],
            params=[content_type.id, user.id, min_score, user.id, user.id]
        ).distinct()

        # objects = model_class._default_manager.filter(pk__in=content_type.votes.extra(
        #     where=['user_id IN (select to_user_id from %s where from_user_id = %d and exclude = 0)' % (self.model._meta.db_table, user.pk)],
        # ).filter(score__gte=min_score).exclude(
        #     object_id__in=IgnoredObject.objects.filter(content_type=content_type, user=user).values_list('object_id', flat=True),
        # ).exclude(
        #     object_id__in=Vote.objects.filter(content_type=content_type, user=user).values_list('object_id', flat=True)
        # ).distinct().values_list('object_id', flat=True))
        
        return objects
    
    def update_recommendations(self):
        # TODO: this is mysql only atm
        # TODO: this doesnt handle scores that have multiple values (e.g. 10 points, 5 stars)
        # due to it calling an agreement as score = score. We need to loop each rating instance
        # and express the condition based on the range.
        from djangoratings.models import Vote
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute('begin')
        cursor.execute('truncate table %s' % (self.model._meta.db_table,))
        cursor.execute("""insert into %(t1)s
          (to_user_id, from_user_id, agrees, disagrees, exclude)
          select v1.user_id, v2.user_id,
                 sum(if(v2.score = v1.score, 1, 0)) as agrees,
                 sum(if(v2.score != v1.score, 1, 0)) as disagrees, 0
            from %(t2)s as v1
              inner join %(t2)s as v2
                on v1.user_id != v2.user_id
                and v1.object_id = v2.object_id
                and v1.content_type_id = v2.content_type_id
            where v1.user_id is not null
              and v2.user_id is not null
            group by v1.user_id, v2.user_id
            having agrees / (disagrees + 0.0001) > 3
          on duplicate key update agrees = values(agrees), disagrees = values(disagrees);""" % dict(
            t1=self.model._meta.db_table,
            t2=Vote._meta.db_table,
        ))
        cursor.execute('commit')
        cursor.close()