import json
import logging
import math
import os
import random
import re
import time
from contextlib import suppress
from copy import deepcopy

import numpy as np
import pandas as pd
import datetime
import calendar
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from Utils.Common.Fake import Fake
from Utils.Models.Api import Endpoint
from Utils.Web.Handlers.Dropdown import Dropdown
from Utils.Web.Handlers.Form import Form
from Utils.Web.Handlers.Pagination import Pagination
from Utils.Web.Handlers.Table import Table
from Utils.Common.Common import Common
from selenium.webdriver.support.select import Select
from Utils.Common.Meta import Meta

from Utils.Models.Repository import *

from selenium.webdriver.common.action_chains import ActionChains


class Handlers:
    def __init__(self, helpers, web, rules_handler):
        self.h = helpers
        self.web = web
        self.meta = Meta(helpers, self.web)
        self.common = Common(self.h, rules_handler)

    def handle_selector(self, element: InputAttribute, random_index=False, node_instance_index=1,
                        attribute_instance_index=1, update_attribute=False):
        """ Calculates the selector for an element.  \n
            - gets the selector associated to the element;
            - replaces the selector attributes with values;
            - if there are multiple values for a selector attribute, either takes a random one,
              or the one at a specified index;
            - applies metas to the selector, if any;
            - updates attribute values in dataframes, if needed;
            - if there are multiple values for a selector attribute, marks the one that is used;

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
            random_index: Bool, optional
                if True, random selector attribute values are selected if there are multiple values
            node_instance_index: Number, optional
                the node instance of the test step, default is 1
            attribute_instance_index: Number, optional
                the attribute index, if there are multiple values, default is 1
            update_attribute: Bool, optional
                True if attribute values should be updated in dataframes, False otherwise, default is False

            Returns
            -------
            string, int
                - the selector as a string
                - the selector index, if there are multiple identical selectors on the same page
        """
        rules_reversed_again = []
        logging.debug(f'Begin selector calculation for element {element.friendly}')
        try:
            selector_df = Selectors.get(id=element.selector_id)
            if selector_df is None:
                return selector_df, 0

            selector = selector_df.selector
            element_index = selector_df.index
            if not element_index or pd.isna(element_index):
                element_index = 0

            # if there are no attributes to replace in the selector, return the current values
            if not re.search('{\d+}', selector):
                logging.debug(f'End selector calculation for element {element.friendly}. '
                              f'Selector: {selector}; index: {element_index}')
                return selector, int(element_index)

            # get the attributes of the selector
            selectors_attributes = SelectorsAttributes.get_all(selectorId=element.selector_id)

            # if there are no selector attributes, return the current values
            if len(selectors_attributes) == 0:
                logging.debug(f'End selector calculation for element {element.friendly}. '
                              f'Selector: {selector}; index: {element_index}')
                return selector, int(element_index)

            rand_index = None
            rand_range = None
            selector = selector_df.selector
            order_index = 1
            while True:
                try:
                    selector_attributes = None
                    for el in selectors_attributes:
                        if el.orderIndex == order_index:
                            selector_attributes = el
                    attribute_id = selector_attributes.attributeId
                except (Exception,):
                    break

                last_valid_selector = selector
                while True:
                    # get the value of the selector attribute, random or at a given index
                    attribute_values = SuiteAttributes.get_all(attributeId=attribute_id)
                    attribute_value = None
                    if len(attribute_values) > 0:
                        if random_index and rand_range is None:
                            maxaii = max([av.attribute_instance_index for av in attribute_values if av.attribute_instance_index is not None])
                            rand_range = [i for i in range(1, int(maxaii + 1))]
                        if random_index and rand_index is None:
                            rand_index = random.randint(0, len(rand_range) - 1)

                        index = rand_range[rand_index] if random_index else attribute_instance_index
                        attribute = self.h.get_attribute_or_main_attribute(attribute_id, attribute_instance_index=index, actor=self.web.actor)
                        if attribute.attribute is None:
                            raise Exception()
                        attribute_value = attribute.value

                        # if this value is retrieved from previous requests, but has to be modified with metas
                        if selector_attributes.meta:
                            attribute_value = self.meta.handle_meta_attribute(
                                selector_attributes.meta, attribute_value, attribute_id)
                    elif not random_index and attribute_instance_index == 1:
                        # we need to get a value at the specific index, but there are no values to choose from
                        raise Exception()

                    selector = selector.replace('{' + str(order_index) + '}', str(attribute_value))

                    if not update_attribute:
                        break

                    attribute_id = attribute_id if len(attribute_values) > 0 else element.attributeId
                    index = rand_range[rand_index] if random_index else attribute_instance_index

                    # update the value in the big dataframe and mark the attribute as 'inUse'
                    self.set_attribute_property(
                        attribute_id, 'attributeValue', Fake(attribute_value),
                        attribute_instance_index=index, node_instance_index=node_instance_index)
                    self.set_attribute_property(
                        attribute_id, 'inUse', np.nan, node_instance_index=node_instance_index)
                    self.set_attribute_property(
                        attribute_id, 'inUse', True,
                        attribute_instance_index=index, node_instance_index=node_instance_index)

                    # we don't want the rules reversed for selectors, because we are only doing validations
                    if selector_attributes.ruleId and self.web.rules_reversed and selector_attributes.ruleId not in rules_reversed_again:
                        rules_reversed_again.append(selector_attributes.ruleId)
                        self.web.reverse_rule(selector_attributes.ruleId)

                    # check if the value satisfies the rule
                    rule = SimpleRules.get_all(id=selector_attributes.ruleId)
                    condition_result = False
                    if rule is not None and len(rule) > 0:
                        condition_result = self.web.rules_handler.handle_simple_rules(rule, in_use=True)
                    else:
                        rule = ComplexRules.get_all(id=selector_attributes.ruleId)
                        if rule is not None and len(rule) > 0:
                            condition_result = self.web.rules_handler.handle_complex_rules(rule, in_use=True)

                    if rule is None or len(rule) == 0:
                        break
                    if (not self.web.rules_reversed and condition_result) or \
                       (self.web.rules_reversed and not condition_result):
                        break
                    selector = last_valid_selector

                    del rand_range[rand_index]
                    rand_index = None
                    if len(rand_range) == 0:
                        raise Exception(f'There is no value for dropdown that satisfies the rules.')
                order_index += 1
            logging.debug(f'End selector calculation for element {element.friendly}. '
                          f'Selector: {selector}; index: {element_index}')
            # reverse the rules back
            for rule_id in rules_reversed_again:
                self.web.reverse_rule(rule_id)
            return selector, int(element_index)
        except Exception as e:
            # reverse the rules back
            for rule_id in rules_reversed_again:
                self.web.reverse_rule(rule_id)
            message = f'Could not get selector for element {element.friendly}. {e}'
            logging.error(message)
            raise Exception(message)

    def handle_button_as_link(self, element: InputAttribute, parent_element=None):
        """ Clicks a link associated to an element.

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
        """
        if parent_element is None:
            parent_element = self.web.driver
        logging.debug(f'Begin handle link for element {element.friendly}')
        self.handle_button_as_button(element, parent_element)
        logging.debug(f'Begin handle link for element {element.friendly}')

    def handle_button_as_button(self, element: InputAttribute, parent_element=None):
        """ Clicks a link button to an element. \n
            Handles input and output events of this element.

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
        """
        if parent_element is None:
            parent_element = self.web.driver
        logging.debug(f'Begin handle button for element {element.friendly}')
        button = self.get_html_element(element, parent_element)
        self.click_element(button)
        logging.debug(f'Begin handle button for element {element.friendly}')

    def handle_hover(self, element: InputAttribute, parent_element=None):
        """ Hovers over an object associated to an element.

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
        """
        if parent_element is None:
            parent_element = self.web.driver
        logging.debug(f'Begin handle hover for element {element.friendly}')
        html_element = self.get_html_element(element, self.web.driver, parent_element)
        self.move_to_element(html_element)
        logging.debug(f'End handle hover for element {element.friendly}')

    def handle_hooks(self, hook_type, hooks: List[Hook]):
        """ Handles hooks, checks that requests are triggered and validates their response.

            Parameters
            ----------
            hook_type: String
                the type of hook, 'onInit'/'onDestroy'
            hooks: List
                a list of hooks to handle
        """
        logging.debug(f'Begin handle {hook_type} hooks')
        for hook in hooks:
            if hook.hookType != hook_type:
                continue
            for endpoint_id in hook.endpoints_ids[::-1]:
                self.handle_endpoint(Endpoints.get_all(endpoint_id=endpoint_id))
        logging.debug(f'End handle {hook_type} hooks')

    def handle_input(self, element: InputAttribute, parent_element=None):
        """ Handles and validates an input. \n
            - validates the status of the input, if it should be disabled or not
            - gets a value or generates a new one for the input
            - inputs the value
            - handles input and output events of this element

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
        """
        logging.debug(f'Begin handle input for element {element.friendly}')
        if parent_element is None:
            parent_element = self.web.driver
        html_element = self.get_html_element(element, parent_element)
        self.check_disabled(html_element, element)

        # if the element is prepopulated, check its values with the one from backend
        if element.prepopulated and element.attributeId:
            attribute_value = self.h.get_attribute_or_main_attribute(element.attributeId, actor=self.web.actor).value
            input_value = self.get_value_from_html_element(element, parent_element)
            if str(attribute_value) != str(input_value):
                raise Exception(f'Prepopulated value {attribute_value} differs from {input_value}.')
            # clear the input
            html_element.clear()

        is_wrong_data_type = self.web.last_node and self.h.data['category']['technical_name'] == 'WRONG_DATA_TYPES' \
                                                and self.h.data['category']['entityId'] == element.id

        if (self.web.missing_value_entity_id is None or element.id != self.web.missing_value_entity_id) and \
                not element.disabled:
            required = random.choice([True, False])
            if element.required:
                required = True
            if required:
                input_value = self.h.generate_input_value(element, self.web.rules_handler, is_wrong_data_type=is_wrong_data_type,
                                                          actor=self.web.actor)
                input_value = input_value.value if type(input_value) == Fake else input_value
                self.move_to_element(html_element)
                html_element.clear()
                html_element.send_keys(input_value)

        logging.debug(f'End handle input for element {element.friendly}')

    def handle_any(self, element: InputAttribute, parent_element=None):
        """ Validates an element that doesn't have a specific type. \n
            - if the element has a selector, verifies that it is present on page
            - handles input and output events

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
            parent_element: WebDriver element
                the parent html element of the current element
                if unspecified or None, the default one is used
        """
        if parent_element is None:
            parent_element = self.web.driver
        logging.debug(f'Begin handle any for element {element.friendly}')
        self.get_html_element(element, parent_element)
        logging.debug(f'End handle any for element {element.friendly}')

    def handle_any_no_events(self, element: InputAttribute, parent_element=None):
        if parent_element is None:
            parent_element = self.web.driver
        logging.debug(f'Begin handle any for element {element.friendly}')
        self.get_html_element(element, parent_element)
        logging.debug(f'End handle any for element {element.friendly}')

    def handle_dropdown(self, element: InputAttribute, parent_element=None):
        logging.debug(f'Begin handle dropdown for element {element.friendly}')
        Dropdown(element, self, self.h, self.web).validate(parent_element)
        logging.debug(f'End handle dropdown for element {element.friendly}')

    def handle_table(self, component: Component, parent_element=None):
        logging.debug(f'Start handle table for component {component.friendly}')
        Table(component, self.h, self)

        if parent_element is None:
            parent_element = self.web.driver
        component_settings = json.loads(component.componentSettings)
        testing_percent = int(self.web.config['DEFAULT'].get('PARTIAL_TESTING_PERCENT', 50))

        pages_to_test = None
        pagination = None
        if component.paginationId:
            pagination = Pagination(Components.get(id=component.paginationId), self.h, self)
            pagination.validate()
            pages_to_test = pagination.pages_to_test
        if pages_to_test is None or len(pages_to_test) == 0:
            pages_to_test = [1]

        table_element = parent_element
        if component_settings['tableTag']['elementId'] is not None:
            table_element = self.get_element_or_element_group(component_settings['tableTag']['elementType'], component_settings['tableTag']['elementId'])
            self.validate_element_or_element_group(component_settings['tableTag']['elementType'], table_element, parent_element)
            table_element = self.get_html_element(table_element, parent_element)

        for page in pages_to_test:
            if pagination:
                pagination.go_to_page(page)

            self.handle_table_header(component_settings, table_element)
            if pagination:
                self.handle_table_body(component_settings,
                                       pagination=True,
                                       items_per_page=pagination.items_per_page,
                                       total_items=pagination.no_of_results,
                                       pages_nr=pagination.no_of_pages,
                                       page=page,
                                       testing_percent=testing_percent,
                                       table_element=table_element)
            else:
                self.handle_table_body(component_settings)
            self.handle_table_footer(component_settings, table_element)
        # go back to first page
        if pagination:
            pagination.go_to_first_page()
        logging.debug(f'End handle table for component {component.friendly}')

    def validate_element_or_element_group(self, element_type, element_id, parent_element=None):
        if element_type is None or element_id is None:
            return

        if element_type.upper() == 'ELEMENT':
            self.web.validators.validate_element(element_id, parent_element=parent_element)
        elif element_type.upper() == 'GROUP-ELEMENT':
            self.web.validators.validate_element_group(element_id, parent_element=parent_element)

    def get_element_or_element_group(self, element_type, element_id) -> InputAttribute | ElementsGroup | None:
        if element_type is None:
            return None
        if element_type.upper() == 'ELEMENT':
            return InputAttributes.get(id=element_id)
        elif element_type.upper() == 'GROUP-ELEMENT':
            return ElementsGroups.get(id=element_id)
        return None

    def handle_table_header(self, component_settings, table_element=None):
        settings = component_settings['tableHeader']

        if settings['activation'] is not None:
            activation_element = self.get_element_or_element_group(settings['activationType'], settings['elementId'])
            self.validate_element_or_element_group(settings['activationType'], activation_element, table_element)

        header_element = self.web.driver if table_element is None else table_element
        if settings['elementId'] is not None:
            header_element = self.get_element_or_element_group(settings['elementType'], settings['elementId'])
            self.validate_element_or_element_group(settings['activationType'], header_element, table_element)
            header_element = self.get_html_element(header_element, table_element)

        for row in settings['tableHeaderRows']:
            if row['elementId'] is None:
                continue
            header_row = self.get_element_or_element_group(row['elementType'], row['elementId'])
            self.validate_element_or_element_group(row['elementType'], header_row, header_element)
            header_row = self.get_html_element(header_row, header_element)
            for cell in settings['tableHeaderColumns']:
                if cell['elementId'] is None:
                    continue
                header_cell = self.get_element_or_element_group(cell['elementType'], cell['elementId'])
                self.validate_element_or_element_group(cell['elementType'], header_cell, header_row)

    def handle_table_body(self, component_settings, pagination=False, items_per_page=None, total_items=None, pages_nr=None, page=None, testing_percent=None, table_element=None):
        settings = component_settings['tableBody']
        body_element = self.web.driver if table_element is None else table_element

        if settings['elementId'] is not None:
            body_element = self.get_element_or_element_group(settings['elementType'], settings['elementId'])
            self.validate_element_or_element_group(settings['elementType'], body_element, table_element)
            body_element = self.get_html_element(body_element, table_element)

        if not pagination:
            row_nr = 1
            while True:
                try:
                    self.handle_table_row(settings['tableBodyRows'], settings['tableBodyColumns'], row_nr, 1, row_nr, body_element)
                except (Exception,):
                    break
                row_nr += 1

        items_per_page = total_items % items_per_page if page == pages_nr else items_per_page
        rows_to_test = []
        if self.web.config['DEFAULT'].get('PARTIAL_TESTING', False) in ['True', 'true', '1', True]:
            rows_to_test = random.sample(range(1, items_per_page + 1), math.ceil(testing_percent * items_per_page / 100))
        for i in range(1, items_per_page + 1):
            if rows_to_test == [] or i in rows_to_test:
                self.handle_table_row(settings['tableBodyRows'], settings['tableBodyColumns'], items_per_page, page, i, body_element)

    def handle_table_footer(self, component_settings, table_element=None):
        settings = component_settings['tableFooter']

        footer_element = self.web.driver if table_element is None else table_element
        if settings['elementId'] is not None:
            footer_element = self.get_element_or_element_group(settings['elementType'], settings['elementId'])
            self.validate_element_or_element_group(settings['elementType'], footer_element, table_element)
            footer_element = self.get_html_element(footer_element, table_element)

        for cell in settings['tableFooterColumns']:
            if cell['elementId'] is None:
                continue
            footer_cell = self.get_element_or_element_group(cell['elementType'], cell['elementId'])
            self.validate_element_or_element_group(cell['elementType'], footer_cell, footer_element)

    def handle_table_row(self, rows, cells, rows_nr, page_nr, row_nr, parent_element=None):
        logging.debug(f'Start handle table for row {row_nr}')
        row_nr = row_nr % (rows_nr + 1)
        for row in rows:
            row_element = self.get_element_or_element_group(row['elementType'], row['elementId'])
            self.validate_element_or_element_group(row['elementType'], row_element, parent_element)
            row_element = self.get_html_element(row_element, parent_element, element_index=row_nr)
            for cell in cells:
                cell_element = self.get_element_or_element_group(cell['elementType'], cell['elementId'])
                self.validate_element_or_element_group(cell['elementType'], cell_element, row_element)
                if not hasattr(cell_element, 'attributeId') or not cell_element.attributeId or np.isnan(cell_element.attributeId):
                    continue

                try:
                    attribute_index = (page_nr - 1) * rows_nr + row_nr
                    attribute_value = self.h.get_attribute_or_main_attribute(
                        cell_element.attributeId, attribute_instance_index=attribute_index, actor=self.web.actor).value
                except (Exception,):
                    continue
                cell_value = self.get_value_from_html_element(cell_element, parent_element=row_element)
                if attribute_value != cell_value:
                    # TODO: make this validation strict and use meta
                    continue
                    raise Exception(f'Data from table is not the one received from API. '
                                    f'Value {attribute_value} differs from {cell_value}.')
        logging.debug(f'End handle table for row {row_nr}')

    def handle_calendar(self, component: Component, parent_element=None) -> None:
        logging.debug(f'Start handle calendar for component {component.friendly}')
        if parent_element is None:
            parent_element = self.web.driver
        component_settings = json.loads(component.componentSettings)

        # handle calendar body
        calendar_body = parent_element
        if component_settings['calendarTag']['elementId']:
            calendar_element = self.get_element_or_element_group(component_settings['calendarTag']['elementType'], component_settings['calendarTag']['elementId'])
            self.handle_any(calendar_element, parent_element)
            calendar_body = self.get_html_element(calendar_element, parent_element)

        properties = {
            'year': {'min': datetime.now().year - 50, 'max': datetime.now().year + 50, 'value': 0, 'to_exclude': []},
            'month': {'min': 1, 'max': 12, 'value': 0, 'to_exclude': []},
            'day': {'min': 1, 'max': 28, 'value': 0, 'to_exclude': []}
        }

        if component.validDataCondition:
            rule_attributes = self.web.rules_handler.calculate_attributes_based_on_rule(component.validDataCondition)
            for k1, attribute in rule_attributes.items():
                for at_type in ['year', 'month', 'day']:
                    with suppress(Exception):
                        properties[at_type]['min'] = attribute['subAttributes'][at_type]['min']
                    with suppress(Exception):
                        properties[at_type]['max'] = attribute['subAttributes'][at_type]['max']
                    with suppress(Exception):
                        properties[at_type]['to_exclude'] = attribute['subAttributes'][at_type]['to_exclude']
                    with suppress(Exception):
                        properties[at_type]['value'] = attribute['subAttributes'][at_type]['value']

        # choose a random date based on the properties
        random_date = self.web.rules_handler.get_random_date(properties)
        date_attributes = {}

        for at_type in ['Year', 'Month', 'Day']:
            current_element = None
            value_changed = False

            if component_settings[f'calendar{at_type}'][f'current{at_type}']['elementId']:
                current_element = self.get_element_or_element_group(component_settings[f'calendar{at_type}'][f'current{at_type}']['elementType'],
                                                                    component_settings[f'calendar{at_type}'][f'current{at_type}']['elementId'])
                try:
                    self.handle_any(current_element, calendar_body)
                    current_value = self.get_value_from_html_element(current_element, calendar_body)
                    try:
                        properties[at_type.lower()]['value'] = int(current_value)
                        if at_type == 'Month':
                            properties[at_type.lower()]['value'] += 1
                    except ValueError:
                        properties[at_type.lower()]['value'] = self.web.rules_handler.month_to_num(current_value)
                    attribute_id = current_element.attributeId
                    if attribute_id:
                        if attribute_id not in date_attributes:
                            date_attributes[attribute_id] = self.web.rules_handler.get_date_format_from_attribute_id(attribute_id)
                        if date_attributes[attribute_id] is not None:
                            date_attributes[attribute_id] = date_attributes[attribute_id].replace('{' + at_type.lower() + '}', str(properties[at_type.lower()]['value']))
                            self.set_attribute_property(attribute_id, 'attributeValue', Fake(date_attributes[attribute_id]))
                        else:
                            self.set_attribute_property(attribute_id, 'attributeValue', Fake(properties[at_type.lower()]['value']))
                except (Exception,):
                    # there may be cases when this element may not be accessible because it has the date in the selector
                    # and the date may not be generated yet
                    pass

            if component_settings[f'calendar{at_type}'][f'previous{at_type}']['elementId']:
                previous_element = self.get_element_or_element_group(component_settings[f'calendar{at_type}'][f'previous{at_type}']['elementType'],
                                                                    component_settings[f'calendar{at_type}'][f'previous{at_type}']['elementId'])
                self.handle_any_no_events(previous_element, calendar_body)
                date_value = getattr(random_date, at_type.lower())
                if date_value < properties[at_type.lower()]['value']:
                    value_changed = True
                    counter = 1
                    for i in range(properties[at_type.lower()]['value'] - int(date_value)):
                        attribute_id = previous_element.attributeId
                        if attribute_id:
                            if attribute_id not in date_attributes:
                                date_attributes[attribute_id] = self.web.rules_handler.get_date_format_from_attribute_id(attribute_id)
                            if date_attributes[attribute_id] is not None:
                                date_attributes[attribute_id] = date_attributes[attribute_id].replace('{' + at_type.lower() + '}', str(date_value - counter))
                                self.set_attribute_property(attribute_id, 'attributeValue', Fake(date_attributes[attribute_id]))
                            else:
                                self.set_attribute_property(attribute_id, 'attributeValue', Fake(properties[at_type.lower()]['value'] - counter))
                        self.handle_button_as_button(previous_element, calendar_body)
                        counter += 1
                    properties[at_type.lower()]['value'] = date_value

            if component_settings[f'calendar{at_type}'][f'next{at_type}']['elementId']:
                next_element = self.get_element_or_element_group(component_settings[f'calendar{at_type}'][f'next{at_type}']['elementType'],
                                                                     component_settings[f'calendar{at_type}'][f'next{at_type}']['elementId'])
                self.handle_any_no_events(next_element, calendar_body)
                date_value = getattr(random_date, at_type.lower())
                if date_value > properties[at_type.lower()]['value']:
                    value_changed = True
                    counter = 1
                    for i in range(int(date_value - properties[at_type.lower()]['value'])):
                        attribute_id = next_element.attributeId
                        if attribute_id:
                            if attribute_id not in date_attributes:
                                date_attributes[attribute_id] = self.web.rules_handler.get_date_format_from_attribute_id(attribute_id)
                            if date_attributes[attribute_id] is not None:
                                date_attributes[attribute_id] = date_attributes[attribute_id].replace('{' + at_type.lower() + '}', str(properties[at_type.lower()]['value'] + counter))
                                self.set_attribute_property(attribute_id, 'attributeValue', Fake(date_attributes[attribute_id]))
                            else:
                                self.set_attribute_property(attribute_id, 'attributeValue', Fake(properties[at_type.lower()]['value'] + counter))
                        self.handle_button_as_button(next_element, calendar_body)
                        counter += 1
                    properties[at_type.lower()]['value'] = date_value

            if not value_changed and getattr(random_date, at_type.lower()) != properties[at_type.lower()]['value'] and current_element is not None:
                # try clicking the current element, if there are no others things to press in order to achieve the date
                properties[at_type.lower()]['value'] = getattr(random_date, at_type.lower())
                attribute_id = current_element.attributeId
                if attribute_id:
                    if attribute_id not in date_attributes:
                        date_attributes[attribute_id] = self.web.rules_handler.get_date_format_from_attribute_id(attribute_id)
                    if date_attributes[attribute_id] is not None:
                        date_attributes[attribute_id] = date_attributes[attribute_id].replace('{' + at_type.lower() + '}', str(properties[at_type.lower()]['value']))
                        self.set_attribute_property(attribute_id, 'attributeValue', Fake(date_attributes[attribute_id]))
                    else:
                        self.set_attribute_property(attribute_id, 'attributeValue', Fake(properties[at_type.lower()]['value']))

                self.click_element(self.get_html_element(current_element, calendar_body))

        logging.debug(f'End handle calendar for component {component.friendly}')

    def handle_form(self, component: Component, parent_element=None):
        logging.debug(f'Start handle form for component {component.friendly}')
        Form(component, self.h, self).validate(parent_element)
        logging.debug(f'End handle form for component {component.friendly}')

    def handle_modal(self, component: Component, parent_element=None):
        settings = json.loads(component.componentSettings)
        if parent_element is None:
            parent_element = self.web.driver

        # handle modal tag
        modal_element = parent_element
        if settings['modalTag']['elementId'] and not np.isnan(settings['modalTag']['elementId']):
            modal_element = InputAttributes.get(id=settings['modalTag']['elementId'])
            self.handle_any(modal_element, parent_element)
            modal_element = self.get_html_element(modal_element, parent_element)

        # handle modal header, body and footer
        for modal_section in ['modalHeader', 'modalBody', 'modalFooter']:
            for header in settings[modal_section]:
                element = InputAttributes.get(id=header['elementId'])
                self.web.validators.validate_element(element, modal_element)

    def handle_iframe(self, component: Component, parent_element=None):
        logging.debug(f'Start handle iframe for component {component.friendly}')
        settings = json.loads(component.componentSettings)
        if parent_element is None:
            parent_element = self.web.driver

        # handle iframe tag
        iframe_element = parent_element
        if settings['modalTag']['elementId'] and not np.isnan(settings['modalTag']['elementId']):
            iframe_element = InputAttributes.get(id=settings['modalTag']['elementId'])
            self.handle_any(iframe_element)
            iframe_element = self.get_html_element(iframe_element, parent_element)
            self.web.driver.switch_to.frame(iframe_element)

        # handle iframe header, body and footer
        for iframe_section in ['modalHeader', 'modalBody', 'modalFooter']:
            for header in settings[iframe_section]:
                element = InputAttributes.get(id=header['elementId'])
                self.web.validators.validate_element(element, iframe_element)
        logging.debug(f'End handle iframe for component {component.friendly}')

    def handle_iframe_out(self):
        self.web.driver.switch_to_default_content()

    def get_attribute_value_or_search_in_page(self, attribute: InputAttribute):
        """ Tries to get the value of an attribute from the big dataframe.
            If it has no value, it is searched in page using meta property.

            Parameters
            ----------
            attribute: Series
                row of the attributes dataframe

            Returns
            ----------
            value of the attribute
        """
        try:
            value = self.h.get_attribute_or_main_attribute(attribute.attributeId, actor=self.web.actor).value
            if np.isnan(value) or value is None or value == '':
                raise Exception()
            return value
        except (Exception,):
            element = InputAttributes.get(id=attribute.attributeId, elementOptionsMeta='{'+attribute.friendly+'}')
            html_element = self.get_html_element(element, self.web.driver)
            return self.get_value_from_html_element(html_element)

    def handle_endpoint(self, endpoints: [Endpoint]):
        """ Handles and validates an api request. \n
            - checks network log for the response of the request, before the timeout being reached
            - if the response is received, check its status code, deserialize response, validates response data and
              populates dataframes with values
            - thrown an exception if the request is not valid

            Parameters
            ----------
            endpoints: List[Endpoint]
                list of the endpoint with each status code
        """
        if len(endpoints) == 0:
            return

        logging.debug(f'Begin handle endpoint {endpoints[0].endpoint_friendly}')
        start_time = time.perf_counter()
        timeout = self.parse_timeout_from_df(endpoints[0].timeout)
        frequency = min(timeout / 2, 500)
        all_possible_urls = self.h.valorize_endpoint_url(endpoints[0], actor=self.web.actor)

        response = None
        trigger_request = None
        while (time.perf_counter() - start_time) * 1000 <= timeout:
            # wait for response to be received
            try:
                trigger_request, response = self.get_response(endpoints[0], all_possible_urls)
            except (Exception,):
                time.sleep(frequency / 1000)
            if response:
                break
            time.sleep(frequency / 1000)

        if response:
            req_json = self.req_res_to_json(trigger_request)
            self.web.inputParamValues.append({'body': req_json['body'], 'header': req_json['headers']})
            res_json = self.req_res_to_json(response)
            self.web.bodyOutput.append({'body': res_json['body'], 'header': res_json['headers']})

            # get the status code of the response
            endpoint_status_codes = []
            for endpoint in endpoints:
                if endpoint.statusCode == response.status_code:
                    endpoint_status_codes.append(endpoint)

            if len(endpoint_status_codes) == 0:
                raise Exception(f'{endpoints[0].endpoint_friendly} received an unexpected status code: {response.status_code}')

            valid_endpoints = []
            for endpoint_status_code in endpoint_status_codes:
                # make a copy of the suite attributes to avoid modifying the original ones in case of failure
                suite_attributes_copy = deepcopy(SuiteAttributes.df)
                try:
                    # validate_rule
                    if endpoint_status_code.rule:
                        rule = SimpleRules.get_all(id=endpoint_status_code.rule)
                        if rule is not None and len(rule) > 0:
                            condition_result = self.web.rules_handler.handle_simple_rules(rule)
                            if not condition_result:
                                raise Exception()
                        else:
                            rule = ComplexRules.get_all(id=endpoint_status_code.rule)
                            condition_result = self.web.rules_handler.handle_complex_rules(rule)
                            if not condition_result:
                                raise Exception()

                    # validate request body
                    self.common.handle_request_response(endpoint_status_code, req_json['body'], des_type='request', actor=self.web.actor)

                    # validate response body
                    self.common.handle_request_response(endpoint_status_code, res_json['body'], des_type='response', actor=self.web.actor)
                    valid_endpoints.append(endpoint_status_code)
                except Exception as e:
                    logging.error(f'Could not validate endpoint {endpoints[0].endpoint_friendly}. {e}')
                    SuiteAttributes.df = suite_attributes_copy
                    continue

            if len(valid_endpoints) == 0:
                raise Exception(f'{endpoints[0].endpoint_friendly} received an unexpected response. '
                                f'Check that everything is mapped properly.')

            # self.handle_status_code(endpoints[0], response)
            for valid_endpoint in valid_endpoints:
                self.web.fulfilled_requests.append({
                    'endpointId': int(valid_endpoint.endpoint_id),
                    'statusCodeId': int(valid_endpoint.id),
                    'method': trigger_request.method,
                    'url': trigger_request.url + '?' + trigger_request.querystring,
                    'projectId': int(valid_endpoint.projectId),
                    'requestData': self.req_res_to_json(trigger_request),
                    'responseData': self.req_res_to_json(response)
                })

            # if the response is a negative one, the test should fail
            for valid_endpoint in valid_endpoints:
                if valid_endpoint.outcome == 'NEGATIVE':
                    raise Exception(f'{valid_endpoint.endpoint_friendly} received a negative response: {response.status_code}')
        else:
            # if the response was not received, this test does not deserve to pass
            raise Exception(f'{endpoints[0].endpoint_friendly} received no response in {timeout / 1000} seconds')
        logging.debug(f'End handle request {endpoints[0].endpoint_friendly}')

    @staticmethod
    def clear_input_values(html_element):
        with suppress(Exception,):
            html_element.clear()

        with suppress(Exception,):
            dropdown = Select(html_element)
            dropdown.deselect_all()

    def handle_message(self, message: InMessage | OutMessage, message_type='in'):
        """ Handles and validates an api request. \n
            - checks network log for the response of the request, before the timeout being reached
            - if the response is received, check its status code, deserialize response, validates response data and
              populates dataframes with values
            - thrown an exception if the request is not valid

            Parameters
            ----------
            message: Series
                message data, row of the inMessages/outMessages dataframe
            message_type: String
                the message type, 'in' or 'out'
        """
        # TODO: temporary
        time.sleep(20)
        return

        logging.debug(f'Begin handle message {message.friendly}')
        start_time = time.perf_counter()
        # timeout = self.parse_timeout_from_df(message['timeout'])
        timeout = 5000
        frequency = min(timeout / 2, 500)
        # url = self.valorize_request_url(message)
        url = message.url

        in_message = None
        out_message = None
        if message_type == 'in':
            in_message = message
        else:
            out_message = message
            if message.inMessageId:
                in_message = InMessages.get(id=message.inMessageId)

        in_data = None
        out_data = None
        while (time.perf_counter() - start_time) * 1000 <= timeout:
            # wait for response to be received
            try:
                out_data, in_data = self.get_message_data(in_message, out_message, url)
            except (Exception,):
                time.sleep(frequency / 1000)
            if (in_message is None or in_data) and (out_message is None or out_data):
                break
            time.sleep(frequency / 1000)

        if (in_message is not None and not in_data) or (out_message is not None and not out_data):
            raise Exception(f'{message.friendly} could not be found in {timeout}')

        if in_message is not None and in_data:
            try:
                self.common.handle_request_response(message, json.loads(in_data), 'response', actor=self.web.actor)
            except (Exception,):
                raise Exception(
                    f'Could not deserialize message {message.friendly}. Check that everything is mapped properly.')
        if out_message is not None and out_data:
            try:
                self.common.handle_request_response(message, json.loads(out_data), 'request', actor=self.web.actor)
            except (Exception,):
                raise Exception(
                    f'Could not deserialize message {message.friendly}. Check that everything is mapped properly.')

        logging.debug(f'End handle message {message.friendly}')

    @staticmethod
    def req_res_to_json(req_res_object):
        new_json = {}
        for attribute_key in ['body', 'cert', 'date', 'headers', 'host', 'method',
                              'params', 'path', 'querystring', 'response', 'url']:
            with suppress(Exception):
                attribute = getattr(req_res_object, attribute_key)
                try:
                    try:
                        attribute = attribute.decode('utf-8')
                        attribute = json.loads(attribute)
                    except (Exception,):
                        attribute = attribute.decode('utf-8').replace("'", '"')
                        attribute = json.loads(attribute)
                except (Exception,):
                    if attribute_key == 'headers':
                        try:
                            attribute = dict(attribute)
                        except (Exception,):
                            attribute = str(attribute)
                    elif attribute_key == 'cert':
                        attribute = str(attribute)
                    elif attribute_key == 'body' and len(attribute) == 0:
                        attribute = {}
                    elif type(attribute) != int and type(attribute) != float and type(attribute) != dict:
                        attribute = str(attribute)
                new_json[attribute_key] = attribute
        return new_json

    def get_response(self, endpoint: Endpoint, all_possible_urls: list):
        """ Gets the response for a request triggered. \n
            Searches the network log in reverse order to find the response that matches our request.

            Parameters
            ----------
            endpoint: Series
                request data, row of the requests dataframe
            all_possible_urls: List[String]
                all possible urls of the request

            Returns
            -------
            dict
                the response as a dictionary
        """
        logging.debug(f'Begin search response for endpoint {endpoint.endpoint_friendly}')

        all_possible_query_params = [url.split('?')[-1] for url in all_possible_urls]
        # handling http requests
        for trigger_request in self.web.driver.requests[::-1]:
            if not trigger_request.response or trigger_request.method != endpoint.verb:
                continue

            if trigger_request.url in all_possible_urls or trigger_request.url + '?' + trigger_request.querystring in all_possible_urls or \
                    (trigger_request.url in all_possible_urls and trigger_request.querystring in all_possible_query_params) or \
                    trigger_request.url.split('?')[0] in all_possible_urls or trigger_request.url.split('?')[0] + '/' in all_possible_urls:
                logging.debug(f'End search response for request {endpoint.endpoint_friendly}. '
                              f'Response found: {trigger_request.response.body}')
                return trigger_request, trigger_request.response
        return None, None

    def get_message_data(self, in_message, out_message, url):
        """ Gets the data of a websocket message (in or out)

            Parameters
            ----------
            in_message: Series
                websocket in message, None if not existing
            out_message: Series
                websocket out message, None if not existing
            url: String
                websockets url

            Returns
            -------
            dict
                the response as a dictionary
        """
        for request in self.web.driver.requests[::-1]:
            if request.url != url:
                continue
            ws_messages = request.ws_messages
            for index, message in enumerate(ws_messages[::-1]):
                if out_message is not None:
                    if message.from_client is False or not self.identify_websocket_message(message.content, out_message, 'out'):
                        continue
                elif in_message is not None:
                    if message.from_client is True or not self.identify_websocket_message(
                            message.content, in_message, 'in'):
                        continue
                    sanitized_response = self.sanitize_response(message.content, in_message)
                    logging.debug(f'End search response for message {out_message["friendly"]}. '
                                  f'Response found: {sanitized_response}')
                    return None, sanitized_response

                if in_message is None:
                    sanitized_response = self.sanitize_response(message.content, out_message)
                    return sanitized_response, None
                for response_message in ws_messages[(len(ws_messages) - index):]:
                    if response_message.from_client is True or not self.identify_websocket_message(
                            response_message.content, in_message, 'in'):
                        continue
                    sanitized_response = self.sanitize_response(response_message.content, in_message)
                    logging.debug(f'End search response for message {out_message["friendly"]}. '
                                  f'Response found: {sanitized_response}')
                    return self.sanitize_response(message.content, out_message), sanitized_response
        return None, None

    @staticmethod
    def sanitize_response(response_string: str, request: Endpoint):
        """ Sanitizes the string body of a response. \n
            Clears everything before and after the brackets.

            Parameters
            ----------
            response_string: string
                the response body as a string
            request: Series
                request data, row of the requests dataframe

            Returns
            -------
            string
                the sanitized response as a string
        """
        if 'bodyIsList' in request and request.bodyIsList is True:
            return response_string[response_string.find('['):response_string.rfind(']') + 1]
        return response_string[response_string.find('{'):response_string.rfind('}') + 1]

    def identify_websocket_message(self, message_body, message, msg_type='out', node_instance_index=1):
        try:
            dataframe = OutMessagesAttributes if msg_type == 'out' else InMessagesAttributes
            message_attributes = [ma.friendly for ma in dataframe.get_all(node_id=message['id'], node_instance_index=node_instance_index)]
            for attribute in message_attributes:
                if attribute not in message_body:
                    return False

            json_request = json.loads(self.sanitize_response(message_body, message))
            suite_attributes_copy = SuiteAttributes.df.copy()
            des_type = 'request' if msg_type == 'out' else 'response'
            self.common.handle_request_response(message, json_request, des_type, actor=self.web.actor)
            suite_attributes_deserialized = SuiteAttributes.df.copy()
            SuiteAttributes.df = suite_attributes_copy

            message_attributes = dataframe.get_all(node_id=message['id'], node_instance_index=node_instance_index)
            for attribute in message_attributes:
                if attribute.attributeValue is not None:
                    deserialized_attribute_values = suite_attributes_deserialized[
                        suite_attributes_deserialized['attributeId'] == attribute.attributeId]['attributeValue'].values
                    found = False
                    for value in deserialized_attribute_values:
                        if type(value) == Fake and attribute.attributeValue == value.value:
                            found = True
                            break
                    if not found:
                        return False
            return True
        except (Exception,):
            return False

    @staticmethod
    def parse_timeout_from_df(timeout):
        """ Parses a human friendly timeout to milliseconds. \n
            Ex.: 5s = 5 seconds; 5m = 5 minutes; 5h = 5 hours; 1000 = 1 second

            Parameters
            ----------
            timeout: String
                the timeout value as a string

            Return
            ------
            int
                the parsed timeout as an integer, 5000 by default
        """
        try:
            if timeout.endswith('s'):
                return int(timeout[:-1]) * 1000
            elif timeout.endswith('m'):
                return int(timeout[:-1]) * 60 * 1000
            elif timeout.endswith('h'):
                return int(timeout[:-1]) * 60 * 60 * 1000
            return int(timeout)
        except (Exception,):
            return 5000  # 5 seconds default

    def handle_status_code(self, request: Endpoint, response, node_instance_index=1):
        """ Handles and validates the status code of a request. \n
            Searches for a status code object associated to this request and its response status code.
            Validates the status code attributes values.
            If the status code is a negative one, or the values validation fails, throws an exception.

            Parameters
            ----------
            request: Series
                request data, row of the requests dataframe
            response: Dict
                dictionary with the response data
            node_instance_index: Number, optional
                the node instance of the test step, default is 1
        """

        status_codes_ids = [sc['statusCodeId'] for sc in request.requestStatusCodes]
        status_code = StatusCodes.get(statusCode=response.status_code, id=status_codes_ids)
        if status_code is None:
            return

        if '{{negative}}' in status_code.friendly:
            raise Exception(f'Request {request.friendly} returned a negative status code.')

        response_status_codes = ResponseStatusCodes.get_all(statusCodeId=status_code.id, requestId=request.id)
        for row in response_status_codes:
            try:
                attribute = self.h.get_attribute_or_main_attribute(row.entityId, node_instance_index=node_instance_index, actor=self.web.actor)
                attribute_value = attribute.value
                attribute = attribute.attribute

                # TODO: temporary until the dataframes are fixed
                if type(attribute_value) in [int, float] or attribute_value.isnumeric():
                    attribute_type = 'NUMBER'
                else:
                    attribute_type = 'STRING'

                condition = self.web.rules_handler.check_simple_rule(
                    attribute_type, attribute_value, row.comparisonValue, row.conditionOperator)
                if not condition:
                    raise Exception(f'Status code {status_code.friendly} validation failed. '
                                    f'Response validation failed for attribute {attribute["friendly"]}')
            except (Exception,):
                raise Exception(f'Status code {status_code.friendly} validation failed.')

    @staticmethod
    def check_disabled(html_element, element: InputAttribute):
        """ Validates if an element should be disabled or not.

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element
            element: Series
                element data, a row from the dataframe
        """
        disabled = html_element.is_enabled()
        if element.disabled and element.disabled != disabled:
            raise Exception(f'Disabled validation failed')

    def identify_element(self, selector, parent_element, index=0):
        """ Identifies a html element, moves the cursor to it and takes a screenshot. \n

            Parameters
            ----------
            selector: String
                the selector of the element as a string
            parent_element: WebDriverElement
                the parent html element of the element that is identified
            index: Number
                the index of the element, if there are multiple ones with
                the same selector on the page

            Returns
            -------
            WebDriverElement
                the html element if found, else throws an exception
        """

        try:
            # get the html with xpath or css as a fallback, move the cursor to it
            try:
                if selector.startswith('/') or selector.startswith('(/') or selector.startswith('//'):
                    new_parent = WebDriverWait(parent_element, timeout=10).until(
                        lambda d: d.find_elements(By.XPATH, selector))
                else:
                    raise Exception('')
            except (Exception,):
                new_parent = WebDriverWait(parent_element, timeout=10).until(
                    lambda d: d.find_elements(By.CSS_SELECTOR, selector))
            self.move_to_element(new_parent[index])

            # take a screenshot
            with suppress(Exception):
                screenshot_data = {
                    'uuid': new_parent[index].id,
                    'image': self.web.driver.get_screenshot_as_base64()
                }
                self.web.screenshots.append(screenshot_data)
                if self.web.config['DEFAULT'].get('SCREENSHOTS', False) in ['True', 'true', '1', True]:
                    self.web.driver.save_screenshot(os.path.join(os.path.dirname(__file__), '../..', '..', f'screenshots/{new_parent[index].id}.png'))
            return new_parent[index]
        except (Exception,):
            raise Exception(f'Could not identify element with selector {selector}.')

    def get_html_element(self, element: InputAttribute, parent_element=None, element_index=None):
        """ Returns the html element associated to an element.

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
            parent_element: WebDriverElement
                the parent html element of the element that is identified
            element_index: Number
                the index of the html element
                if not specified or None, the index will be 0

            Returns
            -------
            WebDriverElement
                the html element associated to the element
        """
        try:
            if parent_element is None:
                parent_element = self.web.driver
            selector, index = self.handle_selector(element)
            if element_index is not None:
                index = element_index
            if selector is None:
                return
            html_element = self.identify_element(selector, parent_element, index)
            return html_element
        except (Exception,):
            raise Exception(f'Could not find element {element.friendly} in page.')

    def click_element(self, html_element):
        """ Clicks a html element. \n
            Moves the cursor on the element.
            Tries to click the element, until it is successfully clicked or until the timeout expires.
            Throws an exception if the element couldn't be clicked.

            Parameters
            ----------
            html_element: WebDriverElement
                the html element that gets clicked
        """
        self.move_to_element(html_element)
        start_time = time.perf_counter()
        while time.perf_counter() - start_time <= 10:
            try:
                ActionChains(driver=self.web.driver).click(html_element).perform()
                return
            except (Exception,):
                time.sleep(0.5)
        raise Exception(f'Element {html_element["friendly"]} is not clickable')

    def get_value_from_html_element(self, element: InputAttribute, parent_element=None, element_index=None):
        """ Gets the value from a html element.\n
            Supported element types: input, dropdown, plain text.

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
            parent_element: WebdriverElement
                parent html element of the current element
                if absent or None, it takes the default value
            element_index: Number
                the index of element in the page,
                if there are multiple elements with the same selector

            Returns
            -------
            string
                the value of the html element, as a string
        """
        try:
            if not parent_element:
                parent_element = self.web.driver

            # inputs
            with suppress(Exception):
                html_element = self.get_html_element(element, parent_element, element_index)
                if html_element.get_attribute('value') is not None:
                    return html_element.get_attribute('value')

            # dropdowns
            with suppress(Exception):
                html_element = Select(self.get_html_element(element, parent_element, element_index))
                if html_element.first_selected_option.text is not None:
                    return html_element.first_selected_option.text

            # plain text
            with suppress(Exception):
                html_element = self.get_html_element(element, parent_element, element_index)
                with suppress(Exception):
                    self.check_contrast(html_element)
                if html_element.text is not None:
                    return html_element.text

            return None
        except Exception as e:
            raise Exception(f'Could not get value from html element. Error: {e}')

    def set_attribute_property(self, attribute_id, column, value, attribute_instance_index=None, node_instance_index=None):
        same_attribute_id = (SuiteAttributes.df['attributeId'] == attribute_id)
        same_attribute_index = (SuiteAttributes.df['attribute_instance_index'] == attribute_instance_index) if attribute_instance_index is not None else pd.Series(True, index=SuiteAttributes.df.index)
        same_node_index = (SuiteAttributes.df['node_instance_index'] == node_instance_index) if node_instance_index is not None else pd.Series(True, index=SuiteAttributes.df.index)
        SuiteAttributes.df.loc[(same_attribute_id & same_attribute_index & same_node_index), column] = value

    def check_contrast(self, html_element):
        """ Given a html element, calculates its contrast.
            If there is a problem with the contrast, a warning
            is added to the warnings variable from Web class.

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element
        """
        foreground = html_element.value_of_css_property('color')
        background = self.get_bg_color(html_element)

        f_r, f_g, f_b, f_a = self.get_rgba_values_from_string(foreground)
        b_r, b_g, b_b, b_a = self.get_rgba_values_from_string(background)

        f_l = self.get_relative_luminance(f_r, f_g, f_b)
        b_l = self.get_relative_luminance(b_r, b_g, b_b)
        if f_l >= b_l:
            contrast = (f_l + 0.05) / (b_l + 0.05)
        else:
            contrast = (b_l + 0.05) / (f_l + 0.05)
        validation_warning = self.validate_contrast_ratio(html_element, contrast)
        if validation_warning:
            self.web.warnings.append(validation_warning)

    def validate_contrast_ratio(self, html_element, contrast):
        """ Given a html element, and its contrast,
            check if it has a valid contrast based on
            these guidelines:
            https://www.w3.org/TR/WCAG20

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element
            contrast: Number
                the contrast value of the html_element

            Return
            ---------
            message: String
                None if the contrast ratio is valid, else a message
                that explains why the contrast is not suitable
        """
        text = html_element.text
        if contrast <= 1.5:
            return f'Text {text} is unreadable because if has a contrast of {contrast}'

        is_large_text = self.is_large_text(html_element)
        if is_large_text and contrast < 3.0:
            return f'Text {text} does not meet the AA contrast requirements, with a contrast of {contrast}'
        if not is_large_text and contrast < 4.5:
            return f'Text {text} does not meet the AA contrast requirements, with a contrast of {contrast}'

        return None

    @staticmethod
    def is_large_text(html_element):
        """ Given a html element, checks if the text of
            the html is large or not, based on this conditions:
            https://www.w3.org/TR/WCAG20/#larger-scaledef

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element

            Return
            ---------
            is_large_text: Bool
                True if the text is large, else False
        """
        font_size = html_element.value_of_css_property('font-size').replace('px', '').replace('em', '')
        if int(font_size) >= 18:
            return True
        elif int(font_size) >= 14:
            font_weight = html_element.value_of_css_property('font-weight')
            if int(font_weight) >= 700:
                return True
        return False

    @staticmethod
    def get_bg_color(html_element):
        """ Given a html element, returns the background
            color of the element. If the element has a transparent
            background color, its parents are searched for a solid value.

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element

            Return
            ---------
            background_color: String
                the background color as a string ('rgba(120,255,255,1')
        """
        while True:
            color = html_element.value_of_css_property('background-color')
            if color not in ['rgba(0, 0, 0, 0)', 'transparent', '']:
                return color
            else:
                html_element = html_element.find_element(By.XPATH, './..')
            if html_element.tag_name == 'body':
                return None

    @staticmethod
    def get_rgba_values_from_string(string_rgba):
        """ Extracts the rgba values from a string like
            'rgba(120,255,255,1)' or similar

            Parameters
            ----------
            string_rgba: String
                color value as string

            Return
            ---------
            values: List
                a list of red, green, blue and alpha values
        """
        string_rgba = string_rgba.replace('rgba', '').replace(' ', '').replace('(', '').replace(')', '')
        return [int(value) for value in string_rgba.split(',')]

    def get_relative_luminance(self, r, g, b):
        """ Given the (r,g,b) values of a color,
            returns the relative luminance of the color. \n
            https://www.w3.org/TR/WCAG20/#relativeluminancedef

            Parameters
            ----------
            r: Number between 0 and 255
                red value of the color
            g: Number between 0 and 255
                green value of the color
            b: Number between 0 and 255
                blue value of the color

            Return
            ---------
            l: Number
                the relative luminance of a (r,g,b) color
        """
        r = self.normalize_rgb_value(r)
        g = self.normalize_rgb_value(g)
        b = self.normalize_rgb_value(b)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @staticmethod
    def normalize_rgb_value(value):
        """ Given the value of a color,
            returns the normalized value. \n
            https://www.w3.org/TR/WCAG20/#relativeluminancedef

            Parameters
            ----------
            value: Number between 0 and 255
                the red/green/blue value of a rgb color

            Return
            ---------
            value: Number
                the normalized value
        """
        value = value/255
        if value < 0.03928:
            return value / 12.92
        else:
            return pow(value, 2.4)

    def move_to_element(self, html_element):
        """ Given a html_element, the element
            is scrolled into view and the cursor is moved on its
            center. If slow mode is off, selenium waits
            250ms for the element to be visible and clickable.

            Parameters
            ----------
            html_element:
                webdriver html element
        """
        duration = 250 if self.web.config['DEFAULT'].get('SLOW_MODE', True) in ['True', 'true', '1', True] else 0

        # scroll to the element
        self.web.driver.execute_script("arguments[0].scrollIntoView();", html_element)

        # wait until the element is scrolled into view
        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) <= 10:
            with suppress(Exception):
                ActionChains(self.web.driver, duration=duration).move_to_element(html_element).perform()
                return
            time.sleep(1/2)

    def click_element_until_value(self, attribute, value, format_attribute, current_value=None):
        """ Clicks on an element until the desired attribute value is achieved. \n
            Searches for elements that modifies the value of the attribute.
            Chooses the appropriate element, in order to get to the desired value.
            Clicks the element until the value is achieved.
            Parameters
            ----------
            attribute: Series
                attribute data, row from attributes dataframe
            value: Number
                the desired value of the attribute
            format_attribute: String
                the sub_attribute of the format (ex.: attribute_name.year)
            current_value: Number
                if given, this will be the initial value, instead of taking
                the initial value from the attribute or searching it
                in the page
        """
        attribute_type = format_attribute.split('.')[-1].lower()
        if attribute['friendly'] == format_attribute:
            meta_attribute_name = '{' + attribute['friendly'] + '}'
        else:
            meta_attribute_name = '{' + attribute['friendly'] + '.' + format_attribute + '}'
        elements = InputAttributes.df[InputAttributes.df['elementOptions.meta'].str.contains(meta_attribute_name) == True]
        initial_value = self.get_initial_values(elements, attribute_type, attribute)
        if current_value is not None:
            initial_value = current_value
        elif initial_value is not None:
            initial_value = self.initial_value_to_int(initial_value)

        if initial_value is None:
            element = elements[elements['elementOptions.meta'] == meta_attribute_name].iloc[0]
        elif value < initial_value:
            element = elements[elements['elementOptions.meta'].str.contains('-')].iloc[0]
        elif value > initial_value:
            element = elements[elements['elementOptions.meta'].str.contains('\+')].iloc[0]
        else:
            element = None

        try:
            if value == initial_value:
                element = elements[elements['elementOptions.meta'] == meta_attribute_name].iloc[0]
                html_element = self.get_html_element(element, self.web.driver)
                self.click_element(html_element)
                return
        except (Exception,):
            pass

        if element is not None:
            if initial_value is not None:
                step = int(element['elementOptions.meta'].replace(meta_attribute_name, '').replace('+', '').replace('-', '').strip())
                value = abs(value - initial_value)//step * step + initial_value
                clicks_nr = abs(value - initial_value) // step
                for i in range(clicks_nr):
                    # set the new value of attribute
                    SuiteAttributes.update(attributeId=attribute['attributeId'], update_column='attributeValue', update_value=Fake(initial_value + (i+1)*step))
                    attribute['attributeValue'] = Fake(initial_value + (i+1)*step)
                    self.handle_button_as_button(element)

    def get_initial_values(self, elements, format_attribute, attribute, composed_attribute=True):
        """ Searches for an element that specifies the value of a format attribute
            and gets the value from the associated html_element. \n

            Parameters
            ----------
            elements: Dataframe
                dataframe with elements that modify/specify data about the format attribute value
            format_attribute: String
                the sub_attribute of the format (ex.: attribute_name.year)
            attribute: Series
                attribute data, row from attributes dataframe
            composed_attribute: Bool
                whether it is a sub-attribute of a bigger attribute and the
                meta has the format 'attribute.sub-attribute'.
                Default is True

            Returns
            -------
            string
                string value of the attribute from the page
        """
        try:
            if composed_attribute:
                element = elements[elements['elementOptions.meta'] == '{' + attribute['friendly'] + '.' + format_attribute + '}'].iloc[0]
            else:
                element = elements[elements['elementOptions.meta'] == '{' + format_attribute + '}'].iloc[0]
            return self.get_value_from_html_element(element)
        except (Exception,):
            return None

    @staticmethod
    def initial_value_to_int(initial_value):
        """ Converts a string value to int. \n
            If the value is a month, returns the month index.

            Parameters
            ----------
            initial_value: String
                string value

            Returns
            -------
            int
                the string value converted to int
        """
        if initial_value in list(calendar.month_name):
            return list(calendar.month_name).index(initial_value)
        return int(initial_value)
