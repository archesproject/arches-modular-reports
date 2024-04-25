"""
Django settings for arches_provenance project.
"""

import os
import arches
import inspect
from django.utils.translation import gettext_lazy as _

try:
    from arches.settings import *
except ImportError:
    pass

# ACCESSIBILITY_MODE = ""

APP_NAME = "arches_provenance"
APP_ROOT = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
STATICFILES_DIRS = (os.path.join(APP_ROOT, "media"),) + STATICFILES_DIRS
STATIC_ROOT = "/arches/static"

DATATYPE_LOCATIONS.append("arches_provenance.datatypes")
FUNCTION_LOCATIONS.append("arches_provenance.functions")
SEARCH_COMPONENT_LOCATIONS.append("arches_provenance.search_components")

LOCALE_PATHS.append(os.path.join(APP_ROOT, "locale"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "mnl1pz=2p+sacc88*8ujh)r9-p8du+8#6#hd)kn$k5a(8)k)k7"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ROOT_URLCONF = "arches_provenance.urls"

# a prefix to append to all elasticsearch indexes, note: must be lower case
ELASTICSEARCH_PREFIX = "arches_provenance"

ELASTICSEARCH_CUSTOM_INDEXES = []
# [{
#     'module': 'arches_provenance.search_indexes.sample_index.SampleIndex',
#     'name': 'my_new_custom_index' <-- follow ES index naming rules
# }]

KIBANA_URL = "http://localhost:5601/"
KIBANA_CONFIG_BASEPATH = "kibana"  # must match Kibana config.yml setting (server.basePath) but without the leading slash,
# also make sure to set server.rewriteBasePath: true

LOAD_DEFAULT_ONTOLOGY = False
LOAD_PACKAGE_ONTOLOGIES = True

DATABASES = {
    "default": {
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "CONN_MAX_AGE": 0,
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "HOST": "localhost",
        "NAME": "arches_provenance",
        "OPTIONS": {},
        "PASSWORD": "postgis",
        "PORT": "5432",
        "POSTGIS_TEMPLATE": "template_postgis",
        "TEST": {"CHARSET": None, "COLLATION": None, "MIRROR": None, "NAME": None},
        "TIME_ZONE": None,
        "USER": "postgres",
    }
}

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.gis",
    "arches",
    "arches.app.models",
    "arches.management",
    "guardian",
    "captcha",
    "revproxy",
    "corsheaders",
    "oauth2_provider",
    "django_celery_results",
    "compressor",
    "arches_provenance",
    "webpack_loader",
)

ARCHES_APPLICATIONS = ()

ALLOWED_HOSTS = []

SYSTEM_SETTINGS_LOCAL_PATH = os.path.join(APP_ROOT, "system_settings", "System_Settings.json")
WSGI_APPLICATION = "arches_provenance.wsgi.application"

RESOURCE_IMPORT_LOG = os.path.join(APP_ROOT, "logs", "resource_import.log")
DEFAULT_RESOURCE_IMPORT_USER = {"username": "admin", "userid": 1}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "file": {
            "level": "WARNING",  # DEBUG, INFO, WARNING, ERROR
            "class": "logging.FileHandler",
            "filename": os.path.join(APP_ROOT, "arches.log"),
            "formatter": "console",
        },
        "console": {"level": "WARNING", "class": "logging.StreamHandler", "formatter": "console"},
    },
    "loggers": {"arches": {"handlers": ["file", "console"], "level": "WARNING", "propagate": True}},
}

# Absolute filesystem path to the directory that will hold user-uploaded files.
MEDIA_ROOT = os.path.join(APP_ROOT)

# Sets default max upload size to 15MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 15728640

# Unique session cookie ensures that logins are treated separately for each app
SESSION_COOKIE_NAME = "arches_provenance"

# For more info on configuring your cache: https://docs.djangoproject.com/en/2.2/topics/cache/
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    },
    "user_permission": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "user_permission_cache",
    },
}

# Hide nodes and cards in a report that have no data
HIDE_EMPTY_NODES_IN_REPORT = True

BYPASS_CARDINALITY_TILE_VALIDATION = False
BYPASS_UNIQUE_CONSTRAINT_TILE_VALIDATION = False
BYPASS_REQUIRED_VALUE_TILE_VALIDATION = False

DATE_IMPORT_EXPORT_FORMAT = "%Y-%m-%d"  # Custom date format for dates imported from and exported to csv

# Identify the usernames and duration (seconds) for which you want to cache the time wheel
CACHE_BY_USER = {"anonymous": 3600 * 24}
TILE_CACHE_TIMEOUT = 600  # seconds
GRAPH_MODEL_CACHE_TIMEOUT = None

OAUTH_CLIENT_ID = ""  #'9JCibwrWQ4hwuGn5fu2u1oRZSs9V6gK8Vu8hpRC4'
MOBILE_DEFAULT_ONLINE_BASEMAP = {"default": "mapbox://styles/mapbox/streets-v9"}
MOBILE_IMAGE_SIZE_LIMITS = {
    # These limits are meant to be approximates. Expect to see uploaded sizes range +/- 20%
    # Not to exceed the limit defined in DATA_UPLOAD_MAX_MEMORY_SIZE
    "full": min(1500000, DATA_UPLOAD_MAX_MEMORY_SIZE),  # ~1.5 Mb
    "thumb": 400,  # max width/height in pixels, this will maintain the aspect ratio of the original image
}

APP_TITLE = "Arches | Provenance"
COPYRIGHT_TEXT = "All Rights Reserved."
COPYRIGHT_YEAR = "2019"

ENABLE_CAPTCHA = False
# RECAPTCHA_PUBLIC_KEY = ''
# RECAPTCHA_PRIVATE_KEY = ''
# RECAPTCHA_USE_SSL = False
NOCAPTCHA = True
# RECAPTCHA_PROXY = 'http://127.0.0.1:8000'
if DEBUG is True:
    SILENCED_SYSTEM_CHECKS = ["captcha.recaptcha_test_key_error"]


# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  #<-- Only need to uncomment this for testing without an actual email server
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = "xxxx@xxx.com"
# EMAIL_HOST_PASSWORD = 'xxxxxxx'
# EMAIL_PORT = 587

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

CELERY_BROKER_URL = ""  # RabbitMQ --> "amqp://guest:guest@localhost",  Redis --> "redis://localhost:6379/0"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_BACKEND = "django-db"  # Use 'django-cache' if you want to use your cache as your backend
CELERY_TASK_SERIALIZER = "json"


CELERY_SEARCH_EXPORT_EXPIRES = 24 * 3600  # seconds
CELERY_SEARCH_EXPORT_CHECK = 3600  # seconds

CELERY_BEAT_SCHEDULE = {
    "delete-expired-search-export": {
        "task": "arches.app.tasks.delete_file",
        "schedule": CELERY_SEARCH_EXPORT_CHECK,
    },
    "notification": {
        "task": "arches.app.tasks.message",
        "schedule": CELERY_SEARCH_EXPORT_CHECK,
        "args": ("Celery Beat is Running",),
    },
}

# By setting RESTRICT_MEDIA_ACCESS to True, media file requests outside of Arches will checked against nodegroup permissions.
RESTRICT_MEDIA_ACCESS = False


# see https://docs.djangoproject.com/en/1.9/topics/i18n/translation/#how-django-discovers-language-preference
# to see how LocaleMiddleware tries to determine the user's language preference
# (make sure to check your accept headers as they will override the LANGUAGE_CODE setting!)
# also see get_language_from_request in django.utils.translation.trans_real.py
# to see how the language code is derived in the actual code

####### TO GENERATE .PO FILES DO THE FOLLOWING ########
# run the following commands
# language codes used in the command should be in the form (which is slightly different
# form the form used in the LANGUAGE_CODE and LANGUAGES settings below):
# --local={countrycode}_{REGIONCODE} <-- countrycode is lowercase, regioncode is uppercase, also notice the underscore instead of hyphen
# commands to run (to generate files for "British English, German, and Spanish"):
# django-admin.py makemessages --ignore=env/* --local=de --local=en --local=en_GB --local=es  --extension=htm,py
# django-admin.py compilemessages


# default language of the application
# language code needs to be all lower case with the form:
# {langcode}-{regioncode} eg: en, en-gb ....
# a list of language codes can be found here http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en"

# list of languages to display in the language switcher,
# if left empty or with a single entry then the switch won't be displayed
# language codes need to be all lower case with the form:
# {langcode}-{regioncode} eg: en, en-gb ....
# a list of language codes can be found here http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGES = [
    #   ('de', _('German')),
    ("en", _("English")),
    #   ('en-gb', _('British English')),
    #   ('es', _('Spanish')),
]

# override this to permenantly display/hide the language switcher
SHOW_LANGUAGE_SWITCH = len(LANGUAGES) > 1

STATIC_URL = "/arches/pir/static/"

STATICFILES_DIRS = build_staticfiles_dirs(
    root_dir=ROOT_DIR,
    app_root=APP_ROOT,
    arches_applications=ARCHES_APPLICATIONS,
)

TEMPLATES = build_templates_config(
    root_dir=ROOT_DIR,
    debug=DEBUG,
    app_root=APP_ROOT,
    arches_applications=ARCHES_APPLICATIONS,
)

WEBPACK_LOADER = {
    "DEFAULT": {
        "STATS_FILE": os.path.join(APP_ROOT, "webpack/webpack-stats.json"),
    },
}

DOCKER = False
HOSTED_APPS = ()

try:
    from .package_settings import *
except ImportError:
    try:
        from package_settings import *
    except ImportError as e:
        pass

try:
    from .settings_local import *
except ImportError as e:
    try:
        from settings_local import *
    except ImportError as e:
        pass

if DOCKER:
    try:
        from .settings_docker import *
    except ImportError:
        try:
            from settings_docker import *
        except ImportError as e:
            pass

INSTALLED_APPS = INSTALLED_APPS + HOSTED_APPS

if __name__ == "__main__":
    transmit_webpack_django_config(
        root_dir=ROOT_DIR,
        app_root=APP_ROOT,
        arches_applications=ARCHES_APPLICATIONS,
        public_server_address=PUBLIC_SERVER_ADDRESS,
        static_url=STATIC_URL,
        webpack_development_server_port=WEBPACK_DEVELOPMENT_SERVER_PORT,
    )
