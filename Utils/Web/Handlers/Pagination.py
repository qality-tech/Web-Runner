import json
import math
import random

from Utils.Common.Fake import Fake
from Utils.Models.Repository import *

class Pagination:
    def __init__(self, component: Component, helpers, handlers):
        # TODO: a better idea could be to make a model out of this
        self.h = helpers
        self.handlers = handlers
        self.component = component
        self.settings = json.loads(component.componentSettings)
        self.current_page_number = 1
        self.no_of_pages = None
        self.items_per_page = None
        self.no_of_results = None
        self.pages_to_test = [1]

        # general settings
        self.maximum_number_of_pages = self.settings['maximumNumberOfPagesVisible']
        self.previous_page_element_id = self.settings['previousPageElementId']
        self.next_page_element_id = self.settings['nextPageElementId']

        self.current_page_element_id = self.settings['pageElementId']
        # TODO: manareala (to add this option in WUI)
        element = InputAttributes.get(id=self.current_page_element_id)
        self.current_page_object_id = element.original_object_id
        self.current_page_attribute_id = element.attributeId

        # total number of results
        self.total_number_of_results_element_id = self.settings['totalNumberOfResults']['elementId'] if 'elementId' in self.settings['totalNumberOfResults'] else None
        self.total_number_of_results_element_type = self.settings['totalNumberOfResults']['elementType']
        self.total_number_of_results_object_id = self.settings['totalNumberOfResults']['objectId']
        self.total_number_of_results_attribute_id = self.settings['totalNumberOfResults']['attributeId']

        # items per page
        self.items_per_page_element_id = self.settings['itemsPerPage']['elementId'] if 'elementId' in self.settings['itemsPerPage'] else None
        self.items_per_page_element_type = self.settings['itemsPerPage']['elementType']
        # TODO: manareala (to add this option in WUI)
        element = InputAttributes.get(id=self.items_per_page_element_id) if self.items_per_page_element_type == 'ELEMENT' else ElementsGroups.get(id=self.items_per_page_element_id)
        self.items_per_page_object_id = element.original_object_id
        self.items_per_page_attribute_id = element.attributeId

        # page number
        self.page_number_element_id = self.settings['pageNumber']['elementId'] if 'elementId' in self.settings['pageNumber'] else None
        self.page_number_element_type = self.settings['pageNumber']['elementType']

        # first page
        self.first_page_element_id = self.settings['firstPage']['elementId'] if 'elementId' in self.settings['firstPage'] else None
        self.first_page_element_type = self.settings['firstPage']['elementType']
        self.first_page_dynamic = self.settings['firstPage']['dynamic']

        # last page
        self.last_page_element_id = self.settings['lastPage']['elementId'] if 'elementId' in self.settings['lastPage'] else None
        self.last_page_element_type = self.settings['lastPage']['elementType']
        self.last_page_dynamic = self.settings['lastPage']['dynamic']

        # TODO add no_of_pages element and attribute id in WUI

    def calculate_missing_value(self):
        if self.no_of_pages is None:
            if self.items_per_page is not None and self.no_of_results:
                self.no_of_pages = max(1, self.no_of_results // self.items_per_page)

        if self.no_of_results is None:
            if self.items_per_page is not None and self.no_of_pages is not None:
                self.no_of_results = self.items_per_page * (self.no_of_pages - 1)

    def calculate_pages_to_test(self):
        if self.handlers.web.config['DEFAULT'].get('PARTIAL_TESTING', False) in ['True', 'true', '1', True] and self.no_of_pages is not None:
            testing_percent = int(self.handlers.web.config['DEFAULT'].get('PARTIAL_TESTING_PERCENT', 50))
            self.pages_to_test = random.sample(range(1, self.no_of_pages + 1), math.ceil(testing_percent * self.no_of_pages / 100))
            self.pages_to_test.sort()
        elif self.no_of_pages is not None:
            self.pages_to_test = [i for i in range(1, self.no_of_pages + 1)]

    def validate(self):
        # total number of results
        self.validate_total_number_of_results()
        # items per page
        self.validate_items_per_page()
        # current page
        self.validate_current_page()

        # calculate missing values based on the other values, if possible
        self.calculate_missing_value()
        # calculate the pages that need to be tested
        self.calculate_pages_to_test()


    def validate_total_number_of_results(self):
        frontend_value = None
        backend_value = None

        if self.total_number_of_results_element_id is not None and self.total_number_of_results_element_type == 'ELEMENT':
            total_number_of_results_element = InputAttributes.get(id=self.total_number_of_results_element_id)
            if total_number_of_results_element is not None:
                frontend_value = self.handlers.get_value_from_html_element(total_number_of_results_element)

        if self.total_number_of_results_object_id is not None and self.total_number_of_results_attribute_id is not None:
            backend_value = SuiteAttributes.get(parent_object_id=self.total_number_of_results_object_id,
                                                attributeId=self.total_number_of_results_attribute_id).attributeValue
            backend_value = backend_value.value if type(backend_value) == Fake else backend_value

        if frontend_value is not None and backend_value is not None:
            if int(frontend_value) != int(backend_value):
                raise Exception('Total number of results is not displayed correctly in the page')

        if frontend_value is not None:
            self.no_of_results = int(frontend_value)
        elif backend_value is not None:
            self.no_of_results = int(backend_value)

    def validate_items_per_page(self):
        frontend_value = None
        backend_value = None

        if self.items_per_page_element_id is not None and self.items_per_page_element_type == 'ELEMENT':
            items_per_page_element = InputAttributes.get(id=self.items_per_page_element_id)
            if items_per_page_element is not None:
                frontend_value = self.handlers.get_value_from_html_element(items_per_page_element)

        if self.items_per_page_object_id is not None and self.items_per_page_attribute_id is not None:
            backend_value = SuiteAttributes.get(parent_object_id=self.items_per_page_object_id,
                                                attributeId=self.items_per_page_attribute_id).attributeValue
            backend_value = backend_value.value if type(backend_value) == Fake else backend_value

        if frontend_value is not None and backend_value is not None:
            if int(frontend_value) != int(backend_value):
                raise Exception('Items per page is not displayed correctly in the page')

        if frontend_value is not None:
            self.items_per_page = int(frontend_value)
        elif backend_value is not None:
            self.items_per_page = int(backend_value)

    def validate_pages_actions(self):
        pass

    def validate_current_page(self):
        frontend_value = None

        if self.current_page_element_id is not None:
            current_page_element = InputAttributes.get(id=self.current_page_element_id)
            if current_page_element is not None:
                frontend_value = self.handlers.get_value_from_html_element(current_page_element)

        if self.current_page_object_id is not None and self.current_page_attribute_id is not None:
            backend_value = SuiteAttributes.get(parent_object_id=self.current_page_object_id,
                                                attributeId=self.current_page_attribute_id).attributeValue
            backend_value = backend_value.value if type(backend_value) == Fake else backend_value
        else:
            backend_value = self.current_page_number

        if frontend_value is not None and backend_value is not None:
            if int(frontend_value) != int(backend_value):
                raise Exception('Current is not displayed correctly in the page')

        if frontend_value is not None:
            self.current_page_number = int(frontend_value)
        elif backend_value is not None:
            self.current_page_number = int(backend_value)

    def next_page(self):
        if self.next_page_element_id is None:
            return
        next_page_element = InputAttributes.get(id=self.next_page_element_id)
        self.handlers.web.validators.validate_element(next_page_element)
        self.current_page_number += 1
        if self.current_page_attribute_id is not None and self.current_page_object_id is not None:
            SuiteAttributes.update(attributeId=self.current_page_attribute_id, parent_object_id=self.current_page_object_id,
                                   update_column='attributeValue', update_value=Fake(self.current_page_number))
        self.validate_current_page()

    def previous_page(self):
        if self.previous_page_element_id is None:
            return
        previous_page_element = InputAttributes.get(id=self.previous_page_element_id)
        self.handlers.web.validators.validate_element(previous_page_element)
        self.current_page_number -= 1
        if self.current_page_attribute_id is not None and self.current_page_object_id is not None:
            SuiteAttributes.update(attributeId=self.current_page_attribute_id, parent_object_id=self.current_page_object_id,
                                   update_column='attributeValue', update_value=Fake(self.current_page_number))
        self.validate_current_page()

    def go_to_first_page(self):
        if self.first_page_element_id is None:
            self.go_to_page(1)
            return
        if self.first_page_element_type == 'ELEMENT':
            first_page_element = InputAttributes.get(id=self.first_page_element_id)
            self.handlers.web.validators.validate_element(first_page_element)
        else:
            first_page_element = ElementsGroups.get(id=self.first_page_element_id)
            self.handlers.web.validators.validate_element_group(first_page_element)

        self.current_page_number = 1
        SuiteAttributes.update(attributeId=self.current_page_attribute_id, parent_object_id=self.current_page_object_id,
                               update_column='attributeValue', update_value=Fake(self.current_page_number))
        self.validate_current_page()

        if self.first_page_dynamic:
            # TODO
            pass

    def go_to_last_page(self):
        if self.last_page_element_id is None:
            self.go_to_page(self.no_of_pages)
            return
        if self.last_page_element_type == 'ELEMENT':
            last_page_element = InputAttributes.get(id=self.last_page_element_id)
            self.handlers.web.validators.validate_element(last_page_element)
        else:
            last_page_element = ElementsGroups.get(id=self.last_page_element_id)
            self.handlers.web.validators.validate_element_group(last_page_element)

        self.current_page_number = self.no_of_pages
        SuiteAttributes.update(attributeId=self.current_page_attribute_id, parent_object_id=self.current_page_object_id,
                               update_column='attributeValue', update_value=Fake(self.current_page_number))
        self.validate_current_page()

        if self.last_page_dynamic:
            # TODO
            pass

    def go_to_page(self, page_no):
        if page_no == self.current_page_number:
            return
        while page_no < self.current_page_number:
            self.previous_page()
        while page_no > self.current_page_number:
            self.next_page()
