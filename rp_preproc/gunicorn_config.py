"""Gunicorn config values"""

# pylint: disable=invalid-name
#         reviewed and disabled
bind = '0.0.0.0:8000'
workers = 4
timeout = 3600
keepalive = 7200
access_logfile = '/dev/stdout'
log_level = 'DEBUG'
