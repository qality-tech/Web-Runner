import random
import string
from contextlib import suppress
from datetime import datetime

from Utils.Models.Repository import *
from Utils.Common.Fake import Fake
from Utils.Common.ExtendedFaker import ExtendedFaker


class DataGenerators:
    def __init__(self):
        self.faker = ExtendedFaker().faker

    def make_number(self, element=None, properties=None):
        if properties is None:
            properties = {'min': -1000, 'max': 1000, 'to_exclude': []}

        if 'value' in properties:
            return properties['value']
        if 'to_exclude' not in properties:
            properties['to_exclude'] = []

        with suppress(Exception,):
            return random.choice([i for i in range(properties['min'], properties['max'] + 1) if i not in properties['to_exclude']])
        return 0

    def make_string(self, N=None, element=None, properties=None):
        if N is None:
            N = 10
        if properties is None:
            properties = {'to_exclude': []}

        if 'value' in properties:
            return properties['value']
        if 'to_exclude' not in properties:
            properties['to_exclude'] = []

        faker_config = self.get_faker_config_from_element(element)
        if element is None or faker_config is None:
            return ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))
        else:
            try:
                return getattr(self.faker, faker_config)()
            except:
                with suppress(Exception):
                    attributes = getattr(self.faker, faker_config.split('_')[0])()
                    return attributes[faker_config.split('_')[1]]

        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))

    def get_faker_config_from_element(self, element):
        try:
            for attribute in SuiteAttributes.get_all(attributeId=element.attributeId):
                if attribute.fakerApiConfig is not None:
                    return attribute.fakerApiConfig
            return None
        except(Exception,):
            return None

    def make_bool(self, element=None, properties=None):
        return random.randint(0, 1) == 1

    def make_date(self, format="%Y-%m-%d %H:%M:%S.%f", element=None, properties=None):
        current_time = datetime.now(tz=None)
        to_return = current_time.strftime(format)
        return to_return

    def make_object(self, element=None, properties=None):
        try:
            try:
                attrribute_type = element.attribute_type
            except:
                reference_attribute_id = element.referenceAttribute
                attrribute_type = SuiteAttributes.get(attributeId=reference_attribute_id).attribute_type
            return Fake(DataTypes.get(typeId=attrribute_type).method(element=element, properties=properties))
        except:
            return self.make_string(properties)

    def make_date_between_two_dates(self, start, end):
        return self.faker.date_time_between(start_date=start, end_date=end)

    def make_email(self, element=None, properties=None):
        return self.faker.email()

    def make_phone(self, element=None, properties=None):
        return self.faker.phone_number().split('x')[0]
