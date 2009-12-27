import unittest
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from exceptions import *
from fields import AnonymousRatingField, RatingField

settings.RATINGS_VOTES_PER_IP = 1

class RatingTestModel(models.Model):
    rating = AnonymousRatingField(range=2, can_change_vote=True)
    rating2 = RatingField(range=2, can_change_vote=False)

class RatingTestCase(unittest.TestCase):
    def testRatings(self):
        instance = RatingTestModel.objects.create()
        
        # Test adding votes
        instance.rating.add(score=1, user=None, ip_address='127.0.0.1')
        self.assertEquals(instance.rating.score, 1)
        self.assertEquals(instance.rating.votes, 1)

        # Test adding votes
        instance.rating.add(score=2, user=None, ip_address='127.0.0.2')
        self.assertEquals(instance.rating.score, 3)
        self.assertEquals(instance.rating.votes, 2)

        # Test changing of votes
        instance.rating.add(score=2, user=None, ip_address='127.0.0.1')
        self.assertEquals(instance.rating.score, 4)
        self.assertEquals(instance.rating.votes, 2)
        
        # Test users
        user = User.objects.create(username='django-ratings')
        user2 = User.objects.create(username='django-ratings2')
        
        instance.rating.add(score=2, user=user, ip_address='127.0.0.3')
        self.assertEquals(instance.rating.score, 6)
        self.assertEquals(instance.rating.votes, 3)
        
        instance.rating2.add(score=2, user=user, ip_address='127.0.0.3')
        self.assertEquals(instance.rating2.score, 2)
        self.assertEquals(instance.rating2.votes, 1)
        
        self.assertRaises(IPLimitReached, instance.rating2.add, score=2, user=user2, ip_address='127.0.0.3')
