from setuptools import setup, find_packages


kwargs = {
    # Packages
    'packages': find_packages(exclude=['tests', '*.tests',
        '*.tests.*', 'tests.*']),
    'include_package_data': True,

    # Dependencies
    'install_requires': [
        'django',    
    ],

    'test_suite': 'test_suite',

    # Metadata
    'name': 'django-sts',
    'version': __import__('sts').get_version(),
    'author': 'Byron Ruth',
    'author_email': 'b@devel.io',
    'description': 'State Transition System for Django',
    'license': 'BSD',
    'keywords': 'FSM state machine transition Django',
    'url': 'https://github.com/cbmi/django-sts/',
    'classifiers': [
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Information Technology',
    ],
}

setup(**kwargs)
