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
"""Process payload for RP PreProc client and REST API service"""
import logging
import urllib3

from flask_restplus import Resource

from glusto.core import Glusto as g

from rp_preproc.api.process.parsers import import_parser_payload
from rp_preproc.api.restplus import api
from rp_preproc.libs.preproc import PreProcService


# TODO: get rid of this if possible
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# pylint: disable=invalid-name
#         reviewed and disabled
log = logging.getLogger(__name__)

description = 'Operations related to importing results into ReportPortal'
payload_namespace = api.namespace('process/payload', description=description)


@payload_namespace.route('/')
class XunitImport(Resource):
    """Namespace class for importing an RP PreProc payload"""
    # pylint: disable=no-self-use
    @api.expect(import_parser_payload)
    def post(self):
        """Process a raw xUnit XML file for importing into ReportPortal"""
        args = import_parser_payload.parse_args()

        # set logging options
        log_level = 'INFO'
        if args.debug:
            log_level = 'DEBUG'
        g.log = g.create_log('mylog', filename='STDOUT', level=log_level)
        g.log.info('payload received...')
        g.log.info(args)

        preproc = PreProcService(args)
        response = preproc.process()
        preproc.cleanup_tmp()

        print('IMPORT COMPLETE: {}'.format(response))

        return response
