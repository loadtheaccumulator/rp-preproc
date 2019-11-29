# rp-preproc
Pre-processor for ReportPortal

## Install rp-preproc client during alpha, beta
### Install via pip
    $ virtualenv -p `which python3` venv
    $ source venv/bin/activate
    (venv) $ pip install git+https://github.com/loadtheaccumulator/rc_preproc.git#preprocX


## Develop during alpha, beta
### Setup the python virtual environment
    $ virtualenv -p `which python3` venv
    $ source venv/bin/activate
    (venv) $ pip install -r requirements.txt

### Clone this repo
    (venv) git clone <URL TO THIS REPO>

### Install rp_preproc
    (venv) $ python setup.py develop
    # run rp_preproc server
    (venv) $ gunicorn -c rp_preproc/gunicorn_config.py \
    --reload rp_preproc.app:app &

### run client script
    (venv) $ rp_preproc -c resources/examples/rp_preproc_payload_remote.json \
    -d resources/examples/payload_example_medium

### run client script using the remote rp_preproc service
    (venv) $ rp_preproc -c resources/examples/rp_preproc_payload_remote.json \
    -d resources/examples/payload_example_medium --service

### run client script and merge multiple launches
    (venv) $ rp_preproc -c resources/examples/rp_preproc_payload_remote.json \
    -d resources/examples/payload_example_medium --merge

### run client script w/o pre-processing the XML
    (venv) $ rp_preproc -c resources/examples/rp_preproc_payload_remote.json \
    -d resources/examples/payload_example_medium --simple
