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
"""PreProc module for importing data into ReportPortal"""
import gzip
import json
import os
import shutil
import tarfile
import uuid
import xmltodict

from glusto.core import Glusto as g

from rp_preproc.libs.configs import Configs
from rp_preproc.libs.reportportal import (ReportPortal, Filter, Dashboard,
                                          WidgetLaunchesTable,
                                          WidgetOverallStats)
from rp_preproc.libs.xunit_xml import XunitXML


class PreProc:
    """PreProc client class for preprocessing test results for ReportPortal"""
    @property
    def args(self):
        """Args from cli or service"""
        return self._args

    @property
    def configs(self):
        """Configs arg"""
        return self._configs

    def __init__(self, args):
        # read config files and update g.config attributes
        self._args = args
        self._config_file = self.args.get('config_file', None)
        g.log.debug('ARGS: %s', self._args)
        self._configs = None

    @staticmethod
    def get_uuid():
        """Unique ID helper"""
        return uuid.uuid1()

    @staticmethod
    def read_config_file(fqpath):
        """Read a json formatted file into a dictionary"""
        configfd = open(fqpath, 'r')
        if configfd:
            config = json.load(configfd)

            return config

        return None

    @staticmethod
    def gzip_file(input_filepath, gzip_filepath):
        """Gzip a file"""
        with open(input_filepath, 'rb') as f_in:
            with gzip.open(gzip_filepath, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        # TODO: add errorcheck
        return True

    @staticmethod
    def process_response(response):
        """Process an HTTP response into something usable"""
        # TODO: process status code and set return
        g.log.debug('RESPONSE...')
        g.log.debug(response)
        g.log.debug('status_code: %s', response.status_code)
        g.log.debug('text: %s', response.text)
        return_code = response.status_code
        if response.status_code == 200:
            return_code = 0

        return return_code

    @staticmethod
    def get_results_dir(args, config):
        """Get the directoy containing results from config, args, etc."""
        if args.results_dir is not None:
            results_dir = args.results_dir
        else:
            results_dir = config.get('results_dir', None)

        return results_dir

    def process(self):
        """Process the files in the payload for importing into ReportPortal"""
        g.log.debug('PREPROCESSING STARTED')
        rportal = ReportPortal(self.configs.rp_config)
        # get list of xml result files
        results_file_dir = os.path.join(self.configs.payload_dir, 'results')
        result_file_list = XunitXML.get_file_list(results_file_dir)
        return_obj = {}

        # Loop through result files in drop directory
        responses = []
        for fqpath in result_file_list:
            with open(fqpath) as xmlfd:
                g.log.debug('Processing fqpath %s', fqpath)
                filename = os.path.basename(fqpath)
                filename_base, _ = os.path.splitext(filename)
                g.log.debug('%s %s', filename, filename_base)
                if self.configs.simple_xml:
                    # this is for xml file import without processing
                    g.log.debug('Sending file...')
                    response = rportal.api_post_zipfile(fqpath)
                else:
                    g.log.debug('Parsing XML...')
                    xml_data = xmltodict.parse(xmlfd.read())
                    xunit_xml = XunitXML(rportal, name=filename_base,
                                         configs=self._configs,
                                         xml_data=xml_data)
                    response = xunit_xml.process()
                    responses.append(response)

        #return_obj["responses"] = responses

        # Merge launches
        launch_list = rportal.launches.list
        if len(result_file_list) > 1:
            #print('DO THE MERGE ON: {}'.format(self.configs.merge_launches))
            #print(type(self.configs.merge_launches))
            if self.configs.merge_launches:
                #launch_list = rportal.launches.list
                g.log.debug('launches: %s', launch_list)
                merged_launch_id = rportal.launches.merge(merge_type='DEEP')
                return_obj["merged_launch"] = merged_launch_id

                #if merged_launch_id is None:
                #    # the merge failed. return launch list with error
                #    pass
        else:
            if self.configs.merge_launches:
                g.log.debug('MERGE SKIPPED: Cannot merge a single file')

        return_obj["launches"] = launch_list

        # Auto create a default dashboard with default filter and widget
        g.log.debug('AUTO_DASHBOARD: %s', self.configs.auto_dashboard)
        # TODO: refactor into Dashboard autocreate
        if self.configs.auto_dashboard:
            dashboard_obj = self.auto_create_dashboard(rportal)
            return_obj['auto_dashboard'] = dashboard_obj

        g.log.debug('RETURN OBJECT: %s', return_obj)
        return return_obj

    def auto_create_dashboard(self, rportal):
        """Auto-create a default dashboard with basic widgets and a filter"""
        dashboard_obj = {}
        widgets = []

        rp_dashboard = Dashboard(rportal)
        dashboard_id = rp_dashboard.create()
        dashboard_obj['id'] = dashboard_id

        # Create a filter
        filter_obj = {}
        rp_filter = Filter(rportal)

        filter_id = rp_filter.create()
        filter_obj['id'] = filter_id

        # Create a widget
        widget_obj = {}
        rp_widget = WidgetLaunchesTable(rportal, filter_id=filter_id)
        widget_id = rp_widget.create()
        g.log.debug('WIDGET_ID from PREPROC: %s', widget_id)
        widget_obj['id'] = widget_id
        widget_obj['filter'] = filter_obj
        widgets.append(widget_obj)

        # Add the widget to the dashboard
        rp_dashboard.add_widget(widget_id)

        # Create a widget
        widget2_obj = {}
        rp_widget2 = WidgetOverallStats(rportal, filter_id=filter_id)
        widget2_id = rp_widget2.create()
        widget2_obj['id'] = widget2_id
        widget2_obj['filter'] = filter_obj
        widgets.append(widget2_obj)

        # Add the widget to the dashboard
        rp_dashboard.add_widget(widget2_id, size=20)

        dashboard_obj['widgets'] = widgets

        # Get the dashboard URL
        dashboard_obj['url'] = rp_dashboard.url
        #return_obj['auto_dashboard'] = dashboard_obj

        g.log.debug('DASHBOARD OBJECT: %s', dashboard_obj)
        return dashboard_obj


class PreProcClient(PreProc):
    """PreProc client class for preprocessing test results for ReportPortal"""
    def __init__(self, args):
        super().__init__(args)

        self._configs = Configs(args)


class PreProcService(PreProc):
    """PreProc service class for preprocessing test results for ReportPortal"""
    def __init__(self, args):
        super().__init__(args)

        # handle uploaded config file
        uploaded_config_file = self._args.get('config_file', None)
        if uploaded_config_file is not None:
            # read the config into an object
            configfile = \
                PreProcService.jsonfile_to_object(uploaded_config_file)
            self._configs = Configs(args, config=configfile)

        self._url = None

        # generate a uuid for temp use
        rppp_uuid = uuid.uuid1()
        self.tmp_dir = os.path.join('/tmp', 'rppp_{}'.format(rppp_uuid.hex))
        os.mkdir(self.tmp_dir)

        # handle payload
        uploaded_payload_file = self._args.get('payload_file', None)
        g.log.debug('uploaded_payload_file: %s', uploaded_payload_file)
        tmp_payload_dir = os.path.join(self.tmp_dir,
                                       'uploaded_rp_preproc_results')
        if uploaded_payload_file is not None:
            tmp_payload_filepath = \
                PreProcService.save_uploaded_file(uploaded_payload_file,
                                                  self.tmp_dir)
            PreProcService.untar_file(tmp_payload_filepath, tmp_payload_dir)

        self.configs.payload_dir = tmp_payload_dir
        self._payload_dir = tmp_payload_dir

        # save the config file in case it's needed later
        PreProcService.save_uploaded_file(uploaded_config_file,
                                          tmp_dir=tmp_payload_dir)

    @staticmethod
    def save_uploaded_file(uploaded_file, tmp_dir='/tmp'):
        """Save a file uploaded via REST API"""
        # TODO: move this to a REST API helper class/module
        filename = uploaded_file.filename
        filepath = os.path.join(tmp_dir, 'uploaded_{}'.format(filename))
        g.log.debug('save uploaded filepath: %s', filepath)
        uploaded_file.save(filepath)
        uploaded_file.close()

        # TODO: add DEBUG output
        # TODO: log error and/or raise exception
        if os.path.exists(filepath):
            return filepath

        return None

    @staticmethod
    def untar_file(tar_filepath, destination_path):
        """Untar a file"""
        # TODO: move this to a REST API helper class/module
        tar = tarfile.open(tar_filepath)
        tar.extractall(path=destination_path)
        tar.close()

        if os.path.exists(destination_path):
            return destination_path

        return None

    @staticmethod
    def jsonfile_to_object(config_file):
        """Load json from file into object"""
        # TODO: move this to a REST API helper class/module
        config_string = config_file.read()
        config_json = config_string.decode('utf8').replace("'", '"')
        g.log.debug(config_json)
        config = json.loads(config_json)

        return config

    def cleanup_tmp(self):
        """Cleanup temp dirs/files"""
        # remove temp client dir
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
