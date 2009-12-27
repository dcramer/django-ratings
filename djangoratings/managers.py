from django.db.models import Manager
from django.contrib.contenttypes.models import ContentType
import itertools

class VoteManager(Manager):
    def delete_from_ip_address(self, ip_address):
        # XXX: circular import
        from fields import RatingField

        qs = self.get_query_set().filter(ip_address=ip_address)
    
        to_update = []
        for content_type, objects in itertools.groupby(qs.distinct().values_list('content_type', 'object_id').order_by('content_type'), key=lambda x: x[0]):
            ct = ContentType.objects.get(pk=content_type)
            to_update.extend(list(ct.model_class().objects.filter(pk__in=list(objects)[0])))
    
        qs.delete()

        # TODO: this could be improved
        for obj in to_update:
            for field in getattr(obj, '_djangoratings', []):
                getattr(obj, field.name)._update()
            obj.save()