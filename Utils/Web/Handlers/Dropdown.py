import logging
import math
import random

from Utils.Models.Repository import *

class Dropdown:
    def __init__(self, element: InputAttribute, handlers, h, web):
        self.element = element
        self.handlers = handlers
        self.h = h
        self.web = web
        self.option_element = None
    
    def validate(self, parent_element=None):
        if parent_element is None:
            parent_element = self.handlers.web.driver
        try:
            # open the dropdown
            html_element = self.handlers.get_html_element(self.element, parent_element)
            self.handlers.click_element(html_element)

            # if the element is prepopulated, check its values with the one from backend
            if self.element.prepopulated and self.element.attributeId:
                attribute_value = self.h.get_attribute_or_main_attribute(self.element.attributeId, actor=self.web.actor).value
                input_value = self.handlers.get_value_from_html_element(self.element, parent_element)
                if str(attribute_value) != str(input_value):
                    pass  # TODO: fix this, has to be applied meta over the attribute
                    # raise Exception(f'Prepopulated value {attribute_value} differs from {input_value}.')

            # get the element that represents the dropdown option
            if self.element.dropdown_option_element is None:
                raise Exception(f'Dropdown option element not found for {self.element.friendly}.')
            self.option_element = InputAttributes.get(id=self.element.dropdown_option_element)

            # if options of this dropdown come from an api request, check them to be the same
            self.check_dropdown_options(html_element)

            if self.handlers.web.missing_value_entity_id is None or self.element.id != self.handlers.web.missing_value_entity_id:
                required = random.choice([True, False])
                if self.element.required:
                    required = True
                if required:
                    # select a random option of the dropdown
                    subtype_selector, element_index = self.handlers.handle_selector(self.option_element, random_index=True, update_attribute=True)
                    option = self.handlers.identify_element(subtype_selector, parent_element, element_index)
                    if option.size['width'] == 0 and option.size['height'] == 0:
                        self.handlers.click_element(html_element)
                    self.handlers.click_element(option)

        except Exception as e:
            message = f'Dropdown interaction failed for {self.element.friendly}. {e}'
            raise Exception(message)

    def check_dropdown_options(self, html_element):
        """ Validates the options of a dropdown, if the options come from api. \n
            If an option is not present, an error is raised.

            Parameters
            ----------
            html_element: Webdriver element
                webdriver html element
        """
        logging.debug(f'Begin check dropdown options for element {self.element.friendly}')

        dropdown_options = []
        index = 1
        while True:
            try:
                subtype_selector, element_index = self.handlers.handle_selector(
                    self.option_element, attribute_instance_index=index, random_index=False)
                dropdown_options.append({'selector': subtype_selector, 'element_index': element_index})
                index += 1
            except (Exception,):
                break

        options_to_test = []
        if self.handlers.web.config['DEFAULT'].get('PARTIAL_TESTING', False) in ['True', 'true', '1', True]:
            percent = int(self.handlers.web.config['DEFAULT'].get('PARTIAL_TESTING_PERCENT', 50))
            options_to_test = random.sample(range(0, len(dropdown_options)),
                                            math.ceil(percent * len(dropdown_options) / 100))

        for i in range(len(dropdown_options)):
            if options_to_test == [] or i in options_to_test:
                try:
                    option = self.handlers.identify_element(
                        dropdown_options[i]['selector'], html_element, dropdown_options[i]['element_index'])
                    if option.size['width'] == 0 and option.size['height'] == 0:
                        self.handlers.click_element(html_element)
                    index += 1
                except Exception as e:
                    message = f'Dropdown options validation failed for {self.element.friendly}.'
                    logging.debug(f'{message} {e}')
                    raise Exception(message)
        logging.debug(f'End check dropdown options for element {self.element.friendly}')
