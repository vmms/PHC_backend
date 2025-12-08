"""
BASE settings for core_back project.
"""

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
SECRET_KEY = 'django-insecure-w^8x3)u@^0pgfksva@p4aq*xj2#86&56l_23d6j_tfr3dofki5'


# -------------------
# DEBUG
# -------------------
DEBUG = False    # cada ambiente lo cambia


ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'dada95d14c52.ngrok-free.app'
    ]


CSRF_TRUSTED_ORIGINS = [
    "https://dada95d14c52.ngrok-free.app", 
    "https://ruthe-unretributive-superscientifically.ngrok-free.dev",
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
# DATABASES
# importante: vacío
# cada ambiente usa su propia DB
# -------------------
DATABASES = {}


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
