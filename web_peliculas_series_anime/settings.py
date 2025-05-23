"""
Django settings for web_peliculas_series_anime project.
"""

from pathlib import Path
import os
import sys # Necesario para sys.argv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Carga de variables de entorno desde .env (SOLO PARA DESARROLLO LOCAL) ---
IS_VERCEL_PRODUCTION = os.environ.get('VERCEL_ENV') == 'production'
IS_COLLECTSTATIC = 'collectstatic' in sys.argv # Detectar si se está ejecutando collectstatic

if not IS_VERCEL_PRODUCTION:
    try:
        from dotenv import load_dotenv
        env_path = BASE_DIR / '.env'
        if env_path.is_file():
            load_dotenv(dotenv_path=env_path)
            print("INFO: Archivo .env cargado para desarrollo local.")
        else:
            print(f"INFO: Archivo .env no encontrado en {env_path}. Se usarán valores por defecto o variables de entorno del SO.")
    except ImportError:
        print("ADVERTENCIA: El paquete 'python-dotenv' no está instalado. El archivo .env no se cargará.")
        print("           Para desarrollo local, considera añadir 'python-dotenv' a tus requirements.txt.")
# --- Fin de la carga de .env ---


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} [{name}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': os.environ.get('DJANGO_LOG_LEVEL', 'DEBUG' if not IS_VERCEL_PRODUCTION else 'INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'local_fallback_django_insecure_gm43%hnrhr46nchk!76u=y^#c*si!tqv-t_mg9wy5^5cn(uv6x'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS_STRING = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STRING.split(',') if host.strip()]

if IS_VERCEL_PRODUCTION and os.environ.get('VERCEL_URL'):
    vercel_host = os.environ.get('VERCEL_URL')
    if vercel_host not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(vercel_host)
    # Para permitir todos los dominios de preview de Vercel de este proyecto:
    # (ej. mi-proyecto-git-rama.vercel.app, mi-proyecto- uniquesuffix.vercel.app)
    # Es más seguro ser explícito o usar un patrón más específico si es posible.
    # Si tu VERCEL_URL es tu dominio de producción, esto no ayuda mucho con los previews.
    # Una mejor aproximación es añadir los dominios de preview explícitamente o usar '*.vercel.app'
    # si estás seguro de que solo tu proyecto usará ese patrón.
    # Por ahora, dejaremos que el usuario añada los dominios de preview necesarios a DJANGO_ALLOWED_HOSTS.


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'catalogo',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web_peliculas_series_anime.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'web_peliculas_series_anime.wsgi.application'


# Database
DATABASE_URL = os.environ.get('DATABASE_URL')

if IS_COLLECTSTATIC and not DATABASE_URL:
    # Si estamos corriendo collectstatic y no hay DATABASE_URL (común en entornos de build simples),
    # usa una configuración de base de datos dummy para evitar errores como _sqlite3 no encontrado,
    # asumiendo que collectstatic no REALMENTE necesita una base de datos funcional.
    print("INFO: Ejecutando collectstatic sin un backend de base de datos completo (usando dummy).")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.dummy',
        }
    }
elif DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True if IS_VERCEL_PRODUCTION else False
        )
    }
else: # Fallback a SQLite para desarrollo local o si DATABASE_URL no está configurada
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    if IS_VERCEL_PRODUCTION and not IS_COLLECTSTATIC:
        # No mostrar esta advertencia durante collectstatic si ya estamos usando el dummy.
        print("ADVERTENCIA CRÍTICA: DATABASE_URL no está configurada. Usando SQLite efímero en producción (¡NO RECOMENDADO!).")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "catalogo" / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles_build" / "static"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Configuración para envío de Email (Reporte de Enlaces) ---
# Lee estas configuraciones desde variables de entorno en producción
EMAIL_BACKEND = os.environ.get('DJANGO_EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend') # Console para desarrollo
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'webmaster@localhost')

# URLs de los JSON (Mantenidas como variables de entorno o directamente si son fijas)
# Es mejor poner estas en variables de entorno si pueden cambiar o son sensibles.
# Si son públicas y fijas, está bien tenerlas aquí.
JSON_PELICULAS_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/peliculas.json'
JSON_SERIES_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/series.json'
JSON_ANIME_URL = 'https://raw.githubusercontent.com/DermisZabala/jsonMovieNet/refs/heads/main/anime.json'

# --- Configuraciones de Seguridad para Producción ---
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', 'False').lower() == 'true'
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', 'False').lower() == 'true'
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() == 'true'

# Para HSTS (solo si estás seguro y tu sitio siempre usará HTTPS)
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', 0)) # Ej: 31536000 para 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() == 'true'
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'False').lower() == 'true'

# Si Vercel (o cualquier proxy) maneja HTTPS y reenvía como HTTP
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')