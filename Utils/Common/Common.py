import logging

import numpy as np
import pandas as pd

from Utils.Models.Repository import *
from Utils.Common.Fake import Fake


class Common:
    attributes = None
    def __init__(self, helpers, rules_handler=None):
        self.h = helpers
        self.rules_handler = rules_handler
        self.actor = None

    def handle_request_response(self, endpoint: Endpoint, body, des_type="response", actor=None):
        global parent_instance_index
        parent_instance_index = 1

        # No object assigned to the response/request. Can be a utilitarian endpoint
        if des_type == 'response' and pd.isnull(endpoint.response_id):
            return
        if des_type == 'request' and pd.isnull(endpoint.request_id):
            return

        self.actor = actor
        self.attributes = self.get_request_response_attributes(endpoint, des_type)

        if endpoint.responseAsList:
            return self.handle_request_response_as_list(body)
        if type(body) == dict:
            return self.handle_request_response_as_object(body)

        logging.debug(f"The response is a {type(body)}")

    @staticmethod
    def get_request_response_attributes(endpoint: Endpoint, des_type, node_instance_index=1):
        payload_id = endpoint.response_id if des_type == 'response' else endpoint.request_id
        column_identifier = 'response_id' if des_type == 'response' else 'request_id'
        current_payload_id = SuiteAttributes.df[column_identifier] == payload_id
        current_status_code_id = SuiteAttributes.df['status_code_id'] == endpoint.id
        current_index = SuiteAttributes.df['node_instance_index'] == node_instance_index
        return SuiteAttributes.df[(current_payload_id & current_status_code_id & current_index)].copy()

    def handle_request_response_as_list(self, body):
        global parent_instance_index
        logging.debug("The response should be a list")
        if type(body) != list:
            raise Exception(f"Could not parse the response. It's not a list or a dict. It's a {type(body)}")

        attributes_to_duplicate = self.attributes[self.attributes['depth'] == 1]
        self.duplicate_list_attributes(
            dataframe_to_duplicate=attributes_to_duplicate,
            response_section=body,
            increment_parent=True
        )

        for response_section in body:
            attributes_to_duplicate['parent_instance_index'] = parent_instance_index

            logging.debug('Extracted dataframe attributes are:')
            logging.debug(attributes_to_duplicate[['friendly', 'referenceObjectId', 'referenceAttribute',
                                                   'attribute_instance_index',
                                                   'parent_instance_index']].to_json(orient='records', indent=3))

            self.handle_object_item(
                attributes_of_current_object=attributes_to_duplicate,
                response_instance=response_section,
                parent_instance_index=parent_instance_index)
            parent_instance_index += 1

    def handle_request_response_as_object(self, body, node_instance_index=1):
        logging.debug("The response is an object")
        self.handle_object_item(
            attributes_of_current_object=self.attributes[self.attributes['depth'] == 1],
            response_instance=body,
            parent_instance_index=node_instance_index
        )

    def identify_attributes_in_main_dataframe(self, attributes: pd.DataFrame) -> pd.DataFrame:
        if self.attributes.empty:
            raise Exception('No response attribute to identify.')

        output_structure = []
        attributes.apply(self.identify_attribute_in_main_dataframe, axis=1)
        if len(output_structure) > 0:
            return SuiteAttributes.df.loc[output_structure]

    def identify_attribute_in_main_dataframe(self, attribute_from_dataframe):
        same_attribute = SuiteAttributes.df['sc_attr_id'] == attribute_from_dataframe['sc_attr_id']
        same_parent_instance_index = SuiteAttributes.df['parent_instance_index'] == attribute_from_dataframe['parent_instance_index']
        same_attribute_instance_index = SuiteAttributes.df['attribute_instance_index'] == attribute_from_dataframe['attribute_instance_index']
        same_node_instance_index = SuiteAttributes.df['node_instance_index'] == attribute_from_dataframe['node_instance_index']
        same_actor = SuiteAttributes.df['actor'] == self.actor if self.actor is not None else True
        no_actor = SuiteAttributes.df['actor'].isnull()

        condition = (
                same_parent_instance_index &
                same_attribute_instance_index &
                same_node_instance_index &
                same_attribute &
                (same_actor | no_actor)
        )

        if condition.sum() == 0:
            logging.error('No rows returned by the condition')
            return None
        return condition

    def handle_object_item(self, attributes_of_current_object, response_instance, parent_instance_index):
        """
        Populates a copy of the dataframe which represents this response for a particular index.
        What can come here is {1:a, 2:[], 3:{}}

        :param attributes_of_current_object: row from the dataframe representing the current attribute
        :param response_instance: the JSON from the request's response
        :param parent_instance_index: which instance of attributes is this one
        :return:
        """
        logging.debug(f'Begin of {response_instance}. Index {parent_instance_index}')

        logging.debug('Handling primary objects')
        attributes_of_interest = attributes_of_current_object['main_attribute_type'].isin([*self.h.primary_data_types, self.h.enum_data_type])
        self.check_if_attributes_exist(attributes_of_current_object[attributes_of_interest], response_instance)
        if len(attributes_of_current_object[attributes_of_interest]) > 0:
            logging.debug(f'Number of attributes to set: {attributes_of_current_object[attributes_of_interest].shape[0]}')
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.extract_values(
                    response_instance,
                    attribute), axis=1)
            logging.debug(f'Number of attributes set: {self.count_response_attributes_with_values()}')
        else:
            logging.debug('No primary attributes to set')

        logging.debug('Handling lists and sets')
        attributes_of_interest = attributes_of_current_object['main_attribute_type'].isin([*self.h.list_data_type, self.h.set_data_type])
        self.check_if_attributes_exist(attributes_of_current_object[attributes_of_interest], response_instance)
        if len(attributes_of_current_object[attributes_of_interest]) > 0:
            logging.debug(f'Number of attributes to set: {attributes_of_current_object[attributes_of_interest].shape[0]}')
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.extract_values(
                    response_instance,
                    attribute), axis=1)
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.extract_values_from_object_of_type_list(
                    current_list_item=attribute,
                    response_section=response_instance[attribute['friendly']]), axis=1)
            logging.debug(f'Number of attributes set: {self.count_response_attributes_with_values()}')
        else:
            logging.debug('No lists to handle')

        logging.debug('Handling attributes referencing attributes from other objects')
        object_data_type = attributes_of_current_object['main_attribute_type'].isin(self.h.object_data_types)
        with_referenced_attribute = attributes_of_current_object['referenceAttribute'].notnull()
        attributes_of_interest = (object_data_type & with_referenced_attribute)
        self.check_if_attributes_exist(attributes_of_current_object[attributes_of_interest], response_instance)
        if len(attributes_of_current_object[attributes_of_interest]) > 0:
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.extract_values(
                    response_instance,
                    attribute), axis=1)
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
        else:
            logging.debug('No attributes referenced from other data objects to process')

        logging.debug('Handling attributes pointing to other object')
        attributes_of_interest = (object_data_type & ~with_referenced_attribute)
        self.check_if_attributes_exist(attributes_of_current_object[attributes_of_interest], response_instance)
        if len(attributes_of_current_object[attributes_of_interest]):
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.extract_values(
                    response_instance,
                    attribute), axis=1)
            attributes_of_current_object[attributes_of_interest].apply(
                lambda attribute: self.handle_object_item(
                    attributes_of_current_object=self.attributes[(self.attributes['parent_id'] == attribute['attributeId']) &
                                                                           (np.isnan(self.attributes['depth']) == False)],
                    response_instance=response_instance[attribute['friendly']],
                    parent_instance_index=parent_instance_index
                ),
                axis=1
            )
            logging.debug(f'Number of attributes already set: {self.count_response_attributes_with_values()}')
        else:
            logging.debug('No attributes pointing to another data objects to process')

        logging.debug(f'End iteration {parent_instance_index}')

    @staticmethod
    def check_if_attributes_exist(attributes_mapped, body):
        body_keys = list(body.keys())
        mapped_but_not_in_body = set()
        for i, attribute in attributes_mapped.iterrows():
            if attribute['isOptional']:
                continue
            if attribute['friendly'] not in body_keys:
                mapped_but_not_in_body.add(attribute['friendly'])

        if len(mapped_but_not_in_body) > 0:
            raise Exception(f"{mapped_but_not_in_body} mapped but not in {body}")

    @staticmethod
    def count_response_attributes_with_values():
        return SuiteAttributes.df[SuiteAttributes.df["attributeValue"].notnull()].shape[0]

    def extract_values(self, response: dict, attribute_from_dataframe: pd.DataFrame):
        if attribute_from_dataframe['isOptional'] and attribute_from_dataframe['friendly'] not in response:
            return

        logging.debug(f'Start for: {attribute_from_dataframe["responseObjectAttributeId"]} - {attribute_from_dataframe["friendly"]}')
        try:
            value_from_body = response[attribute_from_dataframe['friendly']]
        except KeyError:
            raise Exception(f"The attribute '{attribute_from_dataframe['friendly']}' does not exist in the response. "
                            f"Check if the mapping is correct.")

        self.check_null(attribute_from_dataframe, value_from_body)
        self.check_empty(attribute_from_dataframe, value_from_body)
        condition = self.identify_attribute_in_main_dataframe(attribute_from_dataframe)
        if condition is None:
            return
        SuiteAttributes.df.loc[condition, 'attributeValue'] = Fake(value_from_body)

        # validate the rule
        attribute = Attributes.get(id=attribute_from_dataframe['attributeId'])
        if attribute is not None and not pd.isnull(attribute.rule):
            self.rules_handler.handle_condition(pd.Series(attribute), element_col='rule')

        logging.debug(f'End')

    @staticmethod
    def check_null(attribute, value):
        if not attribute['notNull']:
            return
        if value is None or str(value).lower() in ['null', 'none', 'nan']:
            raise Exception(f"The attribute '{attribute['friendly']}' is null but it should not be.")

    @staticmethod
    def check_empty(attribute, value):
        if not attribute['notEmpty']:
            return
        if len(str(value)) == 0:
            raise Exception(f"The attribute '{attribute['friendly']}' is empty but it should not be.")

    def extract_values_from_object_of_type_list(self, current_list_item, response_section):
        """
        Receive and address a subsection of the response and handles its data types. The attributes which don't have a
        value at the end will be deleted.

        The problem with matching the correct attribute is that it can be found in multiple depth levels of the same node under different JSONs.
        Then when comes to cloning attributes as a result of lists at the same depth there will be multiple indexes.

        :param current_list_item:
        :param response_section:
        :return:
        """
        logging.debug(f'Start for: {response_section}')
        if response_section == [] and current_list_item['notEmpty'] is False:
            logging.debug("It's an optional empty list")

            all_children = self.attributes['parent_id'] == current_list_item['attributeId']
            if self.attributes[all_children].shape[0] > 0:
                self.handle_children_of_optional_list_item(all_children, current_list_item)

            logging.debug("Crate an empty list as value")
            condition = self.identify_attribute_in_main_dataframe(current_list_item)
            SuiteAttributes.df.loc[condition, 'attributeValue'] = Fake([])
        elif response_section == [] and current_list_item['notEmpty'] is True:
            message = f"It's a mandatory list but the value for {current_list_item['referenceObjectId']} is {response_section}"
            logging.debug(message)
            raise Exception(message)
        elif response_section:
            attributes_to_duplicate = self.setup_list_attributes_for_duplication(current_list_item)

            self.handle_list_item(
                attributes_or_parent_id=attributes_to_duplicate,
                response_entities_holder=response_section
            )
        else:
            logging.debug('It is not a list')
        logging.debug(f'End of: {response_section}')

    def handle_children_of_optional_list_item(self, all_children, current_list_item):
        self.attributes[all_children]['attribute_instance_index'] = current_list_item['attribute_instance_index']
        self.attributes[all_children]['parent_instance_index'] = current_list_item['parent_instance_index']
        condition = self.identify_attributes_in_main_dataframe(self.attributes[all_children])
        if condition is None:
            return
        SuiteAttributes.df.loc[condition, 'attributeValue'] = Fake(None)

    def setup_list_attributes_for_duplication(self, current_list_item):
        attributes_to_duplicate = self.attributes[
            (self.attributes['parent_id'] == current_list_item['attributeId'])]
        attributes_to_duplicate['attribute_instance_index'] = 1
        attributes_to_duplicate['parent_instance_index'] = current_list_item['parent_instance_index']
        attributes_to_duplicate['node_instance_index'] = current_list_item['node_instance_index']
        attributes_to_duplicate.drop_duplicates(['friendly', 'attributeId', 'main_attribute_type', 'main_attribute_id', 'parent_object_id',
                                                 'parent_id', 'depth', 'referenceAttribute', 'referenceObjectId'], inplace=True)
        return attributes_to_duplicate

    def handle_list_item(self,
                         attributes_or_parent_id: int | pd.DataFrame,
                         response_entities_holder: list
                         ):
        logging.debug(f"Start for {response_entities_holder}")
        if type(attributes_or_parent_id) in [int, float]:
            attributes_to_duplicate = self.attributes[
                (self.attributes['parent_id'] == attributes_or_parent_id)]
        else:
            attributes_to_duplicate = attributes_or_parent_id
        logging.debug("attributes_to_duplicate determined")

        self.duplicate_list_attributes(
            dataframe_to_duplicate=attributes_to_duplicate,
            response_section=response_entities_holder
        )

        attribute_instance_index = 1
        for response_instance in response_entities_holder:
            attributes_to_duplicate['attribute_instance_index'] = attribute_instance_index

            self.handle_object_item(
                attributes_of_current_object=attributes_to_duplicate,
                response_instance=response_instance,
                parent_instance_index=attribute_instance_index
            )

            attribute_instance_index += 1

        logging.debug('End')

    def duplicate_list_attributes(self, dataframe_to_duplicate, response_section, increment_parent=False):
        """
        Looks into attributes and duplicates the attributes which indexes can be found in
        to_be_duplicated as many times as there are elements in response_section.

        :param increment_parent: if parent_instance_index should be equal with the global value or increment once with the iterations
        :param dataframe_to_duplicate: what needs to be duplicated
        :param response_section: The array of elements that has to be duplicated. Useful for knowing how many elements h
        ave to be duplicated.
        :return:
        """
        if dataframe_to_duplicate.empty:
            return
        global parent_instance_index
        logging.debug('Removing existing attributes if any')
        attributes_to_delete = self.identify_attributes_in_main_dataframe(dataframe_to_duplicate)
        if type(attributes_to_delete) == pd.DataFrame:
            logging.debug(f'Will drop indexes {attributes_to_delete.index.values}')
            for i, row in attributes_to_delete.iterrows():
                indexes = SuiteAttributes.df[(SuiteAttributes.df['attributeId'] == row['attributeId']) &
                                                    (SuiteAttributes.df['node_instance_index'] == row['node_instance_index']) &
                                                    (SuiteAttributes.df['parent_id'] == row['parent_id']) &
                                                    (SuiteAttributes.df['responseObjectId'] == row['responseObjectId'])].index
                SuiteAttributes.df.drop(index=indexes, inplace=True)
            SuiteAttributes.df.reset_index(drop=True)
        else:
            logging.debug('No attributes to remove from the main dataframe')

        logging.debug(f'Start duplication for {len(response_section) - 1} instances of:')
        logging.debug(
            dataframe_to_duplicate[["friendly", "node_instance_index", "parent_instance_index"]].to_json(
                orient="columns", indent=3)
        )

        for local_index in range(1, len(response_section) + 1):
            logging.debug(f'Start of duplication for index {local_index}')
            local_copy = dataframe_to_duplicate.copy()

            if increment_parent:
                local_copy['parent_instance_index'] = local_index
                local_copy['attribute_instance_index'] = 1
            else:
                local_copy['attribute_instance_index'] = local_index

            logging.debug(
                f'Saving {local_copy[["friendly", "node_instance_index", "parent_instance_index", "attribute_instance_index"]].to_json(orient="columns", indent=3)}')
            SuiteAttributes.df = pd.concat([local_copy, SuiteAttributes.df], ignore_index=True)
            logging.debug(f'End of duplication for index {local_index}')
        SuiteAttributes.df.reset_index(drop=True, inplace=True)
        logging.debug('End')