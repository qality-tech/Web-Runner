import json
import logging
import time

import pika
import requests


class Rabbit:
    def __init__(self):
        self.target_connection_params = None
        self.connection = None
        self.channel = None
        self.config = None

    def load_config(self, config, suite_id):
        self.config = config
        target_credentials = pika.credentials.PlainCredentials(
            username=config['DEFAULT']['LOCAL_RABBITMQ_SERVER_USERNAME'],
            password=config['DEFAULT']['LOCAL_RABBITMQ_SERVER_PASSWORD']
        )

        self.target_connection_params = pika.ConnectionParameters(
            host=config['DEFAULT']['LOCAL_RABBITMQ_SERVER_ADDRESS'],
            port=int(config['DEFAULT']['LOCAL_RABBITMQ_SERVER_PORT']),
            credentials=target_credentials,
            client_properties={'connection_name': f'APIRunner-{suite_id}'},
            heartbeat=0
        )

    def create_connection(self):
        # check if the rabbit server is running and if the connection is possible
        timeout = 120
        elapsed_time = 0
        freq = 3
        while elapsed_time <= timeout:
            try:
                host = self.config["DEFAULT"].get('LOCAL_RABBITMQ_SERVER_ADDRESS', 'localhost')
                port = self.config["DEFAULT"].get('LOCAL_RABBITMQ_ADMIN_PORT', '15672')
                response = requests.get(
                    url=f'http://{host}:{port}/api/queues/%2F/RUNNER',
                    auth=(
                        self.config['DEFAULT'].get('LOCAL_RABBITMQ_SERVER_USERNAME', 'guest'),
                        self.config['DEFAULT'].get('LOCAL_RABBITMQ_SERVER_PASSWORD', 'guest')
                    )
                )
                if response.status_code != 200:
                    raise Exception('Server not running or queues not initialized yet.')
                break
            except Exception as e:
                print(f'Could not connect to rabbitmq server. Error: {e}')
                time.sleep(freq)
                elapsed_time += freq
                continue

        self.connection = pika.BlockingConnection(self.target_connection_params)
        self.channel = self.connection.channel()
        print('Successfully connected to rabbitmq server.')

    def close_connection(self, test_id):
        self.channel.close()
        self.connection.close(reply_text=f'Test {test_id} finished.')

    def publish_message(self, payload, payload_properties, message_properties):
        body = {'payload': payload, 'payloadProperties': payload_properties}
        logging.debug(message_properties)

        self.channel.basic_publish(
            exchange='',
            routing_key=f'test-{payload_properties["testId"]}',
            properties=message_properties,
            body=json.dumps(body, allow_nan=True).encode('utf-8')
        )

        try:
            del body['payload']['consoleLog']
            del body['payload']['screenshots']
            del body['payload']['inputParamValues']
            del body['payload']['bodyOutput']
            del body['payload']['techSpec']
            del body['payload']['runEnvironment']
        except (Exception,):
            pass
        logging.debug(body)
        print(body)

    def publish_rm_test_finished_message(self, test_id):
        message_properties = pika.BasicProperties(message_id='TEST_FINISHED', headers={'suiteId': test_id})
        body = {'payload': {}, 'payloadProperties': {}}

        self.channel.basic_publish(
            exchange='TEST_STATUSES',
            properties=message_properties,
            routing_key='TEST_STATUSES',
            body=json.dumps(body, allow_nan=True).encode('utf-8')
        )
