from .base import *
import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'mysql',
        'USER': 'admin',
        'PASSWORD': 'root1234',
        'HOST': 'database-phc.cbwmicsw2dg1.us-west-1.rds.amazonaws.com',
        'PORT': '3306',
    }
}

DEBUG = False