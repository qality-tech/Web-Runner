import logging
import os

FORMAT = "%(levelname)-5s [%(asctime)s %(filename)s->%(funcName)s():%(lineno)s] %(message)s"
file_name = os.path.join(os.path.dirname(__file__), '..', '..', 'logging.log')
level = logging.DEBUG


def initialise_logger():
    logging.basicConfig(format=FORMAT, filename=file_name, filemode='w', encoding='utf-8', level=level)


def filter_logs():
    unwanted_libraries = ['requests', 'pika', 'faker', 'urllib3', 'selenium.webdriver.remote.remote_connection',
                          'selenium.webdriver.common', 'seleniumwire', 'hpack', 'dotenv']

    for library in unwanted_libraries:
        logging.getLogger(library).setLevel(logging.INFO)


