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
            ct = ContentType.objects.get(pk=content_type)
            to_update.extend(list(ct.model_class().objects.filter(pk__in=list(objects)[0])))
        
        retval = super(VoteQuerySet, self).delete(*args, **kwargs)
        
        # TODO: this could be improved
        for obj in to_update:
            for field in getattr(obj, '_djangoratings', []):
                getattr(obj, field.name)._update()
            obj.save()
        
        return retval
        
class VoteManager(Manager):
    def get_query_set(self):
        return VoteQuerySet(self.model)