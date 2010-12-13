from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404

from exceptions import *
from django.conf import settings
from default_settings import RATINGS_VOTES_PER_IP

class AddRatingView(object):
    def __call__(self, request, content_type_id, object_id, field_name, score):
        """__call__(request, content_type_id, object_id, field_name, score)
        
        Adds a vote to the specified model field."""
        
        try:
            instance = self.get_instance(content_type_id, object_id)
        except ObjectDoesNotExist:
            raise Http404('Object does not exist')
        
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
        
        had_voted = bool(field.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES))
        
        context['had_voted'] = had_voted
                    
        try:
            adds = field.add(score, request.user, request.META.get('REMOTE_ADDR'), request.COOKIES)
        except IPLimitReached:
            return self.too_many_votes_from_ip_response(request, context)
        except AuthRequired:
            return self.authentication_required_response(request, context)
        except InvalidRating:
            return self.invalid_rating_response(request, context)
        except CannotChangeVote:
            return self.cannot_change_vote_response(request, context)
        except CannotDeleteVote:
            return self.cannot_delete_vote_response(request, context)
        if had_voted:
            return self.rating_changed_response(request, context, adds)
        return self.rating_added_response(request, context, adds)
    
    def get_context(self, request, context={}):
        return context
    
    def render_to_response(self, template, context, request):
        raise NotImplementedError

    def too_many_votes_from_ip_response(self, request, context):
        response = HttpResponse('Too many votes from this IP address for this object.')
        return response

    def rating_changed_response(self, request, context, adds={}):
        response = HttpResponse('Vote changed.')
        if 'cookie' in adds:
            cookie_name, cookie = adds['cookie_name'], adds['cookie']
            if 'deleted' in adds:
                response.delete_cookie(cookie_name)
            else:
                response.set_cookie(cookie_name, cookie, 31536000, path='/') # TODO: move cookie max_age to settings
        return response
    
    def rating_added_response(self, request, context, adds={}):
        response = HttpResponse('Vote recorded.')
        if 'cookie' in adds:
            cookie_name, cookie = adds['cookie_name'], adds['cookie']
            if 'deleted' in adds:
                response.delete_cookie(cookie_name)
            else:
                response.set_cookie(cookie_name, cookie, 31536000, path='/') # TODO: move cookie max_age to settings
        return response

    def authentication_required_response(self, request, context):
        response = HttpResponse('You must be logged in to vote.')
        response.status_code = 403
        return response
    
    def cannot_change_vote_response(self, request, context):
        response = HttpResponse('You have already voted.')
        response.status_code = 403
        return response
    
    def cannot_delete_vote_response(self, request, context):
        response = HttpResponse('You can\'t delete this vote.')
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
        """__call__(request, model, app_label, object_id, field_name, score)
        
        Adds a vote to the specified model field."""
        try:
            content_type = ContentType.objects.get(model=model, app_label=app_label)
        except ContentType.DoesNotExist:
            raise Http404('Invalid `model` or `app_label`.')
        
        return super(AddRatingFromModel, self).__call__(request, content_type.id,
                                                        object_id, field_name, score)
