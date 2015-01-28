##############
django-ratings
##############

**This project is no longer maintained**

A generic ratings module. The field itself appends two additional fields on the model, for optimization reasons. It adds ``<field>_score``, and ``<field>_votes`` fields, which are both integer fields.

============
Installation
============

You will need to add ``djangoratings`` to your ``INSTALLED_APPS``::

	INSTALLED_APPS = (
	    'django.contrib.admin',
	    'django.contrib.auth',
	    'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'djangoratings',
	)

Finally, run ``python manage.py syncdb`` in your application's directory to create the tables.

=================
Setup your models
=================

The way django-ratings is built requires you to attach a RatingField to your models. This field will create two columns, a votes column, and a score column. They will both be prefixed with your field name::

	from djangoratings.fields import RatingField

	class MyModel(models.Model):
	    rating = RatingField(range=5) # 5 possible rating values, 1-5

Alternatively you could do something like::

	from djangoratings.fields import AnonymousRatingField

	class MyModel(models.Model):
	    rating = AnonymousRatingField(range=10)

If you'd like to use the built-in weighting methods, to make it appear more difficult for an object
to obtain a higher rating, you can use the ``weight`` kwarg::

	class MyModel(models.Model):
	    rating = RatingField(range=10, weight=10)

``RatingField`` allows the following options:

* ``range = 2`` - The range in which values are accepted. For example, a range of 2, says there are 2 possible vote scores.
* ``can_change_vote = False`` - Allow the modification of votes that have already been made.
* ``allow_delete = False`` - Allow the deletion of existent votes. Works only if ``can_change_vote = True``
* ``allow_anonymous = False`` - Whether to allow anonymous votes.
* ``use_cookies = False`` - Use COOKIES to authenticate user votes. Works only if ``allow_anonymous = True``. 

===================
Using the model API
===================

And adding votes is also simple::

	myinstance.rating.add(score=1, user=request.user, ip_address=request.META['REMOTE_ADDR'], request.COOKIES) # last param is optional - only if you use COOKIES-auth

Retrieving votes is just as easy::

	myinstance.rating.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES) # last param is optional - only if you use COOKIES-auth

*New* You're also able to delete existent votes (if deletion enabled)::

	myinstance.rating.delete(request.user, request.META['REMOTE_ADDR'], request.COOKIES) # last param is optional - only if you use COOKIES-auth

Accessing information about the rating of an object is also easy::

	# these do not hit the database
	myinstance.rating.votes
	myinstance.rating.score

How you can order by top-rated using an algorithm (example from Nibbits.com source)::

	# In this example, ``rating`` is the attribute name for your ``RatingField``
	qs = qs.extra(select={
	    'rating': '((100/%s*rating_score/(rating_votes+%s))+100)/2' % (MyModel.rating.range, MyModel.rating.weight)
	})
	qs = qs.order_by('-rating')

Get overall rating for your instance on a scale [0-range]::

        myinstance.rating.get_rating()

Get recent ratings for your instance::

	# This returns ``Vote`` instances.
	myinstance.rating.get_ratings()[0:5]

Get the percent of voters approval::

	myinstance.rating.get_percent()

Get that same percentage, but excluding your ``weight``::

	myinstance.rating.get_real_percent()

===============================
Generic Views: Processing Votes
===============================

The best way to use the generic views is by extending it, or calling it within your own code::

	from djangoratings.views import AddRatingFromModel
	
	urlpatterns = patterns('',
	    url(r'rate-my-post/(?P<object_id>\d+)/(?P<score>\d+)/', AddRatingFromModel(), {
	        'app_label': 'blogs',
	        'model': 'post',
	        'field_name': 'rating',
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

==========================
COOKIE format
==========================

*New*: For now COOKIE name has fixed format: "vote-{{ content_type.id }}.{{ object.id }}.{{ rating_field.key }}[:6]" and COOKIE value is simple datetime-stamp.

Example: vote-15.56.2c5504=20101213101523456000 

And this COOKIE lives in user's browser for 1 year (this period is also fixed for now)

*This feature may change in the future*

==========================
Limit Votes Per IP Address
==========================
*New in 0.3.5*: There is now a setting, ``RATINGS_VOTES_PER_IP``, to limit the number of unique IPs per object/rating-field combination. This is useful if you have issues with users registering multiple accounts to vote on a single object::

	RATINGS_VOTES_PER_IP = 3

=============
Template Tags
=============

Right now django-ratings has limited support for template tags, and only for Django.
Load a ratings template tag set. ```{% load ratings %}```.

-----------------
rating_by_request
-----------------

Retrieves the ``Vote`` cast by a user on a particular object and
stores it in a context variable. If the user has not voted, the
context variable will be 0::

	{% rating_by_request request on instance.field as vote %}

If you are using Coffin, a better approach might be::

	{% with instance.field_name.get_rating_for_user(request.user, request.META['REMOTE_ADDR'], request.COOKIES) as vote %}
		Do some magic with {{ vote }}
	{% endwith %}

To use the ``request`` context variable you will need to add ``django.core.context_processors.request`` to the ``TEMPLATE_CONTEXT_PROCESSORS`` setting.

--------------
rating_by_user
--------------

It is recommended that you use rating_by_request as you will gain full support
for anonymous users if they are enabled

Retrieves the ``Vote`` cast by a user on a particular object and
stores it in a context variable. If the user has not voted, the
context variable will be 0::

	{% rating_by_user user on instance.field as vote %}
