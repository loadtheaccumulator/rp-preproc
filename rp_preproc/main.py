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
"""ReportPortal pre-processor client"""
import argparse
import json
import sys
import time
import urllib3

from glusto.core import Glusto as g

from rp_preproc.libs.payload import Payload
from rp_preproc.libs.preproc import PreProcClient


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def run(args):
    """Function to run the client"""
    # set logging options
    g.set_log_level('glustolog', 'glustolog1', 'INFO')
    if args.log_filepath is not None:
        g.set_log_filename('glustolog', 'glustolog1', args.log_filepath)

    if args.debug:
        print('ARGS DEBUG IS TRUE')
        g.set_log_level('glustolog', 'glustolog1', 'DEBUG')

    g.log.debug(args)

    preproc = PreProcClient(vars(args))
    preproc_response = {}

    import_start_time = int(time.time())
    g.log.info('Import started @ %s', import_start_time)

    use_service = False
    if preproc.configs.service_url and args.service_url != "no":
        use_service = True
        g.log.debug("using service")
    else:
        g.log.debug('using client')

    # SERVICE + PRE_PROC
    if use_service:
        g.log.info("Sending to RP PreProc...")
        rp_return_code = 1

        if (preproc.configs.fqpath is not None and
                preproc.configs.payload_dir is not None):
            g.log.debug('Sending to rp_preproc service')
            g.log.debug('PAYLOAD_DIR: %s', preproc.configs.payload_dir)
            payload = Payload(preproc.configs.fqpath,
                              preproc.configs.payload_dir)
            payload_fqpath = payload.bundle()
            g.log.debug('payload_filepath: %s', payload_fqpath)
            if preproc.configs.service_url is not None:
                rp_preproc_api = (preproc.configs.service_url +
                                  'api/v1/process/payload/')
                data = {'simple_xml': preproc.configs.simple_xml,
                        'merge_launches': preproc.configs.merge_launches,
                        'auto_dashboard': preproc.configs.auto_dashboard,
                        'debug': preproc.configs.debug}
                response = payload.send(rp_preproc_api, data=data)
                g.log.debug(response)
                rp_response = response.json()
        else:
            # TODO: raise a payload_dir Exception
            g.log.error('ERROR: Must specify a payload directory '
                        'via config or CLI')
            return 1

        if response.status_code == 200:
            rp_return_code = 0
    else:
        # Send directly to ReportPortal API
        g.log.info("POSTing directly to ReportPortal API...")
        rp_response = preproc.process()

        rp_return_code = 0

    import_finish_time = int(time.time())
    time_elapsed = import_finish_time - import_start_time
    g.log.info('Import ended at %s', import_finish_time)
    g.log.info('Import ran for %s seconds', time_elapsed)
    preproc_response['start_time'] = import_start_time
    preproc_response['end_time'] = import_finish_time
    preproc_response['elapsed_time'] = time_elapsed

    final_response = {"reportportal": rp_response,
                      "rp_preproc": preproc_response}
    # print the final json to stdout
    print(json.dumps(final_response, indent=2, sort_keys=True))

    return rp_return_code


def main():
    """Entry point console script for setuptools.
    Provides a command-line interface to rp-preproc.

    Example:
        $ rp_client -c rp_preproc_conf.json  \
            -d resources/examples/myresults_example \
            --service http://rp-preproc.example.com:8080/ \
            --merge
    """
    parser = argparse.ArgumentParser(description="ReportPortal client",
                                     epilog="Red Hat QE CCIT")
    parser.add_argument("-c", "--config",
                        help="RP PreProc config file",
                        action="store", dest="config_file",
                        default=None, required=True)
    parser.add_argument("-d", "--payload_dir",
                        help="Directory containing results and attachments",
                        action="store", dest="payload_dir",
                        default=None)
    # optional
    parser.add_argument("-l", "--log",
                        help=("Filepath for logfile"),
                        action="store", dest="log_filepath",
                        default='/tmp/rp_preproc.log')
    parser.add_argument("--service", nargs="?",
                        help=("Send xml to ReportPortal via an "
                              "rp_preproc service."),
                        action="store", dest="service_url")
    parser.add_argument("--simple_xml",
                        help="Send xml without preprocessing",
                        action="store_true", dest="simple_xml",
                        default=None)
    parser.add_argument("--merge",
                        help="Merge multiple launches into one.",
                        action="store_true", dest="merge_launches",
                        default=None)
    parser.add_argument("--auto-dashboard",
                        help=("Automatically create a dashboard "
                              "with basic filter and widget"),
                        action="store_true", dest="auto_dashboard",
                        default=None)
    parser.add_argument("--debug",
                        help="Display debug info in log and stdout",
                        action="store_true", dest="debug")

    args = parser.parse_args()

    return_code = run(args)

    return return_code


# pylint: disable=invalid-name
#         reviewed and disabled
if __name__ == '__main__':
    exitcode = main()

    sys.exit(exitcode)
