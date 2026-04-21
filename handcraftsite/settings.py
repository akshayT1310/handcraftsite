"""
Django settings for handcraftsite project.
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-1%yq_ex3tg@tt2c&!+s5th)h^bc17nl1_7fc1mn6x0-dw#z#=0'

# SECURITY WARNING: don't run with debug turned on in production!
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'shop',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'handcraftsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.cart_count',
            ],
        },
    },
]

WSGI_APPLICATION = 'handcraftsite.wsgi.application'

# Database
# Priority order:
# 1. `DATABASE_URL` env var (recommended for Supabase). If present we parse
#    it via `dj_database_url` and enable SSL by default.
# 2. Vercel-specific DB pieces (`DB_NAME` + `DB_HOST`) — legacy support.
# 3. Local sqlite fallback.
DATABASE_URL = os.environ.get('DATABASE_URL')
# If running on Vercel and no DATABASE_URL is provided, use a writable
# temporary sqlite path so serverless functions can write during runtime.
VERCEL = bool(os.environ.get('VERCEL'))
DEFAULT_SQLITE_PATH = os.environ.get('SQLITE_DB_PATH') if os.environ.get('SQLITE_DB_PATH') else (Path('/tmp/db.sqlite3') if VERCEL else BASE_DIR / 'db.sqlite3')
if DATABASE_URL:
    # When a DATABASE_URL is provided (e.g. Supabase connection string),
    # prefer that. However, importing Django's PostgreSQL backend requires
    # a Postgres driver (psycopg or psycopg2). On Vercel build/runtime the
    # driver may not be available during the build step which runs
    # `manage.py collectstatic`. To avoid failing the build, detect the
    # driver and fall back to SQLite during builds when necessary.
    pg_driver_available = False
    try:
        import psycopg as _pg  # psycopg v3
        pg_driver_available = True
    except Exception:
        try:
            import psycopg2 as _pg  # legacy psycopg2
            pg_driver_available = True
        except Exception:
            pg_driver_available = False

    if pg_driver_available:
        DATABASES = {
            'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600, ssl_require=True)
        }
    else:
        # If we're running on Vercel (build) and driver isn't installed,
        # fall back to sqlite to let build steps like collectstatic succeed.
            if os.environ.get('VERCEL'):
            import warnings

            warnings.warn(
                "Postgres driver (psycopg/psycopg2) not installed; falling back to sqlite for build. "
                "To use Supabase in production, add 'psycopg[binary]' to requirements.txt and pin a compatible Python runtime on Vercel."
            )
            DATABASES = {
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                        "NAME": DEFAULT_SQLITE_PATH,
                }
            }
        else:
            raise RuntimeError(
                "DATABASE_URL is set but no Postgres driver (psycopg/psycopg2) is installed. "
                "Install 'psycopg[binary]' in your environment."
            )
else:
    # On Vercel builds the VERCEL env var may be present even when DB creds
    # are not configured. Only use the explicit DB_* env vars if provided.
    USE_PG = bool(os.environ.get("VERCEL") and os.environ.get("DB_NAME") and os.environ.get("DB_HOST"))
    if USE_PG:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": os.environ.get("DB_NAME"),
                "USER": os.environ.get("DB_USER"),
                "PASSWORD": os.environ.get("DB_PASSWORD"),
                "HOST": os.environ.get("DB_HOST"),
                "PORT": os.environ.get("DB_PORT") or "5432",
                # ensure SSL when connecting to hosted DBs
                "OPTIONS": {"sslmode": "require"},
            }
        }
    else:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": DEFAULT_SQLITE_PATH,
            }
        }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Razorpay Payment Gateway Configuration
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_PORT = 587
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'HANDCRAFT <your-email@gmail.com>'

# MSG91 SMS Configuration
SMS_ENABLED = True  # Set to False to disable SMS
SMS_API_KEY = os.getenv('SMS_API_KEY')
SMS_SENDER_ID = 'HNDCFT'  # Your approved sender ID (6 characters)
SMS_ROUTE = '4'  # 4 = Transactional, 1 = Promotional
SMS_TEMPLATE_ID = ''  # Your MSG91 template ID (optional for flow API)
SMS_COUNTRY_CODE = '91'  # India country code