import logging
import random
import time

import numpy as np
import pandas as pd
import requests

from Utils.Common.Fake import Fake
from Utils.Models.Repository import *
from Utils.Common.Common import Common
from Utils.Common.DataGenerators import DataGenerators
from Utils.Common.RulesHandler import RulesHandler
from Utils.Common.Meta import Meta


class Api:

    def __init__(self, helpers):
        self.list_of_header_prerequisites = []
        self.h = helpers
        self.actor = None
        self.rules_handler = RulesHandler(self.h, self)
        self.common = Common(self.h, self.rules_handler)
        self.dataGenerators = DataGenerators()
        self.url_string = ''
        self.category_entity_id = None
        self.category_entity_type = None
        self.category_validation = None
        self.meta = Meta(helpers, self)

    def valorize_url(self, url_attribute):
        logging.debug('Start')
        attributes = SuiteAttributes.get_all(attributeId=url_attribute['attributeId'], node_instance_index=1)
        if len(attributes) == 0:
            return
        value = attributes[0].attributeValue
        if (value is None or np.isnan(value)) and not url_attribute['isOptional']:
            raise Exception('Could not valorize mandatory attributes for url.')
        elif (value is None or np.isnan(value)) and url_attribute['isOptional']:
            return

        position = UrlAttributes.get_all(attributeId=url_attribute['attributeId'])
        if len(position) > 1:
            raise Exception('Multiple URL indexes have been returned. Check the condition')

        logging.debug(f'value - {value}')
        self.url_string = self.url_string.replace("{" + str(int(position[0].orderIndex)) + "}", value)
        logging.debug('End')

    @staticmethod
    def set_attributes_and_values_into_header_object(header_friendly, header_value, headers):
        if 'token' in header_friendly.lower():
            attribute_value = 'Bearer ' + header_value
            headers['Authorization'] = attribute_value
            logging.debug(f'value - {attribute_value}')
            return
        attribute_value = header_value
        headers[header_friendly] = attribute_value

    @staticmethod
    def set_attributes_and_values_into_body_object(data, attribute_friendly, attribute_value):
        data[attribute_friendly] = attribute_value

    def set_category(self, last_node):
        if not last_node:
            return
        if self.h.data['category']['technical_name'].split('-')[0] == 'OPPOSITE_RULES':
            rule_id_to_reverse = self.h.data['category']['entityId']
            self.rules_handler.reverse_rule(rule_id_to_reverse)
        if self.h.data['category']['technical_name'].split('-')[0] == 'URL_MISSING_VALUES':
            self.category_entity_id = self.h.data['category']['entityId']
            self.category_entity_type = 'url'
            self.category_validation = 'missing_values'
        elif self.h.data['category']['technical_name'].split('-')[0].split('_')[0] == 'HEADER':
            self.category_entity_id = self.h.data['category']['entityId']
            self.category_entity_type = 'header'
            category_name = self.h.data['category']['technical_name'].split('-')[0]
            self.category_validation = category_name.split('_', 1)[-1].lower()
        elif self.h.data['category']['technical_name'].split('-')[0].split('_')[0] == 'BODY':
            self.category_entity_id = self.h.data['category']['entityId']
            self.category_entity_type = 'body'
            category_name = self.h.data['category']['technical_name'].split('-')[0]
            self.category_validation = category_name.split('_', 1)[-1].lower()

    def test_node(self, path_node: Endpoint, report_step, last_node, test_index, test_step):
        logging.debug(f'Start for\n{path_node}')

        self.set_category(last_node)
        self.actor = int(path_node.actor) if type(path_node.actor) != int else path_node.actor
        self.h.update_naming_attributes(path_node.technologyApiId)
        self.url_string = self.setup_url_attributes(path_node)
        report_step['url'] = self.url_string
        headers = self.setup_request_headers(path_node)
        report_step['inputParamValues']['header'] = headers
        data = self.setup_request_parameters(path_node)
        report_step['inputParamValues']['body'] = data

        logging.debug(f'Will call {self.url_string}')
        step_start_time = time.time()
        try:
            current_request = requests.request(path_node.verb, self.url_string, json=data, headers=headers)
        except requests.exceptions.ConnectTimeout:
            raise Exception(f'{path_node.verb} request to {self.url_string} timed out.')
        finally:
            report_step['duration'] = int((time.time() - step_start_time) * 1000)
            logging.debug('Request finished')

        for key, value in current_request.headers.items():
            report_step['bodyOutput']['header'][key] = value
        report_step['bodyOutput']['body'] = current_request.json()

        if current_request.status_code != path_node.statusCode:
            raise Exception(f'Expected status code {path_node.statusCode} but got {current_request.status_code}')

        self.common.handle_request_response(path_node, current_request.json())
        report_step['status'] = 'PASS'
        logging.debug(f"End")
        return report_step

    def setup_request_parameters(self, endpoint: Endpoint):
        request_attributes = RequestAttributes.get_all(status_code_id=endpoint.id)
        data = self.construct_body(request_attributes, endpoint)
        return data

    def setup_url_attributes(self, endpoint: Endpoint):
        attributes_to_ignore = None
        if self.category_entity_type == 'url' and self.category_validation == 'missing_values':
            if self.category_entity_id is not None:
                attributes_to_ignore = [self.category_entity_id]

        all_possible_urls = self.h.valorize_endpoint_url(endpoint, actor=self.actor, attributes_to_ignore=attributes_to_ignore)
        if len(all_possible_urls) == 0:
            raise Exception('Could not valorize the URL')
        # get a random URL
        url = random.choice(all_possible_urls)
        # remove trailing slashes
        url = url.rstrip('/')
        return url

    def setup_request_headers(self, endpoint: Endpoint):
        headers = {}
        header_attributes = HeaderAttributes.get_all(status_code_id=endpoint.id)
        if header_attributes is None:
            return headers
        for header_attribute in header_attributes:
            # if the category is header missing value, skip this attribute
            if self.category_entity_type == 'header' and self.category_validation == 'missing_values':
                if self.category_entity_id is not None and self.category_entity_id == header_attribute.attributeId:
                    continue
            attribute_value = self.get_attribute_value_or_generate(endpoint, header_attribute, attribute_type='header')
            self.set_attributes_and_values_into_header_object(header_attribute.friendly, attribute_value, headers)
        return headers

    def get_attribute_value_or_generate(self, endpoint: Endpoint, attribute: HeaderAttribute | UrlAttribute | RequestAttribute, attribute_type=None, multiple=False):
        attribute_value = self.calculate_attribute_value(endpoint, attribute, attribute_type, multiple)
        meta = attribute.meta
        if pd.isnull(meta) or len(meta) == 0:
            return attribute_value
        return self.meta.handle_meta_attribute(meta, attribute_value, attribute.attributeId)

    def calculate_attribute_value(self, endpoint: Endpoint, attribute: HeaderAttribute | UrlAttribute | RequestAttribute, attribute_type=None, multiple=False):
        if self.category_entity_id == attribute.attributeId:
            # if the category is null values, return None
            if self.category_entity_type == attribute_type and self.category_validation == 'null':
                return None
            # if the category is empty values, return empty string
            if self.category_entity_type == attribute_type and self.category_validation == 'empty':
                if multiple:
                    return []
                return ''
            # if the category is wrong data type, return a value of a different data type
            if self.category_entity_type == attribute_type and self.category_validation == 'wrong_data_types':
                attribute_type = attribute.main_attribute_type if not pd.isnull(attribute.main_attribute_type) else 15670
                other_type_ids = DataTypes.get_all(friendly=['String', 'Date', 'Boolean', 'Number'])
                other_type_ids = [dataType.typeId for dataType in other_type_ids if dataType.typeId != attribute_type]
                random_type_id = random.choice(other_type_ids)
                if multiple:
                    return [DataTypes.get(typeId=random_type_id).method() for _ in range(random.randint(1, 10))]
                return DataTypes.get(typeId=random_type_id).method()

        # check if this attribute has to be generated or has to be taken from another source
        to_generate = self.check_if_attribute_needs_to_be_generated(endpoint, attribute, self.actor)

        if not to_generate:
            attribute_value = self.h.get_attribute_or_main_attribute(attribute.attributeId, actor=self.actor).value
            return self.cast_attribute_value(attribute, attribute_value)
        if pd.isnull(attribute.main_attribute_type):
            if multiple:
                return [DataTypes.get(typeId=15670).method() for _ in range(random.randint(1, 10))]
            return DataTypes.get(typeId=15670).method()

        properties = self.rules_handler.calculate_attributes_based_on_rules([attribute.ruleId])
        properties = properties[attribute.friendly] if properties is not None and attribute.friendly in properties else None
        if multiple:
            return [DataTypes.get(typeId=attribute.main_attribute_type).method(properties=properties) for _ in range(random.randint(1, 10))]
        return DataTypes.get(typeId=attribute.main_attribute_type).method(properties=properties)

    def cast_attribute_value(self, attribute: HeaderAttribute | UrlAttribute | RequestAttribute, attribute_value):
        if type(attribute_value) is Fake:
            attribute_value = attribute_value.value

        if attribute_value is None or (type(attribute_value) is str and len(attribute_value) == 0):
            return attribute_value

        primary_data_types = [*self.h.primary_data_types, self.h.enum_data_type]
        int_data_type = DataTypes.get(friendly='Number').typeId
        bool_data_type = DataTypes.get(friendly='Boolean').typeId

        if attribute.attributeType not in self.h.list_data_type and attribute.main_attribute_type in primary_data_types and type(attribute_value) is str:
            if attribute.main_attribute_type == int_data_type:
                return int(attribute_value)
            if attribute.main_attribute_type == bool_data_type:
                if attribute_value.lower() in ['True', 'true', '1']:
                    return True
                if attribute_value.lower() in ['False', 'false', '0']:
                    return False
        return attribute_value

    @staticmethod
    def check_if_attribute_needs_to_be_generated(endpoint: Endpoint, attribute: RequestAttribute | HeaderAttribute | UrlAttribute, actor):
        # if the attribute comes from the actor, it does not need to be generated
        attributes_from_actor = SuiteAttributes.get(attributeId=[attribute.attributeId, attribute.main_attribute_id], actor=actor)
        if attributes_from_actor:
            return False

        # if the attribute is an attribute desired by this node, it does not need to be generated
        if attribute.attributeId in endpoint.desiredAttributes or attribute.main_attribute_id in endpoint.desiredAttributes:
            return False

        # if the attribute is inherited, it does not need to be generated
        if hasattr(attribute, 'inherited') and attribute.inherited:
            return False
        return True


    def identify_request_attribute_in_main_dataframe(self, attribute):
        same_parent = ResponseAttributes.df['parentId'] == attribute['referenceObjectId']
        same_attribute = ResponseAttributes.df['attributeId'] == attribute['referenceAttribute']
        same_attribute_instance_index = ResponseAttributes.df['attribute_instance_index'] == \
                                        attribute['attribute_instance_index']
        same_node_instance_index = ResponseAttributes.df['node_instance_index_res'] == \
                                   attribute['node_instance_index']
        condition = (
                same_parent &
                same_attribute_instance_index &
                same_node_instance_index &
                same_attribute
        )
        if condition.sum() > 1:
            logging.debug('Too many rows returned by the condition')
        if condition.sum() == 0:
            logging.debug('No rows returned by the condition')
        else:
            return ResponseAttributes.df[condition]

    def construct_body(self, attributes: List[RequestAttribute | HeaderAttributes], endpoint: Endpoint):
        data = {}
        if len(attributes) == 0:
            return data

        attributes_created = {}
        max_depth = max([attribute.depth for attribute in attributes])
        while max_depth >= 0:
            for attribute in attributes:
                if attribute.depth == max_depth:
                    self.create_attribute(attribute, endpoint, attributes_created, attributes)
            max_depth -= 1

        # the attribute of depth 0 is the body itself
        body_attribute_id = [attribute.attributeId for attribute in attributes if attribute.depth == 0]
        if len(body_attribute_id) == 0:
            return data
        return attributes_created[body_attribute_id[0]]

    def create_attribute(self, attribute: RequestAttribute | HeaderAttribute, endpoint: Endpoint, attributes_created: dict, all_attributes):
        # if the category is body missing value, skip this attribute
        if self.category_entity_type == 'body' and self.category_validation == 'missing_values':
            if self.category_entity_id is not None and self.category_entity_id == attribute.attributeId:
                return

        primary_types = [*self.h.primary_data_types, self.h.enum_data_type]
        object_types = self.h.object_data_types
        list_types = self.h.list_data_type
        attribute_value = None

        # the attribute is primary or enum
        if attribute.main_attribute_type in primary_types and (attribute.attributeType in primary_types or attribute.attributeType in object_types):
            # check if the attribute has already been created
            if attribute.attributeId in attributes_created:
                attribute_value = attributes_created[attribute.attributeId]
            else:
                attribute_value = self.get_attribute_value_or_generate(endpoint, attribute, attribute_type='body')

        # the attribute is a list
        if attribute.attributeType in list_types:
            # a list of attributes
            if not pd.isnull(attribute.referenceAttribute):
                if attribute.referenceAttribute in attributes_created:
                    reference_attribute_value = attributes_created[attribute.referenceAttribute]
                else:
                    reference_attribute = RequestAttributes.get(attributeId=attribute.referenceAttribute)
                    self.create_attribute(reference_attribute, endpoint, attributes_created, all_attributes)
                    reference_attribute_value = attributes_created[attribute.referenceAttribute]
                attribute_value = [reference_attribute_value]

            # a list of objects
            if not pd.isnull(attribute.referenceObjectId) and pd.isnull(attribute.referenceAttribute):
                if attribute.referenceObjectId in attributes_created:
                    reference_object_value = attributes_created[attribute.referenceObjectId]
                else:
                    reference_object = RequestAttributes.get(attributeId=attribute.referenceObjectId)
                    self.create_attribute(reference_object, endpoint, attributes_created, all_attributes)
                    reference_object_value = attributes_created[attribute.referenceObjectId]
                attribute_value = [reference_object_value]

        # the attribute is an object
        if attribute.attributeType is None or (attribute.attributeType in object_types and attribute.main_attribute_type in object_types) or attribute.depth == 0:
            new_object = {}
            # child attributes
            for child_attribute in all_attributes:
                if child_attribute.parent_id == attribute.attributeId:
                    child_attribute_value = attributes_created[child_attribute.attributeId] if child_attribute.attributeId in attributes_created else None
                    child_attribute = RequestAttributes.get(attributeId=child_attribute.attributeId)
                    new_object[child_attribute.friendly] = child_attribute_value
            attribute_value = new_object

        attributes_created[attribute.attributeId] = attribute_value
