from flask_restplus import fields
from rp_preproc.api.restplus import api

# TODO: make this useful
xunit = api.model('xunit file', {
    'filename': fields.String(required=True, description='xUnit filename'),
})
