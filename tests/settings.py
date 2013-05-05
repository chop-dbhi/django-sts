DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
    }
}

INSTALLED_APPS = (
    'sts',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'tests',
)

SECRET_KEY = 'abc123'
