from models import Vote
from django.contrib.contenttypes.models import ContentType
from fields import RatingField

def delete_from_ip_address(ip_address):
    qs = Vote.objects.filter(ip_address=ip_address)
    
    to_update = []
    for content_type, objects in itertools.groupby(qs.distinct().values('content_type_id', 'object_id').order_by('content_type_id'), key=lambda x: x[0]):
        ct = ContentType.objects.get_for_model(pk=content_type)
        to_update.extend(ct.get_object_for_this_type(pk__in=objects))
    
    qs.delete()
    
    # TODO: this could be improved
    for obj in to_update:
        for field in obj._meta.fields:
            if isinstance(field, RatingField):
                getattr(obj, field.name)._update()
        obj.save()