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
"""PreProc module for items related to configuration"""
import json
import os

from glusto.core import Glusto as g


# Define sentinel object NULL constant
NULL = object()


# pylint: disable=too-many-instance-attributes
#         reviewed and disabled (jdh)
class Configs:
    """Configuration class to handle config file, args, env tasks.
    Order of precedence (ordoprec) cli > envvars > config > defaults
    """
    def __init__(self, args, fqpath=None, config=None):
        self._args = args
        g.log.debug(self._args)
        self._fqpath = fqpath

        # define args using sentinel (not None)
        self._service_url = NULL
        self._payload_dir = NULL
        self._merge_launches = NULL
        self._simple_xml = NULL
        self._auto_dashboard = NULL
        self._debug = NULL
        self._log_filepath = NULL

        self._config = {}
        g.log.debug('Configs.init(): reading %s', self._fqpath)

        if config is not None:
            self._config = config
        else:
            self._config = self._read_fqpath(self.fqpath)
        g.log.debug("Configs.init(): CONFIG: %s", self._config)

    # PROPERTIES
    # using these to handle order of presidence of config, args, etc.
    @property
    def args(self):
        """args - the args object from CLI or REST API"""
        return self._args

    @property
    def fqpath(self):
        """fqpath - config file fully qualified path"""
        if self._fqpath is None:
            self._fqpath = self.args.get('config_file', None)

        return self._fqpath

    @property
    def config(self):
        """Return the config object"""
        return self._config

    @config.setter
    def config(self, config):
        self._config = config

    @property
    def service_config(self):
        """The RP PreProc section of the config file"""
        return self._config.get('rp_preproc', None)

    @property
    def rp_config(self):
        """The RP PreProc section of the config file"""
        if self._config is not None:
            return self._config.get('reportportal', None)

        return None

    @property
    def payload_dir(self):
        """Directory containing the payload files"""
        if self._payload_dir is NULL:
            self._payload_dir = \
                self.get_config_item('payload_dir',
                                     config=self.service_config)

        return self._payload_dir

    @payload_dir.setter
    def payload_dir(self, payload_dir):
        self._payload_dir = payload_dir

    @property
    def service_url(self):
        """use_service - send to service or use local client"""
        if self._service_url is NULL:
            self._service_url = \
                self.get_config_item('service_url',
                                     config=self.service_config)

        return self._service_url

    @property
    def simple_xml(self):
        """Use simple xml import into ReportPortal instead of processing"""
        if self._simple_xml is NULL:
            self._simple_xml = self.get_config_item('simple_xml',
                                                    config=self.rp_config)

        return self._simple_xml

    @property
    def merge_launches(self):
        """Config merge launches after import"""
        if self._merge_launches is NULL:
            self._merge_launches = \
                self.get_config_item('merge_launches', config=self.rp_config)

        return self._merge_launches

    @property
    def auto_dashboard(self):
        """Automatically create dashboards"""
        if self._auto_dashboard is NULL:
            self._auto_dashboard = \
                self.get_config_item('auto_dashboard', config=self.rp_config)

        return self._auto_dashboard

    @property
    def debug(self):
        """Set debug mode for more verbose logging and messages"""
        if self._debug is NULL:
            self._debug = self.get_config_item('debug',
                                               config=self.rp_config)

        return self._debug

    @property
    def log_filepath(self):
        """Set debug mode for more verbose logging and messages"""
        if self._log_filepath is NULL:
            self._log_filepath = self.get_config_item('log_filepath',
                                                      config=self.rp_config)

        return self._log_filepath

    # PRIVATE METHODS
    def _read_fqpath(self, fqpath=None):
        """Read a json formatted file into a dictionary"""
        g.log.debug('Configs._read_fqpath(): CONFIG FQPATH: %s', fqpath)
        if fqpath is not None:
            self._fqpath = fqpath

        configfd = open(self._fqpath, 'r')
        if configfd:
            self._config = json.load(configfd)

            return self._config

        return None

    def get_config_item(self, config_item, config=None,
                        ordoprec=None, default=None):
        """Order of precedence helper for configs"""
        # cli > envvars > config > defaults
        if config is None:
            config = self.config
        if ordoprec is None:
            ordoprec = ['config', 'env', 'cli']
        ordoprec_dict = {}

        # cli
        ordoprec_dict['cli'] = self.args.get(config_item, None)
        # config
        g.log.debug('Configs.get_config_item()...from config: %s', config)
        ordoprec_dict['config'] = config.get(config_item, None)
        # env
        env_name = 'RP_{}'.format(config_item.upper())
        ordoprec_dict['env'] = os.getenv(env_name, None)

        config_value = default
        for source in ordoprec:
            g.log.debug('Configs.get_config_item()... '
                        'Config item (%s): %s = %s',
                        config_item, source, ordoprec_dict[source])

            if ordoprec_dict[source] is not None:
                config_value = ordoprec_dict[source]

        g.log.debug('Configs.get_config_item()... config_value: %s',
                    config_value)
        return config_value
