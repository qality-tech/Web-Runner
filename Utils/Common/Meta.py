from datetime import datetime
import calendar

from Utils.Models.Repository import *


# noinspection PyUnusedLocal
class Meta:
    def __init__(self, helpers, tech_class):
        self.h = helpers
        self.tech_class = tech_class
        self.methods = {
            'capitalize': self.capitalize,
            'uppercase': self.uppercase,
            'replace_underscore': self.replace_underscore_with_space,
            'replace_underscore_with_space': self.replace_underscore_with_space,
            'replace_underscore_with_comma': self.replace_underscore_with_comma,
            'replace_underscore_with_period': self.replace_underscore_with_period,
            'strftime': self.date_strftime,
            'bool_to_int': self.bool_to_int,
            'int_to_bool': self.int_to_bool,
            'bearer_token': self.bearer_token,
            'str_to_int': self.str_to_int,
            'to_string': self.to_string
        }
        self.conditions = {
            'date': {
                'today': 0,
                'tomorrow': 1,
                'yesterday': -1,
                'next_week': 7,
                'last_week': -7,
                'next_year': 365,
                'previous_year': -365,
                'end_of_month': calendar.monthrange(datetime.now().year, datetime.now().month)[
                                    1] - datetime.now().day + 1
            }
        }

    def handle_meta_attribute(self, meta, attribute_value, attribute_id):
        """ Applies metas over an attribute value. \n
            - splits the meta, in case there are multiple metas
            - sanitizes each meta and calls the desired method from the Meta class

            Parameters
            ----------
            meta: String
                string defining a meta or a list of metas (ex.: "replace_underscore_with_space, capitalize")
            attribute_value: String
                the value on which the metas will be applied
            attribute_id: Number
                the id of the attribute we're applying the meta on

            Returns
            -------
            string
                the new attribute value with applied metas
        """
        if meta is None:
            return attribute_value
        metas = self.split_meta(meta)
        for meta in metas:
            meta_name = meta.strip()
            if 'strftime' in meta_name:
                meta_name = 'strftime'
            meta_to_call = self.methods.get(meta_name)
            if meta_to_call:
                attribute_value = meta_to_call(meta, attribute_value, attribute_id)
        return attribute_value

    @staticmethod
    def split_meta(meta):
        """ Splits a string of metas.

            Parameters
            ----------
            meta: String
                string defining a meta or a list of metas (ex.: "replace_underscore_with_space, capitalize")

            Returns
            -------
            list
                list of the split metas (ex.: ["replace_underscore_with_space", "capitalize"])
        """
        single_quotes = 0
        double_quotes = 0
        new_string = ""
        unique_separator = 'd0n0tm4tch'
        for index, c in enumerate(meta):

            if c == ',':
                if single_quotes % 2 == 0 and double_quotes % 2 == 0:
                    new_string += unique_separator
                    continue
            elif c == '\'':
                single_quotes += 1
            elif c == '\"':
                double_quotes += 1
            new_string += c
        return new_string.split(unique_separator)

    @staticmethod
    def capitalize(meta, value, attribute_id):
        return value.capitalize()

    @staticmethod
    def uppercase(meta, value, attribute_id):
        return value.upper()

    @staticmethod
    def replace_underscore_with_space(meta, value, attribute_id):
        return value.replace('_', ' ')

    @staticmethod
    def replace_underscore_with_comma(meta, value, attribute_id):
        return value.replace('_', ',')

    @staticmethod
    def replace_underscore_with_period(meta, value, attribute_id):
        return value.replace('_', '.')

    @staticmethod
    def to_string(meta, value, attribute_id):
        return str(value)

    @staticmethod
    def bool_to_int(meta, value, attribute_id):
        if type(value) == bool and value:
            return 1
        if type(value) == bool and not value:
            return 0

        if type(value) == str and value.lower() in ['True', 'true', '1']:
            return 1
        if type(value) == str and value.lower() in ['False', 'false', '0']:
            return 0
        return value

    @staticmethod
    def int_to_bool(meta, value, attribute_id):
        if value == 1:
            return True
        if value == 0:
            return False
        return value

    @staticmethod
    def str_to_int(meta, value, attribute_id):
        return int(value)

    @staticmethod
    def bearer_token(meta, value, attribute_id):
        return f"Bearer {value}"

    def date_strftime(self, meta, value, attribute_id):
        """ Converts a date and time into a given format. \n
            Gets the date value from an attribute. Based on the attribute date format,
            extracts year, month, etc. Creates a new date based on the desired format.

            Parameters
            ----------
            meta: String
                the desired format, a strftime instruction (ex: strftime(%Y %d %m))
            value: String
                the date value that will be converted to the new format
            attribute_id: Number
                the id of the date attribute
        """

        attribute = SuiteAttributes.to_model(self.h.get_attribute_or_main_attribute(attribute_id, node_instance_index=1, actor=self.tech_class.actor).attribute)
        try:
            date_format = self.tech_class.rules_handler.get_date_format_from_attribute(attribute)
        except (Exception,):
            date_format = "{day}.{month}.{year}"
        format_attributes = self.tech_class.rules_handler.get_attributes_from_value_with_format(value, date_format)
        date = datetime.now().replace(**format_attributes)
        return eval(f"date.{meta}")
