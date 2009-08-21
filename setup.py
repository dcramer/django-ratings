#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-ratings',
    version='0.3.0',
    author='David Cramer',
    author_email='dcramer@gmail.com',
    description='Generic Ratings in Django',
    url='http://github.com/dcramer/django-ratings',
    install_requires=['django'],
    packages=find_packages(),
    include_package_data=True,
)