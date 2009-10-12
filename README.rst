##############
django-ratings
##############

A generic ratings module. The field itself appends two additional fields on the model, for optimization reasons. It adds `<field>_score`, and `<field>_votes` fields, which are both integer fields.


============
Installation
============

You will need to add `djangoratings` to your `INSTALLED_APPS`::

	INSTALLED_APPS = (
	    'django.contrib.admin',
	    'django.contrib.auth',
	    'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'djangoratings',
	)

Finally, run `python manage.py syncdb` in your appication's directory to create the tables.

=================
Setup your models
=================

The way django-ratings is built requires you to attach a RatingField to your models. This field will create two columns, a votes column, and a score column. They will both be prefixed with your field name::

	from djangoratings import RatingField

	class MyModel(models.Model):
	    rating = RatingField(range=5) # 5 possible rating values, 1-5

Alternatively you could do something like::

	from djangoratings import AnonymousRatingField

	class MyModel(models.Model):
	    rating = AnonymousRatingField(range=10)

If you'd like to use the built-in weighting methods, to make it appear more difficult for an object
to obtain a higher rating, you can use the `weight` kwarg::

	class MyModel(models.Model):
	    rating = RatingField(range=10, weight=10)

===================
Using the model API
===================

And adding votes is also simple::

	myinstance.rating.add(score=1, user=request.user, ip_address=request.META['REMOTE_ADDR'])

Retrieving votes is just as easy::

	myinstance_ai.get_rating(request.user, request.META['REMOTE_ADDR'])

Accessing information about the rating of an object is also easy::

	# these do not hit the database
	myinstance.rating.votes
	myinstance.rating.score

How you can order by top-rated using an algorithm (example from Nibbits.com source)::

	# In this example, `rating` is the attribute name for your `RatingField`
	qs = qs.extra(select={
	    'rating': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (MyModel.rating.range, MyModel.rating.weight)
	})
	qs = qs.order_by('-rating')

Get recent ratings for your instance::

	# This returns `Vote` instances.
	myinstance.rating.get_ratings()[0:5]

Get the percent of voters approval::

	myinstance.rating.get_percent()

Get that same percentage, but excluding your `weight`::

	myinstance.rating.get_real_percent()

===============================
Generic Views: Processing Votes
===============================

The best way to use the generic views is by extending it, or calling it within your own code.

	from djangoratings.views import AddRatingFromModule
	
	urlpatterns = patterns('',
	    url(r'rate-my-post/(?P<object_id>\d+)/(?P<score>\d+)/', AddRatingFromModel(), {
	        'app_label': 'blogs',
	        'model': 'post',
	    }),
	)

Another example, on Nibbits we use a basic API interface, and we simply call the ``AddRatingView`` within our own view::


	from djangoratings.views import AddRatingView
	
	# For the sake of this actually looking like documentation:
	params = {
	    'content_type_id': 23,
	    'object_id': 34,
	    'field_name': 'ratings', # this should match the field name defined in your model
	    'score': 1, # the score value they're sending
	}
	response = AddRatingView()(request, **params)
	if response.status_code == 200:
	    if response.content == 'Vote recorded.':
	        request.user.add_xp(settings.XP_BONUSES['submit-rating'])
	    return {'message': response.content, 'score': params['score']}
	return {'error': 9, 'message': response.content}
