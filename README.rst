A generic ratings module. The field itself appends two additional fields on the model, for optimization reasons. It adds `<field>_score`, and `<field>_votes` fields, which are both integer fields.

Installation
------------

You will need to add `djangoratings` to your `INSTALLED_APPS`::

	INSTALLED_APPS = (
	    'django.contrib.admin',
	    'django.contrib.auth',
	    'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'djangoratings',
	)

Finally, run `python manage.py syncdb` in your appication's directory to create the tables.

Setup your models
-----------------

The way django-ratings is built requires you to attach a RatingField to your models. This field will create two columns, a votes column, and a score column. They will both be prefixed with your field name::

	from djangoratings import RatingField

	class MyModel(models.Model):
	    rating = RatingField(range=5) # 5 possible rating values, 1-5

Alternatively you could do something like::

	from djangoratings import AnonymousRatingField

	class MyModel(models.Model):
	    rating = AnonymousRatingField(range=10)

Using the model API
-------------------

And adding votes is also simple::

	myinstance.rating.add(score=1, user=request.user, ip_address=request.META['REMOTE_ADDR'])

Retrieving votes is just as easy::

	myinstance_ai.get_rating(request.user, request.META['REMOTE_ADDR'])

Accessing information about the rating of an object is also easy::

	# these do not hit the database
	myinstance.rating.votes
	myinstance.rating.score