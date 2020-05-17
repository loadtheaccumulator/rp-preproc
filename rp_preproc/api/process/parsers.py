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
"""REST API arg parsers"""
from werkzeug.datastructures import FileStorage
from flask_restplus import inputs

from rp_preproc.api.restplus import api


# process/payload
# pylint: disable=invalid-name
#         reviewed and disabled
import_parser_payload = api.parser()
import_parser_payload.add_argument('config_file', location='files',
                                   type=FileStorage, required=True,
                                   help=('An RP PreProc config file '
                                         'describing settings for importing '
                                         'into ReportPortal'))
import_parser_payload.add_argument('payload_file', location='files',
                                   type=FileStorage, required=True,
                                   help=('A tar.gz file of results '
                                         'and attachments.'))
import_parser_payload.add_argument('simple_xml', location='form',
                                   required=False, default=None,
                                   type=inputs.boolean,
                                   help=('Send xml without preprocessing.'))
import_parser_payload.add_argument("merge_launches", location='form',
                                   required=False, default=None,
                                   type=inputs.boolean,
                                   help="Merge multiple launches into one.")
import_parser_payload.add_argument("auto_dashboard", location='form',
                                   required=False, default=None,
                                   type=inputs.boolean,
                                   help="Auto create a dashboard.")
import_parser_payload.add_argument("debug", location='form',
                                   required=False, default=None,
                                   type=inputs.boolean,
                                   help="Output debug info to log and stdout")
