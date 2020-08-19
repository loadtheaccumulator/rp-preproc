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
"""ReportPortal class for RP PreProc client and service"""
import json
from mimetypes import guess_type
import os
import posixpath
import re
import time
import uuid
from zipfile import ZipFile

import requests
import urllib3

from glusto.core import Glusto as g
from reportportal_client import ReportPortalService


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# pylint: disable=too-many-instance-attributes, too-many-arguments
#         reviewed and disabled
class ReportPortal:
    """ReportPortal class to assist with RP API calls"""
    def __init__(self, config, endpoint=None, api_token=None, project=None,
                 merge_launches=None, rpuid=None):
        """Create a ReportPortal client instance

        Args:
            config (str): the reportportal config section from file
        """
        self._rpuid = rpuid
        self._service = None
        self._config = config
        self._endpoint = endpoint
        self._api_token = api_token
        self._project = project
        self._merge_launches = merge_launches
        self._launches = Launches(self)

    @property
    def rpuid(self):
        """get the unique id of this instance"""
        if self._rpuid is None:
            self._rpuid = uuid.uuid1().hex

        return self._rpuid

    @property
    def config(self):
        """get the rp section json object"""
        # TODO: add validation for required elements

        return self._config

    @property
    def endpoint(self):
        """get endpoint"""
        if self._endpoint is None:
            self._endpoint = self.config.get('host_url',
                                             os.environ.get('RP_HOST_URL',
                                                            None))
        # TODO: raise exception on endpoint is still None
        return self._endpoint

    @property
    def api_token(self):
        """Get the user api_token"""
        if self._api_token is None:
            self._api_token = self.config.get('api_token',
                                              os.environ.get('RP_API_TOKEN',
                                                             None))
        # TODO: validate api_token is not None
        # TODO: validate api_token works ???
        return self._api_token

    @property
    def project(self):
        """project attr getter"""
        if self._project is None:
            self._project = self.config.get('project',
                                            os.environ.get('RP_PROJECT', None))

        return self._project

    @property
    def service(self):
        """get service"""
        # creating service on first call to get service
        if self._service is None:
            self._service = ReportPortalService(endpoint=self.endpoint,
                                                project=self.project,
                                                token=self.api_token)
            self._service.session.verify = False

            # TODO: validate the service works

        return self._service

    @property
    def launches(self):
        """launch list attr getter"""
        return self._launches

    @property
    def merge_launches(self):
        """Should launches be merged?"""
        if self._merge_launches is None:
            self._merge_launches = self.config.get('merge_launches', False)

        g.log.debug('ReportPortal.merge_launches: %s', self._merge_launches)
        return self._merge_launches

    @merge_launches.setter
    def merge_launches(self, merge_launches_value):
        """Override merge_launches setting"""
        self._merge_launches = merge_launches_value

    @property
    def launch_config(self):
        """launch_config attr gettr"""
        launch_config = Launch.get_config(self.config)

        return launch_config

    def api_put(self, api_path, put_data=None, verify=False):
        """PUT to the ReportPortal API"""
        url = posixpath.join(self.endpoint, 'api/v1/', self.project, api_path)
        g.log.debug('url: %s', url)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(self.api_token)
        session.headers["Content-type"] = "application/json"
        session.headers["Accept"] = "application/json"
        response = session.put(url, data=json.dumps(put_data),
                               verify=verify)

        g.log.debug('r.status_code: %s', response.status_code)
        g.log.debug('r.text: %s', response.text)

        return response

    def api_get(self, api_path, get_data=None, verify=False):
        """GET from the ReportPortal API

        Args:
            get_data (list): list of key=value pairs

        Returns:
            session response object
        """
        url = posixpath.join(self.endpoint, 'api/v1/',
                             self.project, api_path)
        if get_data is not None:
            get_string = '?{}'.format("&".join(get_data))
            url += get_string
        g.log.debug('url: %s', url)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(self.api_token)
        session.headers["Accept"] = "application/json"

        response = session.get(url, verify=verify)

        g.log.debug('r.status_code: %s', response.status_code)
        g.log.debug('r.text: %s', response.text)

        return response

    def api_post(self, api_path, post_data=None, filepath=None, verify=False):
        """POST to the ReportPortal API"""
        url = posixpath.join(self.endpoint, 'api/v1/', self.project, api_path)
        g.log.debug('url: %s', url)

        session = requests.Session()
        session.headers["Authorization"] = "bearer {0}".format(self.api_token)

        if filepath is None:
            session.headers["Content-type"] = "application/json"
            session.headers["Accept"] = "application/json"
            response = session.post(url, data=json.dumps(post_data),
                                    verify=verify)
        else:
            files = {'file': open(filepath, 'rb')}
            response = session.post(url, data={}, files=files, verify=False)

        g.log.debug('r.status_code: %s', response.status_code)
        g.log.debug('r.text: %s', response.text)

        return response

    def api_post_zipfile(self, infile, outfile='/tmp/myresults.zip'):
        """POST a single zip file to the ReportPortal API"""
        with ZipFile(outfile, 'w') as zipit:
            zipit.write(infile)
        api_path = 'launch/import'

        response = self.api_post(api_path, filepath=outfile)

        try:
            response_json = response.json()
            g.log.debug('r.json: %s', response_json)
            idregex = re.match('.*id = (.*) is.*', response_json['msg'])
            launch_id = idregex.group(1)
            g.log.debug('Launch id from xml import: %s', launch_id)
            self.launches.add(launch_id)

            return response_json
        except json.JSONDecodeError:
            return_response = response.text
            g.log.debug('r.text: %s', return_response)

        return None


class Launches:
    """Class to handle multiple launches"""
    def __init__(self, rportal):
        self._rportal = rportal
        self._list = []

    @property
    def list(self):
        """Get the list of launches"""
        return self._list

    def add(self, launch_id):
        """Add a launch to the list"""
        self.list.append(launch_id)

    def merge(self, name='Merged Launch', description='merged launches',
              merge_type='BASIC'):
        """Merge all launches in the list into one launch"""
        g.log.debug('merging launches: %s', self.list)

        name = self._rportal.launch_config.get('name', name)
        description = self._rportal.launch_config.get('description',
                                                      description)
        post_merge_json = {"description": description,
                           "extendSuitesDescription": True,
                           "launches": self.list,
                           "merge_type": merge_type,
                           "mode": "DEFAULT",
                           "name": name}
        api_path = 'launch/merge'
        response = self._rportal.api_post(api_path, post_data=post_merge_json)

        try:
            return_response = response.json()
            g.log.debug('r.json: %s', return_response)
            merged_launch = (return_response['id'])
            g.log.debug('merged launch: %s', merged_launch)

            return merged_launch
        except json.JSONDecodeError:
            # TODO: chase down the specific json exception
            return_response = response.text
            g.log.debug('r.text: %s', return_response)

        return None


class Launch:
    """ReportPortal launch class"""
    @staticmethod
    def get_config(config):
        """Get the launch config section from a ReportPortal config"""
        launch_config = config.get('launch', None)

        return launch_config

    def __init__(self, rportal, name=None, description=None, tags=None):
        """Create an instance of ReportPortal launch class

        Args:
            rportal (obj): A ReportPortal class instance
            name (str): The name of the launch
            description (str): Information describing the launch
            tags (list): A list of tags to add to the launch
        """
        self._rportal = rportal
        self._service = rportal.service
        self._config = Launch.get_config(rportal.config)
        self._name = name
        self._tags = tags
        self._description = description
        self._start_time = None
        self._end_time = None
        self._launch_id = None

        g.log.debug('launch_name: %s', self.name)
        g.log.debug('launch_description: %s', self._description)
        g.log.debug('launch_tags: %s', self._tags)

    @property
    def name(self):
        """Get the name of the launch from config, env, etc."""
        if self._name is None:
            if self._config.get('merge_launches'):
                self._name = self._rportal.rpuid
            else:
                self._name = self._config.get('name',
                                              'RP PreProc Example Launch')

        return self._name

    @property
    def description(self):
        """Get the description of the launch from config, env, etc."""
        default = 'Example launch created by RP PreProc'
        if self._description is None:
            if self._config.get('merge'):
                self._description = self._config.get('name')
            else:
                self._description = self._config.get('description', default)

        return self._description

    @property
    def tags(self):
        """Get launch tags from the config"""
        if self._tags is None:
            self._tags = self._config.get('tags', None)

        return self._tags

    @property
    def start_time(self):
        """Get the launch start time"""
        if self._start_time is None:
            # TODO: get this from the config and default to NOW if None
            self._start_time = str(int(time.time() * 1000))

        return self._start_time

    @property
    def end_time(self):
        """Get the launch end time"""
        if self._end_time is None:
            # TODO: get this from the config and default to NOW if None
            self._end_time = str(int(time.time() * 1000))

        return self._end_time

    def start(self, start_time=None):
        """Start a launch

        Args:
            start_time (str): Launch start time (default: None)

        Returns:
            launch_id (str) on success
            None on fail

        """
        if self._rportal.merge_launches:
            self._name += ' (part)'

        if start_time is not None:
            self._start_time = start_time

        g.log.debug('Starting launch %s @ %s', self.name, self.start_time)
        self._launch_id = \
            self._service.start_launch(name=self.name,
                                       start_time=self.start_time,
                                       tags=self.tags,
                                       description=self.description)
        g.log.debug('Started launch %s', self._launch_id)

        return self._launch_id

        # TODO: "requests.exceptions.HTTPError: 401 Client Error: "
        #       "Unauthorized for url: <https://reportportal.example.com/"
        #       "api/v1/myproject/launch "
        # TODO: UMB integration (here @ launch and start finish???)
        # TODO: set launch id class attr

    def finish(self, end_time=None):
        """Finish the launch"""
        if end_time is not None:
            self._end_time = end_time

        self._service.finish_launch(end_time=self.end_time)
        g.log.debug('time elapsed = %s - %s', self.end_time, self.start_time)
        time_elapsed = int(self.end_time) - int(self.start_time)
        self._rportal.launches.add(self._launch_id)
        g.log.debug('Finished launch')
        g.log.debug('Launch import completed in %s seconds', time_elapsed)

        # TODO: ERROR CHECKING and return the result
        return self._launch_id


class TestItem:
    """TestItem class for ReportPortal API"""
    def __init__(self, rportal):
        self.service = rportal.service

    def start(self):
        """Start a test item"""

    def finish(self):
        """Finish a test item"""

    # TODO: move the logic for this from the other class methods


class RpLog:
    """Log an event in ReportPortal.
    ReportPortal works with the concept of "logging" results"""
    def __init__(self, rportal):
        self.service = rportal.service

    def add_attachment(self, filepath):
        """Add an attachment to a testcase in ReportPortal"""
        filename = os.path.basename(filepath)
        g.log.debug('Attaching %s', filepath)
        with open(filepath, "rb") as file_handle:
            attachment = {
                "name": filename,
                "data": file_handle.read(),
                "mime": guess_type(filepath)[0]
            }
            self.service.log(str(int(time.time() * 1000)),
                             filename, "INFO", attachment)
        # FIXME: return True/False

    def add_attachments(self, fqpath, xml_name, tc_attach_dir):
        """Add attachments from testcase directory

        Args:
            fqpath (str): fullpath to attachments base dir
            xml_name (str): name from the xml file
            tc_attach_dir (str): testcase attachment subdirectory
        """
        basepath = os.path.join(fqpath, tc_attach_dir)
        xml_dirpath = os.path.join(fqpath, xml_name, tc_attach_dir)

        for dirpath in [xml_dirpath, basepath]:
            if os.path.exists(dirpath):
                for root, _, files in os.walk(dirpath):
                    for file in files:
                        file_name = os.path.join(root, file)
                        g.log.debug('file_name')
                        self.add_attachment(file_name)
        # FIXME: return list of attached files or None

    def add_message(self, message='N/A', level='INFO',
                    msg_time=None):
        """Log a message in ReportPortal"""
        if msg_time is None:
            msg_time = str(int(time.time() * 1000))
        self.service.log(time=msg_time,
                         message=message,
                         level=level)


class Filter:
    """ReportPortal Filter API class"""
    def __init__(self, rportal):
        self._rportal = rportal
        self._service = rportal.service
        self._config = rportal.config
        self._launch_config = Launch.get_config(rportal.config)
        self._launch_name = self._launch_config.get('name', 'RP PreProc ???')
        self._name = self._launch_name
        self._id = None
        self._data_template = \
            {
                "elements": [
                    {
                        "description": "RP PreProc Auto Filter",
                        "entities": [
                            {
                                "condition": "eq",
                                "filtering_field": "name",
                                "value": self._launch_name
                            }
                        ],
                        "is_link": False,
                        "name": self._name,
                        "selection_parameters": {
                            "orders": [
                                {
                                    "is_asc": False,
                                    "sorting_column": "start_time"
                                }
                            ],
                            "page_number": 1
                        },
                        "share": True,
                        "type": "launch"
                    }
                ]
            }

    def get_id_by_name(self):
        """Check for existing filter by name
        superadmin_personal/filter?filter.eq.name=<name>
        """
        api_path = 'filter'
        get_string = 'filter.eq.name={}'.format(self._name)
        response = self._rportal.api_get(api_path, get_data=[get_string])
        response_json = response.json()
        g.log.debug('GET FILTER ID BY NAME: %s', response_json)
        if response_json['content']:
            response_filter = response_json['content'][0]
            filter_id = response_filter['id']

            return filter_id

        return None

    def create(self, return_existing=True):
        """Create a Filter"""

        g.log.debug('----------------- FILTER')

        if return_existing:
            filter_id = self.get_id_by_name()

            if filter_id is not None:
                self._id = filter_id
                g.log.debug('RETURNING EXISTING FILTER: %s', self._id)
                return self._id

        api_path = 'filter'
        response = self._rportal.api_post(api_path,
                                          post_data=self._data_template)

        try:
            return_response = response.json()
            g.log.debug('r.json: %s', return_response)
            self._id = return_response[0]['id']
            g.log.debug('filter_id: %s', self._id)

            return self._id
        except json.JSONDecodeError:
            # TODO: chase down the specific json exception
            return_response = response.text
            g.log.debug('r.text: %s', return_response)

        return None


class Widget:
    """ReportPortal Widget API class"""
    def __init__(self, rportal, filter_id=None):
        self._rportal = rportal
        self._service = rportal.service
        self._config = rportal.config
        self._launch_config = Launch.get_config(rportal.config)
        self._launch_name = self._launch_config.get('name', 'RP PreProc ???')
        self._name = "{}-table".format(self._launch_name)
        self._filter_id = filter_id
        self._id = None
        self._data = None

    def get_id_by_name(self):
        """Check for existing filter by name
        superadmin_personal/filter?filter.eq.name=<name>
        """
        api_path = 'widget/shared/search'
        get_string = 'term={}'.format(self._name)
        response = self._rportal.api_get(api_path, get_data=[get_string])
        response_json = response.json()
        g.log.debug('GET WIDGET ID BY NAME: %s', response_json)
        if response_json['content']:
            response_widget = response_json['content'][0]
            widget_id = response_widget['id']
            g.log.debug('RETURNING EXISTING WIDGET: %s', widget_id)

            return widget_id

        return None

    def create(self, return_existing=True):
        """Create a Widget"""

        g.log.debug('----------------- WIDGET')

        if return_existing:
            widget_id = self.get_id_by_name()

            if widget_id is not None:
                self._id = widget_id
                return self._id

        g.log.debug('FILTER_ID: %s', self._filter_id)

        api_path = 'widget'
        response = self._rportal.api_post(api_path,
                                          post_data=self._data)

        try:
            return_response = response.json()
            g.log.debug('r.json: %s', return_response)
            self._id = return_response.get('id', None)
            g.log.debug('widget_id: %s', self._id)
            if self._id is None:
                g.log.error('widget_id is None')

            return self._id
        except json.JSONDecodeError:
            # TODO: chase down the specific json exception
            return_response = response.text
            g.log.error('r.text: %s', return_response)
        except KeyError:
            g.log.error('KeyError')

        return None


class WidgetLaunchesTable(Widget):
    """Create an Overall Stats Widget"""
    def __init__(self, rportal, filter_id=None):
        super().__init__(rportal, filter_id=filter_id)

        self._name = "{} Launches Table".format(self._launch_name)
        self._data = \
            {
                "content_parameters": {
                    "content_fields": [
                        "name",
                        "number",
                        "last_modified",
                        "status",
                        "statistics$defects$product_bug$PB001",
                        "statistics$defects$automation_bug$AB001",
                        "statistics$defects$system_issue$SI001",
                        "statistics$defects$to_investigate$TI001",
                        "tags",
                        "user",
                        "start_time",
                        "end_time",
                        "description",
                        "statistics$executions$total",
                        "statistics$executions$passed",
                        "statistics$executions$failed",
                        "statistics$executions$skipped"
                    ],
                    "gadget": "launches_table",
                    "itemsCount": 10,
                    "metadata_fields": [
                        "start_time"
                    ],
                    "type": "launches_table",
                    "widgetOptions": {
                        "filterName": [self._name]
                    }
                },
                "description": "RP PreProc Auto widget",
                "filter_id": self._filter_id,
                "name": self._name,
                "share": True
            }


class WidgetOverallStats(Widget):
    """Create an Overall Stats Widget"""
    def __init__(self, rportal, filter_id=None):
        super().__init__(rportal, filter_id=filter_id)

        self._name = "{} Overall Stats".format(self._launch_name)
        self._data = \
            {
                "content_parameters": {
                    "content_fields": [
                        "statistics$executions$total",
                        "statistics$executions$passed",
                        "statistics$executions$failed",
                        "statistics$executions$skipped",
                        "statistics$defects$product_bug$PB001",
                        "statistics$defects$automation_bug$AB001",
                        "statistics$defects$system_issue$SI001",
                        "statistics$defects$no_defect$ND001",
                        "statistics$defects$to_investigate$TI001"
                    ],
                    "gadget": "overall_statistics",
                    "itemsCount": 50,
                    "metadata_fields": [
                        "name",
                        "number",
                        "start_time"
                    ],
                    "type": "statistics_panel",
                    "widgetOptions": {
                        "viewMode": ["donut"],
                        "latest": []
                    }
                },
                "description": "RP PreProc Auto widget",
                "filter_id": self._filter_id,
                "name": self._name,
                "share": True
            }


class Dashboard:
    """ReportPortal Dashboard API class"""
    def __init__(self, rportal):
        self._rportal = rportal
        self._service = rportal.service
        self._config = rportal.config
        self._launch_config = Launch.get_config(rportal.config)
        self._launch_name = self._launch_config.get('name', 'RP PreProc ???')
        self._name = self._launch_name
        self._id = None

        self._data_template = \
            {
                "description": "RP PreProc Auto Dashboard",
                "name": self._name,
                "share": True
            }

    @property
    def url(self):
        """get dashboard url"""
        url = posixpath.join(self._rportal.endpoint, 'ui',
                             '#{}'.format(self._rportal.project),
                             'dashboard', self._id)

        return url

    def get_id_by_name(self):
        """Check for existing dashboard by name
        superadmin_personal/filter?filter.eq.name=<name>
        """
        api_path = 'dashboard/shared?page.size=300'
        response = self._rportal.api_get(api_path)
        response_json = response.json()
        g.log.debug('GET DASHBOARD ID BY NAME: %s', response_json)
        if response_json['content']:
            for dashboard in response_json['content']:
                dashboard_id = dashboard.get('id', None)
                dashboard_name = dashboard.get('name', None)
                if dashboard_name == self._name:
                    return dashboard_id

        return None

    def get_info_by_id(self):
        """Get info about dashboard using the id"""
        api_path = 'dashboard/{}'.format(self._id)
        response = self._rportal.api_get(api_path)
        response_json = response.json()
        g.log.debug('GET DASHBOARD ID BY NAME: %s', response_json)

        return response_json

    def create(self, return_existing=True):
        """Create a Dashboard"""

        g.log.debug('----------------- DASHBOARD')

        if return_existing:
            dashboard_id = self.get_id_by_name()

            if dashboard_id is not None:
                self._id = dashboard_id
                g.log.debug('RETURNING EXISTING DASHBOARD: %s', self._id)
                return self._id

        api_path = 'dashboard'
        response = self._rportal.api_post(api_path,
                                          post_data=self._data_template)

        try:
            return_response = response.json()
            g.log.debug('r.json: %s', return_response)
            self._id = return_response.get('id', None)
            g.log.debug('dashboard_id: %s', self._id)

            return self._id
        except json.JSONDecodeError:
            # TODO: chase down the specific json exception
            return_response = response.text
            g.log.error('r.text: %s', return_response)
        except KeyError:
            g.log.error('KeyError')

        return None

    def add_widget(self, widget_id, size=6):
        """Add a widget to the dashboard"""
        widget_data = {
            "addWidget": {
                "widgetId": widget_id,
                "widgetPosition": [0],
                "widgetSize": [size]
            },
            "description": "RP PreProc Auto Widget",
            "name": self._name,
            "share": True,
        }

        g.log.debug('WIDGET DATA: %s', widget_data)
        g.log.debug('BREAKPOINT 1')

        api_path = 'dashboard/{}'.format(self._id)
        dashboard_info = self.get_info_by_id()
        widgets = dashboard_info.get('widgets', None)
        g.log.debug(widgets)
        for widget in widgets:
            g.log.debug(widget)
            if widget.get('widgetId') == widget_id:
                g.log.debug('Widget %s already exists in Dashboard. SKIPPING.',
                            widget_id)
                return None

        g.log.debug('DASHBOARD add_widget api_path %s', api_path)
        response = self._rportal.api_put(api_path,
                                         put_data=widget_data)
        g.log.debug('ENTERING TRY')
        try:
            return_response = response.json()
            g.log.debug('r.json: %s', return_response)
            filter_id = return_response.get('id', None)
            g.log.debug('filter_id: %s', filter_id)

            return filter_id
        except json.JSONDecodeError:
            return_response = response.text
            g.log.error('r.text: %s', return_response)
        except KeyError:
            g.log.error('KeyError: %s', response.text)

        g.log.debug('EXITING TRY')

        return response.status_code
