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
"""xUnit XML class to handle xunit translation into ReportPortal calls"""
import os
import time

from glusto.core import Glusto as g
from rp_preproc.libs.reportportal import Launch, RpLog


class XunitXML:
    '''Class for processing the xUnit XML file for ReportPortal'''
    def __init__(self, rportal, name=None, configs=None, xml_data=None):
        self.rportal = rportal
        self.name = name
        self._configs = configs
        self.xml_data = xml_data

    @staticmethod
    def get_file_list(results_dir):
        """Get a list of XML results files from a directory"""
        # get list of xml result files
        result_file_list = []
        if os.path.exists(results_dir):
            for root, _, files in os.walk(results_dir):
                for thefile in files:
                    fqpath = os.path.join(root, thefile)
                    if os.path.splitext(fqpath)[1] == '.xml':
                        result_file_list.append(fqpath)
                        g.log.debug('fqpath %s', fqpath)

            return result_file_list

        return False

    def process(self):
        """Process xUnit XML data"""
        # override env var with config provided vars
        rp_host_url = os.environ.get('RP_HOST_URL', None)
        g.log.debug('rp_host_url: %s', rp_host_url)

        # Start a launch
        launch = Launch(self.rportal)
        launch_id = launch.start()

        # check for multiple testsuites in xUnit
        if self.xml_data.get('testsuites'):
            # get test suites list
            testsuites_object = self.xml_data.get('testsuites')
            testsuites = testsuites_object.get('testsuite') \
                if isinstance(testsuites_object.get('testsuite'), list) \
                else [testsuites_object.get('testsuite')]
        else:
            testsuites = [self.xml_data.get('testsuite')]

        # create testsuite(s)
        g.log.debug('Processing %s testsuite(s)', len(testsuites))
        for testsuite in testsuites:
            testcases = testsuite.get('testcase')
            if not isinstance(testcases, list):
                testcases = [testcases]
            tsuite = TestSuite(self.rportal, self.name, testsuite)
            tsuite.start()

            # create all testcases
            g.log.debug('Starting testcases')
            for testcase in testcases:
                tcase = TestCase(self.rportal, self.name, testcase,
                                 configs=self._configs)
                tcase.start()
                tcase.finish()

            g.log.debug('\nFinished testcases')

            tsuite.finish()

        # Finish the launch
        launch.finish()

        return {'launch_id': launch_id}, 200


# pylint: disable=too-few-public-methods
# TODO: remove pylint disable when this is built out
# TODO: build this out
class TestSuites:
    """Class to handle multiple TestSuites in an XML file"""
    def __init__(self, rportal, xml_name):
        pass


# pylint: disable=too-many-instance-attributes
#         reviewed and disabled
class TestSuite:
    """Class to handle TestSuite xUnit specific items"""
    def __init__(self, rportal, xml_name, testsuite):
        self.service = rportal.service
        self.xml_name = xml_name
        self.testsuite = testsuite
        self.name = testsuite.get('@name', testsuite.get('@id', 'NULL'))
        self.item_type = 'SUITE'
        self.num_failures = int(self.testsuite.get('@failures', '0'))
        self.num_errors = int(self.testsuite.get('@errors', '0'))
        if self.num_failures > 0 or self.num_errors > 0:
            self.status = 'FAILED'
        else:
            self.status = 'PASSED'

    def start(self):
        """Start a testsuite section in ReportPortal"""
        g.log.debug('Starting testsuite %s', self.name)
        self.item_id = self.service.start_test_item(
            name=self.name,
            start_time=str(int(time.time() * 1000)),
            item_type=self.item_type)

    def finish(self):
        """Finish a testsuite section in ReportPortal"""
        self.service.finish_test_item(self.item_id, end_time=str(int(time.time() * 1000)),
                                      status=self.status)
        g.log.debug('Finished testsuite %s', self.name)


class TestCase:
    """Class to handle xUnit TestCase conversion to ReportPortal API calls"""
    def __init__(self, rportal, xml_name, testcase, configs=None):
        self.service = rportal.service
        self.xml_name = xml_name
        self.testcase = testcase
        self._configs = configs
        self.tc_classname = testcase.get('@classname', '')
        self.tc_name = testcase.get('@name', testcase.get('@id', None))
        self.tc_time = testcase.get('@time')
        self.description = '{} time: {}'.format(self.tc_name, self.tc_time)
        self.status = 'PASSED'
        self.issue = None
        self.rplog = RpLog(rportal)

    def start(self):
        """Start a testcase in ReportPortal"""
        self.test_item_id = self.service.start_test_item(name=self.tc_name[:255],
                                     description=self.description,
                                     tags=['testtag1'],
                                     start_time=str(int(time.time() * 1000)),
                                     item_type='STEP')

        print(self.test_item_id)

        # Add system_out log.
        if self.testcase.get('system-out'):
            self.rplog.add_message(message=self.testcase.get('system-out'),
                                   level="INFO")

        # Indicate type of test case (skipped, failures, passed)
        if self.testcase.get('skipped'):
            self.issue = {"issue_type": "NOT_ISSUE"}
            self.status = 'SKIPPED'
            skipped_case = self.testcase.get('skipped')
            msg = skipped_case.get('@message', '#text') \
                if isinstance(skipped_case, dict) else skipped_case
            self.rplog.add_message(message=msg, level="DEBUG")
        elif self.testcase.get('failure') or self.testcase.get('error'):
            self.status = 'FAILED'
            failures = self.testcase.get('failure',
                                         self.testcase.get('error'))
            failures_txt = ""
            if isinstance(failures, list):
                for failure in failures:
                    msg = failure.get('@message', failure.get('#text')) \
                        if isinstance(failure, dict) else failure
                    failures_txt += \
                        '{msg}\n'.format(msg=msg)
            else:
                failures_txt = failures.get('@message', failures.get('#text'))\
                    if isinstance(failures, dict) else failures

            self.rplog.add_message(message=failures_txt, level="ERROR")

            # handle attachments
            tc_attach_dir = '{}.{}'.format(self.tc_classname,
                                           self.tc_name)
            fqpath = os.path.join(self._configs.payload_dir, 'attachments')
            self.rplog.add_attachments(fqpath, self.xml_name, tc_attach_dir)
        else:
            self.status = 'PASSED'

    def finish(self):
        """Finish a testcase in ReportPortal"""
        self.service.finish_test_item(self.test_item_id,
                                      end_time=str(int(time.time() * 1000)),
                                      status=self.status,
                                      issue=self.issue)

# TODO: set actual status from xml data
