import ast
import requests
import sys
from os import environ
from django.core.exceptions import ImproperlyConfigured

from ldap import SCOPE_SUBTREE as ldap_SCOPE_SUBTREE
from django_auth_ldap.config import LDAPSearch

from arches.settings import ELASTICSEARCH_CONNECTION_OPTIONS



def get_env_variable(var_name):
    msg = "Set the %s environment variable"
    try:
        return environ[var_name]
    except KeyError:
        error_msg = msg % var_name
        raise ImproperlyConfigured(error_msg)


def get_optional_env_variable(var_name):
    try:
        return environ[var_name]
    except KeyError:
        return None


ARCHES_NAMESPACE_FOR_DATA_EXPORT = 'https://localhost:8000/'

FORCE_SCRIPT_NAME = '/arches/pir/'

USER_ARCHES_NAMESPACE_FOR_DATA_EXPORT = get_optional_env_variable('ARCHES_NAMESPACE_FOR_DATA_EXPORT')
if USER_ARCHES_NAMESPACE_FOR_DATA_EXPORT:
    # Make this unique, and don't share it with anybody.
    ARCHES_NAMESPACE_FOR_DATA_EXPORT = USER_ARCHES_NAMESPACE_FOR_DATA_EXPORT

PREFERRED_CONCEPT_SCHEMES = [
    "http://vocab.getty.edu/aat/",
    "https://data.getty.edu/local/thesaurus/",
    "http://www.cidoc-crm.org/cidoc-crm/",
    "https://linked.art/ns/terms/"]
    
ONTOLOGY_PATH = 'ontology'
ONTOLOGY_BASE = 'cidoc_crm_v6.2.4.xml'
ONTOLOGY_BASE_NAME = 'Linked Art'
ONTOLOGY_EXT = ['linkedart.xml', 'linkedart_crm_enhancements.xml']
ONTOLOGY_BASE_VERSION="CIDOC v6.2.4 - Linked Art v1"
#ONTOLOGY_BASE_ID='dfd0b072-1ce6-4b20-9cb0-86790dedf76d'
ONTOLOGY_NAMESPACES = {
        "http://purl.org/dc/terms/": "dcterms",
        "http://purl.org/dc/elements/1.1/": "dc",
        "http://schema.org/": "schema",
        "http://www.w3.org/2004/02/skos/core#": "skos",
        "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
        "http://xmlns.com/foaf/0.1/": "foaf",
        "http://www.w3.org/2001/XMLSchema#": "xsd",
        "https://linked.art/ns/terms/": 'la',
        "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
        "http://www.cidoc-crm.org/cidoc-crm/": "",
        "http://www.ics.forth.gr/isl/CRMgeo/": "geo",
        "http://www.ics.forth.gr/isl/CRMsci/": "sci"
}

# options are either "PROD" or "DEV" (installing with Dev mode set gets you extra dependencies)
MODE = get_env_variable('DJANGO_MODE')

DEBUG = ast.literal_eval(get_env_variable('DJANGO_DEBUG'))

COUCHDB_URL = 'http://{}:{}@{}:{}'.format(get_env_variable('COUCHDB_USER'), get_env_variable('COUCHDB_PASS'),
                                          get_env_variable('COUCHDB_HOST'),
                                          get_env_variable('COUCHDB_PORT'))  # defaults to localhost:5984

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': get_env_variable('PGDBNAME'),
        'USER': get_env_variable('PGUSERNAME'),
        'PASSWORD': get_env_variable('PGPASSWORD'),
        'HOST': get_env_variable('PGHOST'),
        'PORT': get_env_variable('PGPORT'),
        'POSTGIS_TEMPLATE': 'template_postgis',
    }
}

USER_PG_SUPERUSER = get_optional_env_variable('PG_SUPERUSER')
USER_PG_SUPERUSER_PW = get_optional_env_variable('PG_SUPERUSER_PW')
if USER_PG_SUPERUSER and USER_PG_SUPERUSER_PW:
    PG_SUPERUSER = USER_PG_SUPERUSER
    PG_SUPERUSER_PW = USER_PG_SUPERUSER_PW


ELASTICSEARCH_HTTP_PORT = get_env_variable('ESPORT')
ELASTICSEARCH_HOSTS = [
    {'host': get_env_variable('ESHOST'), 'port': int(ELASTICSEARCH_HTTP_PORT)}
    # or AWS Elasticsearch Service:
    #{'host': get_env_variable('ESHOST'), 'port': 443, "use_ssl": True}
]

ELASTICSEARCH_CONNECTION_OPTIONS = {"timeout": 30}

USER_DONT_USE_SSL = get_optional_env_variable('DONT_USE_SSL_ES')
if not USER_DONT_USE_SSL:
    ELASTICSEARCH_CONNECTION_OPTIONS['use_ssl'] = True
    ELASTICSEARCH_CONNECTION_OPTIONS['scheme'] = "https"

    USER_ESUSERNAME = get_optional_env_variable('ESUSERNAME')
    USER_ESPASSWORD = get_optional_env_variable('ESPASSWORD')
    if USER_ESPASSWORD and USER_ESUSERNAME:
        ELASTICSEARCH_CONNECTION_OPTIONS['http_auth'] = (USER_ESUSERNAME, USER_ESPASSWORD)


USER_ELASTICSEARCH_PREFIX = get_optional_env_variable('ARCHES_NAME')
if USER_ELASTICSEARCH_PREFIX:
    ELASTICSEARCH_PREFIX = USER_ELASTICSEARCH_PREFIX

ALLOWED_HOSTS = get_env_variable('DOMAIN_NAMES').split()

USER_SECRET_KEY = get_optional_env_variable('DJANGO_SECRET_KEY')
if USER_SECRET_KEY:
    # Make this unique, and don't share it with anybody.
    SECRET_KEY = USER_SECRET_KEY

#############################################
# ==============LDAP CONFIG START============
#############################################

# Baseline configuration.
AUTHENTICATION_BACKENDS = ('django_auth_ldap.backend.LDAPBackend',
    "arches.app.utils.email_auth_backend.EmailAuthenticationBackend",
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",  # this is default
    "guardian.backends.ObjectPermissionBackend",
    "arches.app.utils.permission_backend.PermissionBackend",
)
AUTH_LDAP_SERVER_URI = get_env_variable('AUTH_LDAP_SERVER_URI')

# By default, all mapped user fields will be updated each time the user logs in.
# To disable this, set AUTH_LDAP_ALWAYS_UPDATE_USER to False
AUTH_LDAP_ALWAYS_UPDATE_USER = True   # Default

AUTH_LDAP_BIND_DN = get_env_variable('AUTH_LDAP_BIND_DN')
AUTH_LDAP_BIND_PASSWORD = get_env_variable('AUTH_LDAP_BIND_PASSWORD')

AUTH_LDAP_USER_SEARCH = LDAPSearch(
    get_env_variable('AUTH_LDAP_SEARCH'),
    ldap_SCOPE_SUBTREE,
    '(uid=%(user)s)',
)

# Setting user details from LDAP reminder:
# from django_auth_ldap.config import LDAPGroupQuery
# AUTH_LDAP_USER_FLAGS_BY_GROUP = {
#     "is_active": "cn=active,ou=groups,dc=example,dc=com",
#     "is_staff": (
#         LDAPGroupQuery("cn=staff,ou=groups,dc=example,dc=com") |
#         LDAPGroupQuery("cn=admin,ou=groups,dc=example,dc=com")
#     ),
#     "is_superuser": "cn=superuser,ou=groups,dc=example,dc=com"
# }

# Simple group restrictions reminder
# AUTH_LDAP_REQUIRE_GROUP = 'cn=enabled,ou=django,ou=groups,dc=example,dc=com'
# AUTH_LDAP_DENY_GROUP = 'cn=disabled,ou=django,ou=groups,dc=example,dc=com'

AUTH_LDAP_USER_ATTR_MAP = {"first_name": "givenName",
                           "last_name": "sn",
                           "email": "mail"}

#############################################
# ==============LDAP CONFIG END==============
#############################################

STATIC_ROOT = get_optional_env_variable('STATIC_ROOT') or '/static_root'

APP_NAME = get_env_variable('ARCHES_NAME')

APP_TITLE = APP_NAME + ' | Arches'

#APP_ROOT = '/web_root/arches/arches/app'

USER_APP_ROOT = get_optional_env_variable('USER_APP_ROOT')
if USER_APP_ROOT:
    # Make this unique, and don't share it with anybody.
    APP_ROOT = USER_APP_ROOT

COPYRIGHT_TEXT = ''
COPYRIGHT_YEAR = '2019'


#############################################
# ============== CELERY CONFIG ==============
#############################################

CELERY_BROKER_URL = get_optional_env_variable('CELERY_BROKER_URL') or "memory://localhost/"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_RESULT_BACKEND = get_optional_env_variable('CELERY_RESULT_BACKEND') or "django-db"  # Use 'django-cache' if you want to use your cache as your backend
CELERY_TASK_SERIALIZER = "json"
CELERY_SEARCH_EXPORT_EXPIRES = 24 * 3600  # seconds
CELERY_SEARCH_EXPORT_CHECK = 3600  # seconds

CELERY_BEAT_SCHEDULE = {
    "delete-expired-search-export": {"task": "arches.app.tasks.delete_file", "schedule": CELERY_SEARCH_EXPORT_CHECK},
    "notification": {"task": "arches.app.tasks.message", "schedule": CELERY_SEARCH_EXPORT_CHECK, "args": ("Celery Beat is Running",)},
}

#############################################
# ============STATIC FILES SUBPATH===========
#############################################
SUBPATH = get_optional_env_variable('ARCHES_SUBPATH') or '/'
MEDIA_URL = SUBPATH + "/"
STATIC_URL = SUBPATH + "static/"
ADMIN_MEDIA_PREFIX = SUBPATH + "static/admin/"

MAPBOX_API_KEY=get_optional_env_variable("MAPBOX_API_KEY") or ""
