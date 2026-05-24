# settings.py
import os
import sys
from pathlib import Path

import environ

# ─────────────────────────────────────────────────────────────
# BASE CONFIG
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize django-environ
env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ─────────────────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # GIS & API
    'django.contrib.gis',        # GeoDjango (must be before your apps)
    'rest_framework',
    'corsheaders',
    
    # Your apps
    'flood_zones',
    'risk_engine',
]

# ─────────────────────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be first
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

# ─────────────────────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────────────────────
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

WSGI_APPLICATION = 'core.wsgi.application'

# ─────────────────────────────────────────────────────────────
# DATABASE (PostGIS)
# ─────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST', default='localhost'),
        'PORT': env('DB_PORT', default='5432'),
    }
}

# ─────────────────────────────────────────────────────────────
# GEODJANGO LIBRARY PATHS (Cross-platform)
# ─────────────────────────────────────────────────────────────
# On Windows: load explicit paths from .env (handles spaces in username)
# On Linux: leave as None → system libraries auto-detected
if sys.platform == 'win32':
    # Add DLL directory for Python 3.8+
    if sys.version_info >= (3, 8):
        dll_dir = r'C:\Users\FAREEHA KARIM\AppData\Local\Programs\Python\Python312\Lib\site-packages\osgeo'
        os.add_dll_directory(dll_dir)
    
    # Load paths from .env with forward slashes, NO escaping
    for lib in ['GDAL', 'GEOS', 'PROJ']:
        env_key = f'{lib}_LIBRARY_PATH'
        value = env(env_key, default=None)
        if value:
            clean_path = value.replace('\\', '/')  # Only normalize slashes
            os.environ[env_key] = clean_path
            globals()[env_key] = clean_path
else:
    # Linux: auto-detect from system paths
    GDAL_LIBRARY_PATH = None
    GEOS_LIBRARY_PATH = None
    PROJ_LIBRARY_PATH = None

# ─────────────────────────────────────────────────────────────
# AUTH & PASSWORD
# ─────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────────────────────
# INTERNATIONALIZATION
# ─────────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'  # Your local timezone
USE_I18N = True
USE_TZ = True

# ─────────────────────────────────────────────────────────────
# STATIC & MEDIA FILES
# ─────────────────────────────────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # For collectstatic

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─────────────────────────────────────────────────────────────
# CORS (React frontend)
# ─────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
])
CORS_ALLOW_CREDENTIALS = True

# ─────────────────────────────────────────────────────────────
# DJANGO REST FRAMEWORK
# ─────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # Remove in prod if desired
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Tighten in production
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# ─────────────────────────────────────────────────────────────
# DEFAULT PRIMARY KEY FIELD TYPE
# ─────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
