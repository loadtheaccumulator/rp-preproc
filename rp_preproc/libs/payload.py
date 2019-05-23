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
"""Payload module to handle files for the RP PreProc service REST API"""
import os
import shutil
import tarfile
import uuid

import requests
from requests.exceptions import Timeout

from glusto.core import Glusto as g


class Payload:
    """Payload class for all things payload related"""
    def __init__(self, config_fqpath, sourcedir_fqpath):
        self.config_fqpath = config_fqpath
        self.sourcedir_fqpath = sourcedir_fqpath
        # generate a uuid for temp use
        rppp_uuid = uuid.uuid1()
        self.tmp_clientdir \
            = os.path.join('/tmp', 'rppp_client_{}'.format(rppp_uuid.hex))
        os.mkdir(self.tmp_clientdir)
        self.client_bundlename = 'rppp_payload.tar.gz'
        self.payload_fqpath = os.path.join(self.tmp_clientdir,
                                           self.client_bundlename)
        g.log.debug('SOURCE: %s', self.payload_fqpath)
        g.log.debug('PAYLOAD: %s', self.payload_fqpath)

    def bundle(self):
        """Bundle the payload and tar.gz it"""
        # tar.gz the results directory
        if self.sourcedir_fqpath is not None:
            return_to_dir = os.getcwd()
            os.chdir(self.sourcedir_fqpath)
            with tarfile.open(self.payload_fqpath, "w:gz") as tarfh:
                for root, _, files in os.walk('.'):
                    g.log.debug('root: %s', root)
                    for file in files:
                        g.log.debug(file)
                        tarfh.add(os.path.join(root, file))
            tarfh.close()
            os.chdir(return_to_dir)

            return self.payload_fqpath

        return None

    def send(self, rp_preproc_url, data):
        """Send a payload file and config file to the service REST API"""
        # send the config, xunit, and attachment files
        g.log.debug('sending payload to %s', rp_preproc_url)

        files = {'config_file': open(self.config_fqpath, 'rb'),
                 'payload_file': open(self.payload_fqpath, 'rb')}

        try:
            response = requests.post(rp_preproc_url, data=data, files=files)
        except Timeout:
            g.log.debug('payload.send() timed out')

        # remove temp client dir
        if os.path.exists(self.tmp_clientdir):
            shutil.rmtree(self.tmp_clientdir)

        g.log.debug('payload.send() Returning...')
        return response
