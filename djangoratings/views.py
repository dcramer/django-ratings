from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponse, Http404

from exceptions import *
        
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
        
        had_voted = bool(field.get_rating_for_user(request.user, request.META['REMOTE_ADDR']))
        
        try:
            field.add(score, request.user, request.META.get('REMOTE_ADDR'))
        except AuthRequired:
            return self.authentication_required_response(request, context)
        except InvalidRating:
            return self.invalid_rating_response(request, context)
        except CannotChangeVote:
            return self.cannot_change_vote_response(request, context)
        if had_voted:
            return self.rating_changed_response(request, context)
        return self.rating_added_response(request, context)
    
    def get_context(self, request, context={}):
        return context
    
    def render_to_response(self, template, context, request):
        raise NotImplementedError

    def rating_changed_response(self, request, context):
        response = HttpResponse('Vote changed.')
        return response
    
    def rating_added_response(self, request, context):
        response = HttpResponse('Vote recorded.')
        return response

    def authentication_required_response(self, request, context):
        response = HttpResponse('You must be logged in to vote.')
        response.status_code = 403
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


class AddRatingFromModel(AddRatingView):
    def __call__(self, request, model, app_label, object_id, field_name, score):
        """__call__(request, module_name, app_label, field_name, score)
        
        Adds a vote to the specified model field."""
        try:
            content_type = ContentType.objects.get(model=model, app_label=app_label)
        except ContentType.DoesNotExist:
            raise Http404('Invalid `model` or `app_label`.')
        
        return super(AddRatingFromModel, self).__call__(request, content_type.id,
            object_id, field_name, score)