import psutil
import threading
import pickle
import subprocess
from getpass import getpass
from datetime import datetime

from selenium.webdriver import DesiredCapabilities
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from Utils.Web.Recorder import Recorder
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service


class Driver:
    def __init__(self, helpers, config):
        self.h = helpers
        self.config = config
        self.drivers = {}
        self.recorder = Recorder(config, self)
        self.cookies_added = {}
        self.current_driver = None
        self.current_pid = None
        self.trusted_certificate = False
        self.pids = {}
        self.browser = self.config['DEFAULT'].get('BROWSER', 'chrome').lower()

    def create_driver(self, technology_id, level, headless=True, suite_id=None, test_id=None):
        """ Creates and saves a chrome driver for the specified technology. \n
            There is created an instance for each technology, because different
            technologies are supposed to run in different instances of the browser. \n
            - if the 'REMOTE' env is set to 'True', the driver runs on a remote machine
            - if the 'DRIVER_PATH' env is set, the driver uses the chrome driver from the specified path,
              instead of getting the default one found on your system

            Parameters
            ----------
            technology_id: Number
                id of current steps' technology
            level: Number
            headless: String, optional
                True - the browser runs in the background
                False - an instance of the browser is opened
            suite_id: id of the suite, used to create the recording file
        """

        try:
            # if not self.trusted_certificate:
            #     self.trust_certificate()

            driver_identifier = f'{technology_id}_{level}'

            if len(self.drivers) == 0 and self.config['DEFAULT'].get('RECORDING', False) in ['True', 'true', '1', True]:
                recorder_thread = threading.Thread(target=self.recorder.start, name="Recorder", args=[
                    f'suite_{suite_id}_test_{test_id}.mp4'])
                recorder_thread.start()
            if self.drivers.get(driver_identifier):
                return

            options = self.init_driver_options(headless, self.browser)
            if self.browser == 'firefox':
                capabilities = DesiredCapabilities.FIREFOX
                capabilities["loggingPrefs"] = {"performance": "ALL", "browser": "ALL"}
            else:
                capabilities = DesiredCapabilities.CHROME
                capabilities["goog:loggingPrefs"] = {"performance": "ALL", "browser": "ALL"}

            capabilities["acceptInsecureCerts"] = True

            if self.config['DEFAULT'].get('REMOTE', False) in ['True', 'true', '1', True]:
                self.drivers[driver_identifier] = webdriver.Remote(
                    command_executor=self.config['DEFAULT'].get('DOCKER_BROWSER'),
                    options=options,
                    desired_capabilities=capabilities)
                return

            if self.browser == 'chrome':
                try:
                    self.drivers[driver_identifier] = webdriver.Chrome(
                        options=options,
                        desired_capabilities=capabilities,
                        service=Service(ChromeDriverManager().install()))
                except (Exception,):
                    self.drivers[driver_identifier] = webdriver.Chrome(
                        options=options,
                        desired_capabilities=capabilities)
            elif self.browser == 'firefox':
                try:
                    self.drivers[driver_identifier] = webdriver.Firefox(
                        options=options,
                        desired_capabilities=capabilities,
                        service=Service(GeckoDriverManager().install()))
                except (Exception,):
                    self.drivers[driver_identifier] = webdriver.Firefox(
                        options=options,
                        desired_capabilities=capabilities)

            self.set_driver_pid(driver_identifier)

        except Exception as e:
            raise Exception(f'Something went wrong. Cannot initialize chrome driver, make sure that it is installed. '
                            f'Error: {e}')

    @staticmethod
    def init_driver_options(headless, browser='chrome'):
        if type(headless) != bool:
            headless = headless.lower() in ('true', '1')

        options = ChromeOptions()
        if browser == 'firefox':
            options = FirefoxOptions()

        if headless:
            options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--password-store=basic")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--enable-automation")
        options.add_argument("--disable-browser-side-navigation")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-setuid-sandbox")
        options.add_argument("--disable-software-rasterizer")
        return options

    def get_driver(self, technology_id, level):
        driver_identifier = f'{technology_id}_{level}'
        self.current_driver = self.drivers[driver_identifier]
        return self.drivers[driver_identifier]

    def get_pid(self, technology_id, level):
        driver_identifier = f'{technology_id}_{level}'
        self.current_pid = self.pids[driver_identifier]
        return self.pids[driver_identifier]

    def set_driver_pid(self, driver_identifier):
        try:
            browser = self.drivers[driver_identifier]
            if self.browser == 'firefox':
                self.pids[driver_identifier] = browser.service.process.pid
            else:
                self.pids[driver_identifier] = psutil.Process(browser.service.process.pid)
        except (Exception,):
            return None

    def close_driver(self, driver_identifier):
        self.save_cookies(driver_identifier)
        if self.drivers.get(driver_identifier):
            self.drivers[driver_identifier].quit()

    def close_drivers(self):
        self.recorder.stop()
        for key in self.drivers.keys():
            self.close_driver(key)

    def trust_certificate(self):
        # mac os
        command = "sudo -S security add-trusted-cert -d -r trustRoot " \
                  "-k /Library/Keychains/System.keychain ca.crt".split()
        password = getpass("Please enter your system password to import chrome certificates: ")
        subprocess.run(
            command, stdout=subprocess.PIPE, input=password, encoding="ascii",
        )
        self.trusted_certificate = True

    def get_console_log(self, technology_id):
        try:
            return self.drivers[technology_id].get_log('browser')
        except (Exception,):
            return []

    def add_cookies(self, technology_id):
        if self.cookies_added.get(technology_id, False):
            return

        if self.h.info.get('dirty_browser', False):
            try:
                cookies = pickle.load(open(f'{technology_id}_cookies.pkl', "rb"))
                for cookie in cookies:
                    self.drivers[technology_id].add_cookie(cookie)
                self.cookies_added[technology_id] = True
            except (Exception,):
                return

    def save_cookies(self, driver_identifier):
        if self.h.info.get('dirty_browser', False) and self.drivers.get(driver_identifier):
            pickle.dump(self.drivers[driver_identifier].get_cookies(), open(f'{driver_identifier}_cookies.pkl', 'wb'))

    def delete_data(self, technology_id, level):
        driver_identifier = f'{technology_id}_{level}'
        driver = self.drivers[driver_identifier]
        driver.delete_all_cookies()
        driver.execute_script('window.localStorage.clear();')
        driver.execute_script('window.sessionStorage.clear();')
