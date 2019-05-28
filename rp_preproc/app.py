import logging.config

import os
from flask import Flask, Blueprint
from flask_restplus import Api
from rp_preproc import settings
from rp_preproc.api.process.endpoints.xunit import ns as xunit_namespace


app = Flask(__name__)
logging_conf_path = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                                  '../logging.conf'))
logging.config.fileConfig(logging_conf_path)
log = logging.getLogger(__name__)

app.config['SWAGGER_UI_DOC_EXPANSION'] = \
   settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP

blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

api = Api(version='0.0.1', title='ReportPortal PreProc API',
          description=('A REST API to pre-process xUnit XML '
                       'for import into ReportPortal'))

api.init_app(blueprint)
api.add_namespace(xunit_namespace)
app.register_blueprint(blueprint)


@app.route('/hello')
def hello():
    return 'hello, world'

def configure_app(flask_app):
    flask_app.config['SWAGGER_UI_DOC_EXPANSION'] = \
        settings.RESTPLUS_SWAGGER_UI_DOC_EXPANSION
    flask_app.config['RESTPLUS_VALIDATE'] = settings.RESTPLUS_VALIDATE
    flask_app.config['RESTPLUS_MASK_SWAGGER'] = settings.RESTPLUS_MASK_SWAGGER
    flask_app.config['ERROR_404_HELP'] = settings.RESTPLUS_ERROR_404_HELP


def initialize_app(flask_app):
    configure_app(flask_app)

    blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

    api = Api(version='0.0.1', title='ReportPortal PreProc API',
              description=('A REST API to pre-process xUnit XML '
                           'for import into ReportPortal'))

    api.init_app(blueprint)
    api.add_namespace(xunit_namespace)
    flask_app.register_blueprint(blueprint)


def main():
#    initialize_app(app)
    log.info('>>>>> Starting development server at '
             'http://{}/api/ <<<<<'.format(app.config['SERVER_NAME']))
    app.run(host='0.0.0.0', port=8080, debug=settings.FLASK_DEBUG)


if __name__ == "__main__":
    main()
