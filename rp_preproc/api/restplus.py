# Copyright 2019 Red Hat QE CCIT
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software. If not, see <http://www.gnu.org/licenses/>.
#
"""RESTPlus setup"""
import logging

from flask_restplus import Api
from rp_preproc import settings


log = logging.getLogger(__name__)

api = Api(version='0.1', title='ReportPortal PreProc API',
          description=('A REST API to pre-process xUnit XML '
                       'for import into ReportPortal'))


@api.errorhandler
def default_error_handler(e):
    """Default error handler"""
    message = 'An unhandled RESTplus exception occurred.'
    log.exception(message)

    if not settings.FLASK_DEBUG:
        return {'message': message}, 500
