import logging
import re
import requests
from zipfile import ZipFile

from flask import request
from flask_restplus import Resource
from rp_preproc.api.process.serializers import xunit
from rp_preproc.api.process.parsers import upload_parser, example_parser
from rp_preproc.api.restplus import api

log = logging.getLogger(__name__)

ns = api.namespace('process/xunit',
                   description='Operations related to importing xunit XML')


@ns.route('/')
class XunitCollection(Resource):

    @api.expect(upload_parser)
    def post(self):
        """
        Process a raw xUnit XML file for importing into ReportPortal
        """
        args = upload_parser.parse_args()
        uploaded_file = args['file']

        xml_file = '/tmp/my_results.xml'
        uploaded_file.save(xml_file)

        outfile = '/tmp/my_results.zip'
        with ZipFile(outfile, 'w') as zipit:
            zipit.write(xml_file)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(args.api_token)

        url = '{}/{}/launch/import'.format(args.endpoint, args.project)
        files = {'file': open(outfile, 'rb')}
        response = requests.post(url=url, data={"mysubmit": "Go"},
                                 files=files, headers=session.headers,
                                 verify=False)

        idregex = re.match('.*id = (.*) is.*', response.json()['msg'])

        return {'api uri': url, 'project': args.project,
                'launch id': idregex.group(1)}, 201


@ns.route('/zipped')
class XunitZipped(Resource):

    @api.expect(upload_parser)
    def post(self):
        """
        Process a zipped archive of an xUnit XML file and related attachments
        """
        args = upload_parser.parse_args()
        uploaded_file = args['file']
        zip_file = '/tmp/my_results2.zip'
        uploaded_file.save(zip_file)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(args.api_token)

        url = '{}/{}/launch/import'.format(args.endpoint, args.project)
        files = {'file': open(zip_file, 'rb')}
        response = requests.post(url=url, data={"mysubmit": "Go"},
                                 files=files, headers=session.headers)

        idregex = re.match('.*id = (.*) is.*', response.json()['msg'])

        return {'api uri': url, 'project': args.project,
                'launch id': idregex.group(1)}, 201


@ns.route('/example')
class XunitCollection(Resource):

    @api_expect(example_parser)
    def get(self):
        """
        Send an example xunit file to test ReportPortal import.
        """
        xml_file = '../../../resources/example_xunit.xml'
        uploaded_file.save(xml_file)

        outfile = '/tmp/my_results.zip'
        with ZipFile(outfile, 'w') as zipit:
            zipit.write(xml_file)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(args.api_token)

        url = '{}/{}/launch/import'.format(args.endpoint, args.project)
        files = {'file': open(outfile, 'rb')}
        response = requests.post(url=url, data={"mysubmit": "Go"},
                                 files=files, headers=session.headers,
                                 verify=False)

        idregex = re.match('.*id = (.*) is.*', response.json()['msg'])

        return {'api uri': url, 'project': args.project,
                'launch id': idregex.group(1)}, 201

