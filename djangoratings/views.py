from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse

class AddRatingView(object):
    def __call__(self, request, content_type_id, object_id, field_name, score):
        """__call__(request, content_type_id, object_id, field_name, score)
        
        Adds a vote to the specified model field."""
        instance = self.get_instance(content_type_id, object_id)
        
        context = self.get_context(request)
        context['instance'] = instance
        
        try:
            field = getattr(instance, field_name)
        except AttributeError:
            return self.invalid_field_response(request, context)
        
        context.update({
            'field': field,
            'score': score,
        })
        
        try:
            field.add(score, request.user, request.META.get('REMOTE_ADDR'))
        except AuthError:
            return self.authentication_required_response(request, context)
        except InvalidRating:
            return self.invalid_rating_response(request, context)
        except CannotChangeVote:
            return self.cannot_change_vote_response(request, context)
        return self.rating_added_response(request, context)
    
    def get_context(self, request, context={}):
        return context
    
    def render_to_response(self, template, context, request):
        raise NotImplementedError
    
    def rating_added_response(self, request, context):
        response = HttpResponse('Vote recorded.')
        return response
    
    def cannot_change_vote_response(self, request, context):
        response = HttpResponse('You have already voted.')
        response.status_code = 403
        return response
    
    def invalid_field_response(self, request, context):
        response = HttpResponse('Invalid field name.')
        response.status_code = 403
        return response
    
    def invalid_rating_response(self, request, context):
        response = HttpResponse('Invalid rating value.')
        response.status_code = 403
        return response
        
    def get_instance(self, content_type_id, object_id):
        return ContentType.objects.get(pk=content_type_id)\
            .get_object_for_this_type(pk=object_id)