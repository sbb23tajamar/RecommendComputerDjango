from pathlib import Path
from dotenv import load_dotenv
import os
 
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)
 
DOC_INT_ENDPOINT = str(os.getenv('AZURE_FORM_RECOGNIZER_ENDPOINT'))
DOC_INT_KEY = str(os.getenv('AZURE_FORM_RECOGNIZER_KEY'))
DOC_INT_MODEL = str(os.getenv('AZURE_MODEL_ID'))
 
AI_ENDPOINT = str(os.getenv('AZURE_OPENAI_ENDPOINT'))
AI_KEY = str(os.getenv('AZURE_OPENAI_KEY'))
AI_MODEL = str(os.getenv('AZURE_OPENAI_MODEL'))
 
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-wuk26=f8-*r5ipo!34^%80e&-0ackr9g(=fv#2r0io)(_u0y!_'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'computers',
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

ROOT_URLCONF = 'computer_manager.urls'

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

WSGI_APPLICATION = 'computer_manager.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'sql_server.pyodbc',  # Usamos el backend de SQL Server
        'NAME': 'ordenadores_db',  # Nombre de tu base de datos
        'USER': 'sbb23tajamar',  # El usuario que usas para conectarte
        'PASSWORD': 'G7$kz!4m',  # Tu contraseña
        'HOST': 'computerserver.database.windows.net',  # Dirección de tu servidor en Azure
        'PORT': '',  # Deja vacío, ya que generalmente el puerto es el predeterminado (1433)
        'OPTIONS': {
            'driver': 'ODBC Driver 18 for SQL Server',  # Usa el driver más reciente
            'extra_params': 'TrustServerCertificate=yes;',  # Para evitar errores con certificados
        },
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'  # O el idioma que estés utilizando

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

 


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
