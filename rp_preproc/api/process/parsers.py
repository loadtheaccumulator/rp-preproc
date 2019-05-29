from flask_restplus import reqparse
from werkzeug.datastructures import FileStorage

from rp_preproc.api.restplus import api


upload_parser = api.parser()
upload_parser.add_argument('endpoint', location='form', required=True,
                           help='The path to the ReportPortal API')
upload_parser.add_argument('api_token', location='form', required=True,
                           help='The user\'s API token from profile')
upload_parser.add_argument('project', location='form', required=True,
                           help='The ReportPortal project')
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True,
                           help='An xUnit XML result file')

example_parser = api.parser()
example_parser.add_argument('endpoint', location='form', required=True,
                            help='The path to the ReportPortal API')
example_parser.add_argument('api_token', location='form', required=True,
                            help='The user\'s API token from profile')
example_parser.add_argument('project', location='form', required=True,
                            help='The ReportPortal project')
