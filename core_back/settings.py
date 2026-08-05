"""
BASE settings for core_back project.
"""
import os
from pathlib import Path
from datetime import timedelta


# -------------------
# BASE PATH
# -------------------
BASE_DIR = Path(__file__).resolve().parent.parent


# -------------------
# SECRET KEY
# (no poner aquí en producción)
# cada ambiente agrega su SECRET_KEY
# -------------------
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-vic')

# -------------------
# DEBUG
# -------------------
DEBUG = os.environ.get('DEBUG', 'True') == 'True'    # cada ambiente lo cambia


ALLOWED_HOSTS = [
    '127.0.0.1',
    #'localhost',
    '1b8e-148-215-111-243.ngrok-free.app',
    '*',
    'test1-back-phc.us-west-1.elasticbeanstalk.com'
    ]


CSRF_TRUSTED_ORIGINS = [
    'https://test1-back-phc.us-west-1.elasticbeanstalk.com',
    'https://1b8e-148-215-111-243.ngrok-free.app',
    #"https://96a967b472d0.ngrok-free.app ", 
    #"https://ruthe-unretributive-superscientifically.ngrok-free.dev",
    ]

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# -------------------
# APPS
# -------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',   
    'storages',

    # Apps
    'accounts',
    'candidates',
    'companies',
    'messages_app',
    'api',
    'addresses',
    'education',
    'jobs',
    'skills',
    'schedulers',
    'jobApplication',
    'payments',
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'core_auth.authentication.AccountJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}


# -------------------
# MIDDLEWARE
# -------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


CORS_ALLOW_ALL_ORIGINS = True


ROOT_URLCONF = 'core_back.urls'

# -------------------
# TEMPLATES
# -------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'core_back.wsgi.application'


# -------------------
# PASSWORDS
# -------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]


# -------------------
# LOCALE
# -------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# -------------------
# STATIC
# -------------------
STATIC_URL = 'static/'


# -------------------
# DEFAULT PK
# -------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# MEDIA_URL = '/media/'
# MEDIA_ROOT = BASE_DIR / 'media'

# -------------------
# EMAIL
# -------------------

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'info@professionalhospitalityconnections.com'
EMAIL_HOST_PASSWORD = 'jonyidxzbtbtginb'

DEFAULT_FROM_EMAIL = 'Professional Hospitality Connections <info@professionalhospitalityconnections.com>'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'phc_front'),        # valor por defecto para local
        'USER': os.environ.get('DB_USER', 'root'),       # valor por defecto local
        'PASSWORD': os.environ.get('DB_PASSWORD', '1234'),       # vacío por defecto local
        'HOST': os.environ.get('DB_HOST', 'localhost'),      # localhost local
        'PORT': os.environ.get('DB_PORT', '3306'),           # puerto MySQL local
    }
}

ELAVON_CONFIG = {
    "merchant_id": os.environ.get("ELAVON_MERCHANT_ID"), 
    "user_id": os.environ.get("ELAVON_USER_ID"),
    "pin": os.environ.get("ELAVON_PIN"),
    "is_demo": os.environ.get("ELAVON_DEMO", "True") == "True",
}

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

AWS_STORAGE_BUCKET_NAME = "phc-media-storage"
AWS_S3_REGION_NAME = "us-west-1"

AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_S3_FILE_OVERWRITE = True
AWS_QUERYSTRING_EXPIRE = 3600

AWS_S3_SIGNATURE_VERSION = "s3v4"

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

import sys
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",  # o DEBUG si quieres todo
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 524288000
FILE_UPLOAD_MAX_MEMORY_SIZE = 524288000

CONVERGE_ACCOUNT_ID = os.environ.get(
    "CONVERGE_ACCOUNT_ID",
    "0022897" 
)

CONVERGE_USER_ID = os.environ.get(
    "CONVERGE_USER_ID",
    "apiuser" 
)

CONVERGE_PIN = os.environ.get(
    "CONVERGE_PIN",
    "PK22NMFYE8K880XPRHE2SJYSQ70R6J8V7CEZK60Q0TVM04UHSF0XS3IFS2UT6OUL"  #
)

CONVERGE_HPP_URL = os.environ.get(
    "CONVERGE_HPP_URL",
    "https://api.demo.convergepay.com/hosted-payments/transaction_token"
)

CONVERGE_XML_URL = os.environ.get(
    "CONVERGE_XML_URL",
    "https://api.demo.convergepay.com/VirtualMerchantDemo/processxml.do"
)

CONVERGE_POST_URL = os.environ.get(
    "CONVERGE_POST_URL",
    "https://api.demo.convergepay.com/hosted-payments/"
)

SUBSCRIPTION_BYPASS_ACCOUNT_IDS = [
    27,
    170,
]