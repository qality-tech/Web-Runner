import configparser
import json
import threading
import os
import subprocess
import platform
import time
from contextlib import suppress

import pika
import requests
from retry import retry

import CodeGenerator
from Utils.Rabbit import Rabbit


class Starter:
    output_absolute_path = None
    suite_id = None
    config = None

    def __init__(self, config):
        self.config = config

    def configure_absolute_path(self, file_name):
        self.output_absolute_path = os.path.abspath(file_name)

    def save_file(self, payload):
        file_name = f"{CWD}/test-{payload['id']}.json"
        with open(file_name, "w") as output_file:
            json.dump(payload, output_file)
        self.configure_absolute_path(file_name)
        print(f'Saving {file_name}')
        return file_name


def setup_dependencies() -> None:
    global run_command

    print('Determine platform.')
    if platform.system() == 'Windows':
        venv_install_command = ['pip', 'install', 'virtualenv']
        venv_command = ['virtualenv', f'{CWD}\\venv']
        req_command = [f'{CWD}\\venv\\Scripts\\pip.exe', 'install', '-r', f'{CWD}\\requirements.txt']
        run_command = [f'{CWD}\\venv\\Scripts\\python.exe', f'{CWD}\\CodeGenerator.py']
    else:
        venv_install_command = None
        venv_command = ['python3', '-m', 'venv', f'{CWD}/venv']
        req_command = [f'{CWD}/venv/bin/pip', 'install', '-r', f'{CWD}/requirements.txt']
        run_command = [f'{CWD}/venv/bin/python3', f'{CWD}/CodeGenerator.py']

    print('Install virtual environment.')
    if venv_install_command:
        subprocess.run(venv_install_command, text=True, capture_output=True)
    print('Create virtual environment.')
    subprocess.run(venv_command, text=True, capture_output=True)
    print('Install dependencies.')
    subprocess.run(req_command, text=True, capture_output=True)
    print('Dependencies installed.')


@retry((pika.exceptions.AMQPConnectionError, pika.exceptions.ConnectionClosedByBroker), delay=5, jitter=(1, 3))
def await_suites_to_be_run():
    if blocked:
        return

    rabbit.create_connection()
    print("Listening.")
    rabbit.channel.basic_qos(prefetch_count=1)
    rabbit.channel.basic_consume(
        queue='RUNNER',
        consumer_tag=f'Runner_{config["DEFAULT"]["QUEUE_NAME"]}',
        on_message_callback=run_test,
        auto_ack=False
    )

    try:
        rabbit.channel.start_consuming()
    except KeyboardInterrupt:
        print("Keyboard interrupt. Stopping gently")
        rabbit.channel.stop_consuming()
        rabbit.channel.close()
        rabbit.connection.close(reply_text=f'Runner {config["DEFAULT"]["QUEUE_NAME"]} stopped.')
    # Do not recover on channel errors
    except pika.exceptions.AMQPChannelError as err:
        print("Caught a channel error: {}, stopping...".format(err))
        pass


def run_test(ch, method, properties, body):
    global blocked
    global run_command
    blocked = True
    ch.basic_ack(method.delivery_tag)
    print('Running test')
    payload = json.loads(body.decode('utf-8'))
    starter = Starter(config)
    file_name = starter.save_file(payload)

    print('Starting CodeGenerator.')
    t1 = threading.Thread(target=CodeGenerator.code_generator_main, args=(file_name,))
    t1.start()
    t1.join()
    print('Finished CodeGenerator.')

    with suppress(Exception):
        notify_rm_test_finished(payload['id'])

    blocked = False
    print('Test finished')


def notify_rm_test_finished(test_id):
    rabbit.publish_rm_test_finished_message(test_id)

print('Starting runner.')
config = configparser.ConfigParser()
CWD = os.path.dirname(os.path.realpath(__file__))
config.read(os.path.join(os.path.dirname(__file__), 'config.env'))

blocked = False
run_command = []

setup_dependencies()
rabbit = Rabbit()
rabbit.load_config(config, config['DEFAULT']['RUNNER_NAME'])

await_suites_to_be_run()
