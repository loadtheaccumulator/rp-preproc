from setuptools import setup, find_packages

setup(
    name='rp-preproc',
    version='0.0.1',
    description='REST API for pre-processing XML data for ReportPortal import',
    url='https://github.com/loadtheaccumulator/rp-preproc',
    author='Jonathan D. Holloway',

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Information Technology',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='reportportal rest api xml xunit junit',

    packages=find_packages(),

    install_requires=['flask-restplus==0.9.2', 'Flask-SQLAlchemy==2.1',
                      'reportportal_client'],
)
