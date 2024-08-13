import logging
import os
import configparser
from datetime import datetime

import pika
import requests

from Utils.Api.Api import Api
from Utils.Common.Common import Common
from Utils.Common.Helpers import Helpers
from Utils.Rabbit import Rabbit
from Utils.Web.Web import Web
from Utils.Common.Logger import initialise_logger, filter_logs
from Utils.Models.Repository import *


def run_test(steps, data, algorithms, rabbit, config):
    sorted_steps = sorted(steps, key=lambda x: x['stepOrder'])
    test_duration = 0
    step_failed = False
    test_status = 'PASS'

    last_page = [page for page in sorted_steps if page['subType'] == 'page']
    last_page = last_page[-1]['id'] if len(last_page) else -1
    last_component = [component for component in sorted_steps if component['subType'] == 'component']
    last_component = last_component[-1]['id'] if len(last_component) else -1
    last_endpoint = [endpoint for endpoint in sorted_steps if endpoint['tech'] == 'API']
    last_endpoint = last_endpoint[-1]['id'] if len(last_endpoint) else -1

    last_node = -1
    category_name = data.data['category']['technical_name'].split('-')[0]
    if category_name == 'ACCESS_DENIED':
        last_node = last_page
    elif category_name in ['OPPOSITE_RULES', 'MISSING_VALUES', 'WRONG_DATA_TYPES']:
        last_node = last_page
    elif category_name == 'WRONG_ACTOR':
        # TODO: we should determine when the login/register is done
        last_node = 0
    failed_on_category = False

    print(f'Category: {data.data["category"]["friendly"]}')

    for test_index, test_step in enumerate(sorted_steps):
        technology = test_step['tech']
        message_properties = pika.BasicProperties(message_id='TEST_STEP_FINISHED',
                                                  headers={'suiteId': data.info["suiteId"]})
        payload_properties = {
            'stepId': test_step['id'],
            'suiteId': data.info['suiteId'],
            'testId': test_step['testQalityId'],
            'pathId': data.info['pathId'],
            'categoryId': data.info['testCategoryId'],
        }

        payload = {
            'duration': 0,
            'startTime': int(datetime.now().timestamp()),
            'endTime': int(datetime.now().timestamp()),
            'friendly': f"{test_step['friendly']}",
            'entityId': test_step['entityId'],
            'stepOrder': test_step['stepOrder'],
            'inputParamValues': {'header': {}, 'body': {}},
            'bodyOutput': {'header': {}, 'body': {}},
            'status': 'IN_PROGRESS' if not step_failed else 'SKIPPED',
            'errorMessage': '',
            'runEnvironment': {}
        }

        # if the previous step failed, skip this one
        if step_failed:
            payload['errorMessage'] = ''
            rabbit.publish_message(payload, payload_properties, message_properties)
            continue

        try:
            if technology == 'API':
                path_node = Endpoints.get(id=test_step['entityId'])
                last_node = last_endpoint
            elif technology == 'WEB' and test_step['subType'] == 'page':
                path_node = Pages.get(id=test_step['entityId'])
            elif technology == 'WEB' and test_step['subType'] == 'component':
                path_node = Components.get(id=test_step['entityId'])
            elif technology == 'WEB' and test_step['subType'] in ['button', 'input']:
                path_node = InputAttributes.get(id=test_step['entityId'])
            elif technology == 'WEB' and test_step['subType'] == 'element_group':
                if 'Custom' in test_step['friendly']:
                    continue
                path_node = ElementsGroups.get(id=test_step['entityId'])
            else:
                continue
            path_node.subType = test_step['subType']
            path_node.actor = test_step['actor']
            path_node.level = test_step['level']
            path_node.desiredAttributes = test_step['desiredAttributes'] if 'desiredAttributes' in test_step else []

            if technology == 'WEB':
                if type(path_node) is InputAttribute or type(path_node) is ElementsGroup:
                    component = Components.get(id=path_node.componentId)
                    tech_id = component.technologyWebId
                else:
                    tech_id = path_node.technologyWebId

                algorithms[technology].drivers.create_driver(technology_id=tech_id,
                                                             level=path_node.level,
                                                             headless=config['DEFAULT'].get('HEADLESS', False),
                                                             suite_id=data.info['suiteId'],
                                                             test_id=data.info['id'])
        except Exception as e:
            step_failed = True
            test_status = 'SKIPPED'
            payload['errorMessage'] = e

        # if the previous step failed, skip this one
        if step_failed:
            rabbit.publish_message(payload, payload_properties, message_properties)
            continue

        try:
            # test current node
            payload = algorithms[technology].test_node(
                path_node=path_node,
                report_step=payload,
                last_node=True if (last_node != -1 and test_step['id'] >= last_node) else False,
                test_index=test_index,
                test_step=test_step
            )
            if payload['status'] == 'FAIL':
                raise Exception()
        except Exception as e:
            if last_node != -1 and test_step['id'] >= last_node and data.data['category']['outcome'] == 'NEGATIVE':
                failed_on_category = True
                payload['status'] = 'PASS'
                payload['errorMessage'] = str(e)
                # skip the remaining steps
                step_failed = True
            else:
                step_failed = True
                test_status = 'FAIL'
                payload['status'] = 'FAIL'
                payload['errorMessage'] = str(e)
                algorithms['WEB'].drivers.close_drivers()
        finally:
            test_duration += payload['duration']
            rabbit.publish_message(payload, payload_properties, message_properties)

    if data.data['category']['outcome'] == 'NEGATIVE' and test_status == 'PASS' and not failed_on_category:
        test_status = 'FAIL'
    return test_status, test_duration


def code_generator_main(output_file_name=None):
    initialise_logger()
    filter_logs()

    config = configparser.ConfigParser()
    config.read(os.path.join(os.path.dirname(__file__), 'config.env'))

    # helper classes
    if not output_file_name:
        output_file_name = 'output.json'

    data = Helpers(output_file_name)
    data.info['dirty_browser'] = False  # TODO: manareala
    algorithms = {
        'API': Api(data),
        'WEB': Web(data, config)
    }
    common = Common(data)

    # create rabbit connection
    rabbit = Rabbit()
    rabbit.load_config(config, data.info["suiteId"])
    rabbit.create_connection()

    # populate data frame
    data.populate_data_type_method()
    data.cast_attribute_value_to_object()

    # send test started message
    message_properties = pika.BasicProperties(message_id='TEST_STARTED', headers={'suiteId': data.info["suiteId"]})
    payload = {
        'duration': 0,
        'status': 'IN_PROGRESS'
    }
    payload_properties = {
        'stepId': 0,
        'suiteId': data.info["suiteId"],
        'testId': data.info["id"],
        'pathId': data.info["pathId"],
        'categoryId': data.info["testCategoryId"],
    }
    rabbit.publish_message(payload, payload_properties, message_properties)

    # run test and get the status and duration
    test_duration = 0
    try:
        test_status, test_duration = run_test(data.info['testSteps'], data, algorithms, rabbit, config)
        # send the fulfilled requests payloads to WUI
        send_requests_payloads(algorithms, config)
    except (Exception,):
        test_status = 'FAIL'
        algorithms['WEB'].drivers.close_drivers()
        send_requests_payloads(algorithms, config)

    # send test result message
    message_properties = pika.BasicProperties(message_id='TEST_FINISHED', headers={'suiteId': data.info["suiteId"]})
    payload = {'status': test_status, 'duration': test_duration}
    rabbit.publish_message(payload, payload_properties, message_properties)

    # close rabbit connection
    rabbit.close_connection(data.info["id"])
    algorithms['WEB'].drivers.close_drivers()
    logging.debug("Test complete! Exiting container")


def get_auth_token(config):
    response = requests.post(
        f'{config["DEFAULT"]["WUI_URL"]}/api/login',
        json={
            "username": config["DEFAULT"]["WUI_USERNAME"],
            "password": config["DEFAULT"]["WUI_PASSWORD"]
        }
    )
    global wui_token
    wui_token = response.json()['token']
    return wui_token


def send_requests_payloads(algorithms, config):
    # for every fulfilled request, do a post to the server
    fulfilled_requests = algorithms['WEB'].fulfilled_requests
    if len(fulfilled_requests) == 0:
        return

    project_id = fulfilled_requests[0]['projectId']
    try:
        requests.post(
            f'{config["DEFAULT"]["WUI_URL"]}/api/projects/{project_id}/log/requests',
            json=fulfilled_requests,
            headers={
                'Authorization': f'Bearer {get_auth_token(config)}'
            },
            allow_redirects=False
        )
    except (Exception,) as e:
        logging.error(f'Could not post request /api/projects/{project_id}/requests, '
                      f'on url {os.getenv("WUI_URL")}/api/projects/{project_id}/requests. '
                      f'Error: {e}')
    return


# code_generator_main()
