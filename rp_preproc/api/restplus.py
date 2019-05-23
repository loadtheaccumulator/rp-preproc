import logging
import traceback

from flask_restplus import Api
from rp_preproc import settings


log = logging.getLogger(__name__)

api = Api(version='0.0.1', title='ReportPortal PreProc API',
          description=('A REST API to pre-process xUnit XML '
                       'for import into ReportPortal'))


@api.errorhandler
def default_error_handler(e):
    message = 'An unhandled exception occurred.'
    log.exception(message)

    if not settings.FLASK_DEBUG:
        return {'message': message}, 500
