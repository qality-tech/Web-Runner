import logging
import random
import shutil
import time
import platform
import psutil
import os

from Utils.Common.Common import Common
from Utils.Common.DataGenerators import DataGenerators
from Utils.Web.Handlers.Handlers import Handlers
from Utils.Web.Driver import Driver
from Utils.Common.RulesHandler import RulesHandler
from Utils.Web.Validators import Validators
from Utils.Models.Repository import *


class Web:
    h = None
    html_parent = None
    screenshots = []
    cursor = {
        'size': "6px",
        'color': 'red'
    }
    warnings = []
    inputParamValues = []
    bodyOutput = []
    missing_values = None
    actor = None
    level = 0
    last_node = False

    def __init__(self, helpers, config):
        self.h = helpers
        self.config = config
        self.url_string = ''
        self.drivers = Driver(self.h, config)
        self.driver = None
        self.pid = None
        self.dataGenerators = DataGenerators()
        self.rules_handler = RulesHandler(self.h, self)
        self.handlers = Handlers(self.h, self, self.rules_handler)
        self.validators = Validators(self.h, self.handlers, self)
        self.fulfilled_requests = []
        self.run_environment = {
            'os': platform.platform(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version(),
            'browser': self.config['DEFAULT'].get('BROWSER', 'chrome').lower(),
            'headless': self.config['DEFAULT'].get('HEADLESS', 'false').lower(),
            'partial_testing': self.config['DEFAULT'].get('PARTIAL_TESTING', 'false').lower(),
            'partial_testing_percent': self.config['DEFAULT'].get('PARTIAL_TESTING_PERCENT', 50),
            'slow_mode': self.config['DEFAULT'].get('SLOW_MODE', 'true').lower()
        }
        self.rules_reversed = False
        self.attribute_data_types_reversed = False
        self.current_node = 0
        self.current_actor_name = ''
        self.common = Common(self.h, self.rules_handler)

        # delete screenshots directory and recreate it if screenshots are enabled in config
        screenshots_path = os.path.join(os.path.dirname(__file__), '..', '..', 'screenshots')
        if os.path.exists(screenshots_path):
            shutil.rmtree(screenshots_path)
        if self.config['DEFAULT'].get('SCREENSHOTS', False) in ['True', 'true', '1', True] or \
                self.config['DEFAULT'].get('RECORDING', False) in ['True', 'true', '1', True]:
            os.makedirs(screenshots_path)

    def setup_url_attributes(self, url, base_url, page_id):
        """ Replaces parameters and query parameters in a given url.\n
            The resulted url is added to the attribute url_string of this class.

            Parameters
            ----------
            url: str
                page url
            page_id: number
                id of the page
        """

        self.url_string = url
        order_index = 1
        while True:
            try:
                url_attribute = UrlAttributes.get(pageId=page_id, orderIndex=order_index)
                attribute_value = self.h.get_attribute_or_main_attribute(url_attribute.attributeId, actor=self.actor).value
                if hasattr(url_attribute, 'type') and url_attribute.type.upper() == 'QUERY PARAM':
                    if url_attribute.queryParamKey is not None and len(url_attribute.queryParamKey) > 0:
                        attribute_value = url_attribute.queryParamKey + '=' + attribute_value
                self.url_string = self.url_string.replace('{' + str(order_index) + '}', str(attribute_value))
            except (Exception,):
                break
            order_index += 1

        if self.url_string.startswith('/'):
            self.url_string = self.url_string[1:]
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.url_string = f'{base_url}/{self.url_string}'

    @staticmethod
    def get_technology_id(path_node):
        if type(path_node) is InputAttribute or type(path_node) is ElementsGroup:
            return Components.get(id=path_node.componentId).technologyWebId
        return path_node.technologyWebId

    def test_node(self, path_node: Page | Component | ElementsGroup | InputAttribute, report_step, last_node, test_index, test_step):
        """ Tests a step from the testcase graph

            Parameters
            ----------
            path_node: dict
                the step data
            report_step: dict
                the object where the result will be placed

            Returns
            ---------
            dict
                the result of testing this step
        """

        if test_step['ignore_in_runner']:
            return self.return_passed_node(report_step)

        # TODO: improve this
        self.current_actor_name = test_step['friendly'].split('as ')[-1]

        self.screenshots = []
        self.inputParamValues = []
        self.bodyOutput = []
        self.current_node = test_index
        self.actor = int(path_node.actor) if type(path_node.actor) != int else path_node.actor
        self.level = int(path_node.level) if type(path_node.level) != int else path_node.level
        self.last_node = last_node

        if hasattr(path_node, 'technologyWebId'):
            self.h.update_naming_attributes(path_node.technologyWebId)
        elif type(path_node) == Component:
            tech_id = Components.get(id=path_node.id).technologyWebId
            self.h.update_naming_attributes(tech_id)

        tech_id = self.get_technology_id(path_node)
        self.driver = self.drivers.get_driver(tech_id, path_node.level)
        self.pid = self.drivers.get_pid(tech_id, path_node.level)
        self.drivers.recorder.window_title = self.driver.title

        self.missing_value_entity_id = None
        if last_node:
            if self.h.data['category']['technical_name'].split('-')[0] == 'ACCESS_DENIED':
                # clear cookies and storage in order to replicate a logout
                # may be replaced with calling the logout endpoint
                try:
                    self.drivers.delete_data(tech_id, path_node.level)
                except:
                    # there may be cases when this one fails when the page is not loaded properly
                    pass
            elif self.h.data['category']['technical_name'].split('-')[0] == 'OPPOSITE_RULES' and not self.rules_reversed:
                # reverse the rule of this category
                self.rules_handler.reverse_rule(self.h.data['category']['entityId'])
                self.rules_reversed = True
            elif self.h.data['category']['technical_name'].split('-')[0] == 'MISSING_VALUES':
                self.missing_value_entity_id = self.h.data['category']['entityId']
            elif self.h.data['category']['technical_name'].split('-')[0] == 'WRONG_DATA_TYPES' and not self.attribute_data_types_reversed:
                element_id = self.h.data['category']['entityId']
                element = InputAttributes.get(id=element_id)
                other_type_ids = DataTypes.get_all(friendly=['String', 'Date', 'Boolean', 'Number'])
                other_type_ids = [dataType.typeId for dataType in other_type_ids if dataType.typeId != element.attribute_type]
                SuiteAttributes.update(attributeId=element.attributeId,
                                       update_column=['fakerApiConfig', 'attribute_type'],
                                       update_value=[None, random.choice(other_type_ids)])
                self.attribute_data_types_reversed = True

        if path_node.subType == 'page':
            return self.test_page(path_node, report_step)
        elif path_node.subType in ['component', 'button', 'input', 'element_group']:
            return self.test_component(path_node, report_step)

    def test_page(self, path_node: Page, report_step):
        """ Tests a page from the testcase graph

            Parameters
            ----------
            path_node: dict
                the step data
            report_step: dict
                the object where the result will be placed

            Returns
            ---------
            dict
                the result of testing this step
        """

        # navigates to a page, if the page loads, the test is successful
        self.setup_url_attributes(path_node.relativeUrl, path_node.projectUrl, path_node.id)
        step_start_time = time.time()
        try:
            self.screenshots = []
            self.driver.get(self.url_string)

            # check if the redirect was made to the desired page
            start_time = time.perf_counter()
            same_url = False
            while (time.perf_counter() - start_time) <= 20:
                if self.sanitize_url(self.url_string) == self.sanitize_url(self.driver.current_url):
                    # try again in case there was a redirect done
                    time.sleep(3)
                    if self.sanitize_url(self.url_string) == self.sanitize_url(self.driver.current_url):
                        same_url = True
                        break
                else:
                    if (time.perf_counter() - start_time) > 10:
                        # try to get to the page again
                        self.driver.get(self.url_string)
                time.sleep(1 / 5)
            if not same_url:
                raise Exception(f'The redirect was made to {self.sanitize_url(self.url_string)} instead of {self.sanitize_url(self.driver.current_url)}')

            # Restore cookies for dirty browser
            if self.h.info.get('dirty_browser', False):
                try:
                    self.drivers.add_cookies(self.get_technology_id(path_node))
                except (Exception,):
                    pass

            # take a screenshot of the page
            self.drivers.recorder.window_title = self.driver.title
            self.take_page_screenshot()
            self.enable_cursor()
        except Exception as e:
            report_step['status'] = 'FAIL'
            raise Exception(f'Page {self.url_string} failed. Error: {e}')
        finally:
            report_step['duration'] = int((time.time() - step_start_time) * 1000)
            report_step['consoleLog'] = self.drivers.get_console_log(self.get_technology_id(path_node))
            report_step['screenshots'] = self.screenshots
            # report_step['screenshots'] = []
            report_step['inputParamValues'] = self.inputParamValues
            report_step['bodyOutput'] = self.bodyOutput
            report_step['runEnvironment'] = self.run_environment
            report_step['techSpec'] = self.get_browser_usage()
            logging.debug('Page test finished')

        report_step['status'] = 'PASS'
        return report_step

    def sanitize_url(self, url):
            if url.endswith('/'):
                url = url[:-1]
            url = url.replace('https://', '')
            url = url.replace('http://', '')
            url = url.split('?')[0]
            if url.endswith('/'):
                url = url[:-1]
            return url

    def test_component(self, path_node: Component | InputAttribute | ElementsGroup, report_step):
        """ Tests a component from the testcase graph

            Parameters
            ----------
            path_node: dict
                the step data
            report_step: dict
                the object where the result will be placed

            Returns
            ---------
            dict
                the result of testing this step
        """

        logging.debug(f'Start for\n{path_node}')
        step_start_time = time.time()

        # validate component and elements of this component
        try:
            self.screenshots = []
            if path_node.subType == 'element_group':
                self.validators.validate_element_group(path_node)
            elif path_node.subType == 'component':
                self.validators.validate_component(path_node)
            elif path_node.subType in ['button', 'input']:
                self.validators.validate_element(path_node)
        except Exception as e:
            report_step['status'] = 'FAIL'
            raise Exception(f'Component {path_node.friendly} failed. Error: {e}')
        finally:
            report_step['duration'] = int((time.time() - step_start_time) * 1000)
            report_step['consoleLog'] = self.drivers.get_console_log(self.get_technology_id(path_node))
            report_step['screenshots'] = self.screenshots
            # report_step['screenshots'] = []
            report_step['inputParamValues'] = self.inputParamValues
            report_step['bodyOutput'] = self.bodyOutput
            report_step['runEnvironment'] = self.run_environment
            report_step['techSpec'] = self.get_browser_usage()
            logging.debug('Component test finished')

        report_step['status'] = 'PASS'
        return report_step

    def return_passed_node(self, report_step):
        report_step['status'] = 'PASS'
        report_step['duration'] = 0
        report_step['screenshots'] = []
        report_step['inputParamValues'] = self.inputParamValues
        report_step['bodyOutput'] = self.bodyOutput
        report_step['runEnvironment'] = self.run_environment
        report_step['techSpec'] = self.get_browser_usage()
        return report_step

    def get_browser_usage(self):
        try:
            process = psutil.Process(self.pid)
            cpu = {
                'cpu_usage': f'{psutil.cpu_percent()}%',
                'cpu_cores': psutil.cpu_count(),
                'cpu_usage_per_cores': psutil.cpu_percent(percpu=True),
                'browser_cpu_usage': f'{process.cpu_percent() / float(psutil.cpu_count())}%',
                'browser_threads_number': process.num_threads()
            }

            virtual_memory_stats = psutil.virtual_memory()
            swap_memory_stats = psutil.virtual_memory()
            memory = {
                'virtual_memory_total': f'{round(virtual_memory_stats.total * pow(10, -9), 2)}GB',
                'virtual_memory_percent': f'{round(virtual_memory_stats.percent, 2)}%',
                'swap_memory_total': f'{round(swap_memory_stats.total * pow(10, -9), 2)}GB',
                'swap_memory_percent': f'{round(swap_memory_stats.percent, 2)}%',
                'browser_memory_usage': f'{round(process.memory_info().rss * pow(10, -9), 2)}GB',
                'browser_memory_percent': f'{round(process.memory_percent(), 2)}%'
            }

            network_stats = psutil.net_io_counters()
            network = {
                'bytes_sent': network_stats.bytes_sent,
                'bytes_received': network_stats.bytes_recv,
                'packets_sent': network_stats.packets_sent,
                'packets_received': network_stats.packets_recv,
                'packets_dropped_in': network_stats.dropin,
                'packets_dropped_out': network_stats.dropout
            }
            return {
                'cpu': cpu,
                'memory': memory,
                'network': network
            }
        except (Exception,):
            logging.error('Could not get browser hardware usage')
            return {}

    def enable_cursor(self):
        """ Draws a figure on the webpage that follows the position of the cursor. \n
            The size and color of the figure can be changed in the cursor attribute
            of this class.
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'mouse_script.txt')
            script = open(script_path).read() \
                .replace('$size', self.cursor['size']) \
                .replace('$color', self.cursor['color'])
            self.driver.execute_script(script)
        except (Exception,):
            print('Could not enable cursor')

    def take_page_screenshot(self):
        try:
            self.handlers.identify_element("//body", self.driver)
        except (Exception,):
            pass

    def validate_response(self):
        return self.validators.validate_response()
