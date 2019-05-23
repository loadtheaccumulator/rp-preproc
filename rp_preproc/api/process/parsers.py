from flask_restplus import reqparse
from werkzeug.datastructures import FileStorage

from rp_preproc.api.restplus import api


upload_parser = api.parser()
upload_parser.add_argument('endpoint', location='form', required=True)
upload_parser.add_argument('api_token', location='form', required=True)
upload_parser.add_argument('project', location='form', required=True)
upload_parser.add_argument('file', location='files',
                           type=FileStorage, required=True)
