import random
import re
from contextlib import suppress
from datetime import datetime
from Utils.Common.DataGenerators import DataGenerators

from Utils.Models.Repository import *

import numpy as np

from Utils.Common.Fake import Fake


class RulesHandler:
    def __init__(self, helpers, tech_class=None):
        self.h = helpers
        self.tech_class = tech_class
        self.dataGenerators = DataGenerators()

    def handle_condition(self, element: Component | ElementsGroup | InputAttribute | SuiteAttribute, element_col='existenceCondition', node_instance_index=1):
        """ Handles the simple and complex rules of an element/element group/component. \n
            Checks if the element creates values or if there are already values created for this element.

            Parameters
            ----------
            element: Series
                element/element group/component data, a row from the dataframes
            element_col: String, optional
                the column of the element with the rule id
            node_instance_index: Number, optional
                the node instance of this test step
        """

        if getattr(element, element_col) is None or np.isnan(getattr(element, element_col)):
            return

        simple_rules = SimpleRules.get_all(id=getattr(element, element_col))
        if simple_rules is not None and len(simple_rules) > 0:
            try:
                rule_result = self.handle_simple_rules(simple_rules, in_use=True)
                if not rule_result:
                    raise Exception(f'Rule {simple_rules[0].friendly} not satisfied for {element.friendly}')
            except (Exception,):
                raise Exception(f'Rule {simple_rules[0].friendly} not satisfied for {element.friendly}')

        complex_rules = ComplexRules.get_all(id=getattr(element, element_col))
        if complex_rules is not None and len(complex_rules) > 0:
            try:
                rule_result = self.handle_complex_rules(complex_rules, in_use=True)
                if not rule_result:
                    raise Exception(f'Rule {complex_rules[0].friendly} not satisfied for {element.friendly}')
            except (Exception,):
                raise Exception(f'Rule {complex_rules[0].friendly} not satisfied for {element.friendly}')

    def handle_simple_rules(self, rules: list, value=None, node_instance_index=1, in_use=False):
        """ Handles simple validation rules. \n
            Evaluates the simple rule, using its attribute value, operator and comparison value.

            Parameters
            ----------
            rules: List
            value:
                the attribute value, in case it is not taken from suiteAttributes, default is None
            node_instance_index: Number
                the node index of the attribute
            in_use: Bool
                whether the attribute value should be the one that is currently used,
                useful for dropdowns

            Returns
            -------
            bool
                True if the simple rule is satisfied, False otherwise
        """
        current_group_index = 1
        result_per_group = {}
        outer_group_operators = {}
        while True:
            rules_in_group = [rule for rule in rules if rule.group_index == current_group_index]
            if len(rules_in_group) == 0:
                break

            outer_group_operators[current_group_index] = rules_in_group[0].group_operator
            inner_group_operator = rules_in_group[0].inner_group_operator
            group_results = []
            for rule in rules_in_group:
                rule_result = False
                value = None
                with suppress(Exception,):
                    # TODO: manareala
                    attribute = SuiteAttributes.get(attributeId=rule.attribute_id)
                    if attribute and attribute.friendly == 'actor_name':
                        value = self.tech_class.current_actor_name

                    if value is None:
                        if in_use:
                            attribute_value = self.h.get_attribute_or_main_attribute(rule.attribute_id, node_instance_index=node_instance_index, in_use=True, actor=self.tech_class.actor).value
                            if attribute_value is None:
                                attribute_value = self.h.get_attribute_or_main_attribute(rule.attribute_id, node_instance_index=node_instance_index, actor=self.tech_class.actor).value
                        else:
                            attribute_value = self.h.get_attribute_or_main_attribute(rule.attribute_id, node_instance_index=node_instance_index, actor=self.tech_class.actor).value
                    else:
                        attribute_value = value
                    if type(attribute_value) == Fake:
                        attribute_value = attribute_value.value

                    # get attribute type
                    attribute_type = DataTypes.get(typeId=rule.attribute_type).friendly
                    rule_result = self.check_simple_rule(attribute_type, attribute_value, rule.value_to_compare, rule.operator)

                group_results.append(rule_result)
                if inner_group_operator in ['AND', 'NONE'] and not rule_result:
                    result_per_group[current_group_index] = False
                    break
                elif inner_group_operator == 'OR' and rule_result:
                    result_per_group[current_group_index] = True
                    break
            if current_group_index not in result_per_group:
                if inner_group_operator == 'OR':
                    result_per_group[current_group_index] = any(group_results)
                else:
                    result_per_group[current_group_index] = all(group_results)
            current_group_index += 1

        if len(result_per_group) == 0:
            return False
        if len(result_per_group) == 1:
            return result_per_group[1]
        current_result = result_per_group[1]
        for group_index in range(2, current_group_index):
            if outer_group_operators[group_index] == 'OR':
                if current_result or result_per_group[group_index]:
                    current_result = True
                else:
                    current_result = False
            else:
                if current_result and result_per_group[group_index]:
                    current_result = True
                else:
                    current_result = False
        return current_result

    @staticmethod
    def check_simple_rule(attribute_type, value_1, value_2, operator):
        if attribute_type.upper() == 'Number':
            value_1 = float(value_1)
            value_2 = float(value_2)
        elif attribute_type.upper() == 'Boolean':
            value_1 = value_1.lower() in ['true', '1']
            value_2 = value_2.lower() in ['true', '1']

        try:
            match operator:
                case '>':
                    return value_1 > value_2
                case '<':
                    return value_2 < value_1
                case '==':
                    return value_1 == value_2
                case '>=':
                    return value_1 >= value_2
                case '<=':
                    return value_1 <= value_2
                case '!=':
                    return value_1 != value_2
                case 'null':
                    return value_1 is None or not value_1 or np.isnan(value_1) or value_1.lower in ['null', 'none', 'nan']
                case '!null':
                    return not(value_1 is None or not value_1 or np.isnan(value_1) or value_1.lower in ['null', 'none', 'nan'])
                case 'empty':
                    return not value_1
                case 'MIN':
                    return len(str(value_1)) >= int(value_2)
                case 'MAX':
                    return len(str(value_1)) <= int(value_2)
                case _:
                    return False
        except (Exception,):
            return False

    def handle_complex_rules(self, rules: list, value=None, node_instance_index=1, in_use=False):
        current_group_index = 1
        result_per_group = {}
        outer_group_operators = {}
        while True:
            rules_in_group = [rule for rule in rules if rule.group_index == current_group_index]
            if len(rules_in_group) == 0:
                break

            outer_group_operators[current_group_index] = rules_in_group[0].group_operator
            inner_group_operator = rules_in_group[0].inner_group_operator
            group_results = []
            for rule in rules_in_group:
                simple_rules = SimpleRules.get_all(id=rule.condition_rule_id)
                if not simple_rules or len(simple_rules) == 0:
                    group_results.append(False)
                rule_result = self.handle_simple_rules(simple_rules, value, node_instance_index, in_use)
                group_results.append(rule_result)
                if inner_group_operator in ['AND', 'NONE'] and not rule_result:
                    result_per_group[current_group_index] = False
                    break
                elif inner_group_operator == 'OR' and rule_result:
                    result_per_group[current_group_index] = True
                    break
            if current_group_index not in result_per_group:
                if inner_group_operator == 'OR':
                    result_per_group[current_group_index] = any(group_results)
                else:
                    result_per_group[current_group_index] = all(group_results)
            current_group_index += 1

        if len(result_per_group) == 0:
            return False
        if len(result_per_group) == 1:
            return result_per_group[1]
        current_result = result_per_group[1]
        for group_index in range(2, current_group_index):
            if outer_group_operators[group_index] == 'OR':
                if current_result or result_per_group[group_index]:
                    current_result = True
                else:
                    current_result = False
            else:
                if current_result and result_per_group[group_index]:
                    current_result = True
                else:
                    current_result = False
        return current_result

    def get_date_format_from_attribute(self, attribute: SuiteAttribute) -> str:
        try:
            return DateAttributesConfiguration.get(attributeId=attribute.attributeId).dateFormat
        except (Exception,):
            return '{year}-{month}-{day}'

    def get_date_format_from_attribute_id(self, attribute_id) -> str | None:
        try:
            return DateAttributesConfiguration.get(attributeId=attribute_id).dateFormat
        except (Exception,):
            return None

    def calculate_attributes_based_on_rule(self, rule_id):
        simple_rules = SimpleRules.get_all(id=rule_id)
        if simple_rules and len(simple_rules) > 0:
            return self.calculate_attributes_based_on_simple_rules(rule_id)

        complex_rules = ComplexRules.get_all(id=rule_id)
        if complex_rules and len(complex_rules) > 0:
            return self.calculate_attributes_based_on_complex_rules(rule_id)

    def calculate_attributes_based_on_rules(self, rules):
        if rules is None or len(rules) == 0:
            return None

        # calculate the properties for each rule
        all_properties = []
        for rule in rules:
            all_properties.append(self.calculate_attributes_based_on_rule(rule))

        if len(all_properties) == 0:
            return None

        # combine all the properties
        properties = all_properties[0]
        for properties_for_rule in all_properties[1:]:
            for attribute_name, properties_for_attribute in properties_for_rule.items():
                if attribute_name not in properties:
                    properties[attribute_name] = properties_for_attribute
                    continue
                properties[attribute_name]['min'] = max(properties[attribute_name].get('min', 0), properties_for_attribute.get('min', 0))
                properties[attribute_name]['max'] = min(properties[attribute_name].get('max', 10000), properties_for_attribute.get('max', 10000))
                properties[attribute_name]['to_exclude'] = properties[attribute_name].get('to_exclude', []) + properties_for_attribute.get('to_exclude', [])
                current_value = properties[attribute_name].get('value', None)
                properties['value'] = current_value if current_value is not None else properties_for_attribute.get('value', None)
                for sub_attribute in properties_for_attribute['subAttributes']:
                    properties[attribute_name]['subAttributes'][sub_attribute]['min'] = max(
                        properties[attribute_name]['subAttributes'][sub_attribute].get('min', 0),
                        properties_for_attribute['subAttributes'][sub_attribute].get('min', 0))
                    properties[attribute_name]['subAttributes'][sub_attribute]['max'] = min(
                        properties[attribute_name]['subAttributes'][sub_attribute].get('max', 10000),
                        properties_for_attribute['subAttributes'][sub_attribute].get('max', 10000))
        return properties


    def calculate_attributes_based_on_simple_rules(self, rule_id):
        current_group_index = 1
        attributes_for_each_group = {}
        group_operators = {}
        while True:
            rules = SimpleRules.get_all(id=rule_id, group_index=current_group_index)
            if not rules or len(rules) == 0:
                break

            inner_group_operator = rules[0].inner_group_operator
            if not inner_group_operator or inner_group_operator.upper() == 'NONE':
                inner_group_operator = 'AND'
            # if the group operator is 'AND', all the rules must be satisfied
            # if the group operator is 'OR', at least one rule must be satisfied, so we choose a random one
            if inner_group_operator.upper() == 'OR':
                rules = [random.choice(rules)]
            group_operators[current_group_index] = rules[0].group_operator

            attributes = {}
            for simple_rule in rules:
                attribute_id = simple_rule.attribute_id if simple_rule.reference_attribute is None else simple_rule.reference_attribute
                attribute = SuiteAttributes.get(attributeId=attribute_id)
                attribute_format = self.get_date_format_from_attribute(attribute)

                if attributes.get(attribute.friendly, None) is None:
                    attributes[attribute.friendly] = {'id': attribute_id, 'min': -10000, 'max': 10000, "subAttributes": {}}
                types = {}
                if re.match('{.*}', simple_rule.value_to_compare):
                    if simple_rule.value_to_compare in ['{now}', '{today}', '{{now}}', '{{today}}']:
                        time = datetime.now()
                        types['year'] = time.year
                        types['month'] = time.month
                        types['day'] = time.day
                        types['hour'] = time.hour
                        types['minute'] = time.minute
                        types['second'] = time.second
                    if simple_rule.value_to_compare in ['{now.day}', '{today.day}', '{{now.day}}', '{{today.day}}']:
                        time = datetime.now()
                        types['day'] = time.day
                    if simple_rule.value_to_compare in ['{now.month}', '{today.month}', '{{now.month}}', '{{today.month}}']:
                        time = datetime.now()
                        types['month'] = time.month
                    if simple_rule.value_to_compare in ['{now.year}', '{today.year}', '{{now.year}}', '{{today.year}}']:
                        time = datetime.now()
                        types['year'] = time.year
                else:
                    types = self.get_attributes_from_value_with_format(simple_rule.value_to_compare, attribute_format)

                # base attribute
                self.get_base_attributes_values_from_rule(simple_rule, attributes, attribute)

                # format attributes
                self.get_format_attributes_values_from_rule(attribute_format, types, attributes, attribute, simple_rule)

            attributes_for_each_group[current_group_index] = attributes
            current_group_index += 1

        return self.get_create_attributes_from_group_attributes(attributes_for_each_group, group_operators, current_group_index)

    def get_base_attributes_values_from_rule(self, simple_rule, attributes, attribute):
        # attribute type
        attribute_type = DataTypes.get(typeId=attribute.main_attribute_type).friendly
        if attribute_type == 'Number':
            simple_rule.value_to_compare = int(simple_rule.value_to_compare)

        if simple_rule.operator == '<' and attribute_type == 'Number':
            attributes[attribute.friendly]['max'] = min(simple_rule.value_to_compare - 1, attributes[attribute.friendly].get('max', 10000))
        elif simple_rule.operator == '>' and attribute_type == 'Number':
            attributes[attribute.friendly]['min'] = max(simple_rule.value_to_compare + 1, attributes[attribute.friendly].get('min', -10000))
        elif simple_rule.operator == '<=' and attribute_type == 'Number':
            attributes[attribute.friendly]['max'] = min(simple_rule.value_to_compare, attributes[attribute.friendly].get('max', 10000))
        elif simple_rule.operator == '>=' and attribute_type == 'Number':
            attributes[attribute.friendly]['min'] = max(simple_rule.value_to_compare, attributes[attribute.friendly].get('min', -10000))
        elif simple_rule.operator == '!=':
            if attributes[attribute.friendly].get('to_exclude', None) is None:
                attributes[attribute.friendly]['to_exclude'] = [simple_rule.value_to_compare]
            else:
                attributes[attribute.friendly]['to_exclude'].append(simple_rule.value_to_compare)
        elif simple_rule.operator == '==':
            attributes[attribute.friendly]['value'] = simple_rule.value_to_compare

    def get_format_attributes_values_from_rule(self, attribute_format, types, attributes, attribute, simple_rule):
        format_attributes = self.get_attributes_from_format(attribute_format)
        for format_attribute in format_attributes:
            attribute_type = format_attribute.split('.')[-1].lower()
            if attribute_type not in types or not types[attribute_type]:
                continue

            if attributes[attribute.friendly]['subAttributes'].get(attribute_type, None) is None:
                attributes[attribute.friendly]['subAttributes'][attribute_type] = {}
            if simple_rule.operator == '<':
                attributes[attribute.friendly]['subAttributes'][attribute_type]['max'] = min(types[attribute_type] - 1, attributes[attribute.friendly]['subAttributes'][attribute_type].get('max', 10000))
            elif simple_rule.operator == '>':
                attributes[attribute.friendly]['subAttributes'][attribute_type]['min'] = max(types[attribute_type] + 1, attributes[attribute.friendly]['subAttributes'][attribute_type].get('min', -10000))
            elif simple_rule.operator == '<=':
                attributes[attribute.friendly]['subAttributes'][attribute_type]['max'] = min(types[attribute_type], attributes[attribute.friendly]['subAttributes'][attribute_type].get('max', 10000))
            elif simple_rule.operator == '>=':
                attributes[attribute.friendly]['subAttributes'][attribute_type]['min'] = max(types[attribute_type], attributes[attribute.friendly]['subAttributes'][attribute_type].get('min', -10000))
            elif simple_rule.operator == '!=':
                if attributes[attribute.friendly]['subAttributes'].get('to_exclude', None) is None:
                    attributes[attribute.friendly]['subAttributes'][attribute_type]['to_exclude'] = [types[attribute_type]]
                else:
                    attributes[attribute.friendly]['subAttributes']['hour']['to_exclude'].append(types[attribute_type])
            elif simple_rule.operator == '==':
                attributes[attribute.friendly]['subAttributes'][attribute_type]['value'] = types[attribute_type]

    def calculate_attributes_based_on_complex_rules(self, rule_id):
        current_group_index = 1
        attributes_for_each_group = {}
        group_operators = {}
        while True:
            rules = ComplexRules.get_all(id=rule_id, group_index=current_group_index)
            if not rules or len(rules) == 0:
                break

            inner_group_operator = rules[0].inner_group_operator
            if not inner_group_operator or inner_group_operator.upper() == 'NONE':
                inner_group_operator = 'AND'
            # if the group operator is 'AND', all the rules must be satisfied
            # if the group operator is 'OR', at least one rule must be satisfied, so we choose a random one
            if inner_group_operator.upper() == 'OR':
                rules = [random.choice(rules)]
            group_operators[current_group_index] = rules[0].group_operator

            attributes_for_each_group_temp = {}
            group_operators_temp = {}
            ct = 1
            for simple_rule in rules:
                attributes_from_simple_rule = self.calculate_attributes_based_on_simple_rules(simple_rule.condition_rule_id)
                attributes_for_each_group_temp[ct] = attributes_from_simple_rule
                group_operators_temp[ct] = inner_group_operator
                ct += 1

            attributes_of_group = self.get_create_attributes_from_group_attributes(
                attributes_for_each_group_temp, group_operators_temp, ct)
            attributes_for_each_group[current_group_index] = attributes_of_group
            current_group_index += 1

        return self.get_create_attributes_from_group_attributes(attributes_for_each_group, group_operators, current_group_index)

    @staticmethod
    def get_create_attributes_from_group_attributes(attributes_for_each_group, group_operators, max_group_index):
        final_attributes = {}
        if len(attributes_for_each_group) == 0:
            return final_attributes
        final_attributes = attributes_for_each_group[1]
        if len(attributes_for_each_group) == 1:
            return final_attributes
        for group_index in range(2, max_group_index):
            attributes_group = attributes_for_each_group[group_index]
            if group_operators[group_index] == 'OR':
                to_choose_from = [attributes_group, final_attributes]
                final_attributes = to_choose_from[random.choice([0, 1])]
            else:
                # intersect the attributes
                for attribute_name, properties in attributes_group.items():
                    if attribute_name not in final_attributes.keys():
                        final_attributes[attribute_name] = properties
                        continue

                    final_attributes[attribute_name]['min'] = max(final_attributes[attribute_name].get('min', 0), properties.get('min', 0))
                    final_attributes[attribute_name]['max'] = min(final_attributes[attribute_name].get('max', 10000), properties.get('max', 10000))
                    for sub_attribute in properties['subAttributes']:
                        final_attributes[attribute_name]['subAttributes'][sub_attribute]['min'] = max(
                            final_attributes[attribute_name]['subAttributes'][sub_attribute].get('min', 0),
                            properties['subAttributes'][sub_attribute].get('min', 0))
                        final_attributes[attribute_name]['subAttributes'][sub_attribute]['max'] = min(
                            final_attributes[attribute_name]['subAttributes'][sub_attribute].get('max', 10000),
                            properties['subAttributes'][sub_attribute].get('max', 10000))

    def get_random_date(self, properties):
        """ Given some date properties, generates a random datetime.

            Parameters
            ----------
            properties: Dict
                dictionary containing min, max, excluded values for the date attributes
                (ex.: {year: {'min': 2001, 'max': 2007, 'to_exclude' = [2003, 2004]}, 'day': {'min': 1, max: '19'}})

            Returns
            -------
            datetime
                randomly generated datetime
        """
        try:
            start = datetime.now()
            start_values = {}
            for key in properties:
                start_values[key] = properties[key]['min']
            start = start.replace(**start_values)

            end = datetime.now()
            end_values = start_values
            for key in properties:
                end_values[key] = properties[key]['max']
            end = end.replace(**end_values)

            exact_values = {}
            for key in properties:
                if properties[key]['value'] != 0:
                    exact_values[key] = properties[key]['value']
            start = start.replace(**exact_values)
            end = end.replace(**exact_values)

            retries = 0
            max_retries = 20
            while True:
                if retries == max_retries:
                    return None
                valid_date = True
                generated_date = self.dataGenerators.make_date_between_two_dates(start, end)
                for key in properties:
                    if 'to_exclude' in properties[key]:
                        for to_exclude_value in properties[key]['to_exclude']:
                            if getattr(generated_date, key) == to_exclude_value:
                                valid_date = False
                                break
                if valid_date:
                    return generated_date
                retries += 1
        except (Exception,):
            return None

    @staticmethod
    def month_to_num(month):
        match month.lower():
            case 'january' | 'jan' | 'ianuarie' | 'ian':
                return 1
            case 'february' | 'feb' | 'februarie':
                return 2
            case 'march' | 'martie':
                return 3
            case 'april' | 'apr' | 'aprilie':
                return 4
            case 'may' | 'mai':
                return 5
            case 'june' | 'iunie':
                return 6
            case 'july' | 'iulie':
                return 7
            case 'august' | 'aug':
                return 8
            case 'september' | 'sept' | 'septembrie':
                return 9
            case 'october' | 'oct' | 'octombrie':
                return 10
            case 'november' | 'nov' | 'noiembrie' | 'noi':
                return 11
            case 'december' | 'dec' | 'decembrie':
                return 12

    @staticmethod
    def get_attributes_from_format(attribute_format):
        """ Given a string format of an attribute, extracts the element of the format.

            Parameters
            ----------
            attribute_format: String
                format of an attribute (ex.: '{year}:{month}-{day}')

            Returns
            -------
            list
                a list of elements from format (ex.: ['year', 'month', 'day'])
        """
        format_attributes = []
        last_bracket = None
        attribute = ''
        for index, c in enumerate(attribute_format):
            if c not in ['{', '}']:
                attribute = attribute + c
            elif c == '{':
                last_bracket = c
                attribute = ''
            elif c == '}' and last_bracket == '{':
                format_attributes.append(attribute)
        return format_attributes

    @staticmethod
    def get_separators_from_format(attribute_format):
        """ Given a string format of a datetime, extracts the elements separators.

            Parameters
            ----------
            attribute_format: String
                datetime format (ex.: '{year}:{month}-{day}')

            Returns
            -------
            list
                a list of separators, in original order (ex.: [':', '-'])
        """
        separators = []
        last_bracket = None
        separator = ''
        for index, c in enumerate(attribute_format):
            if c not in ['{', '}'] and (last_bracket == '}' or last_bracket is None):
                separator = separator + c
            elif c == '{':
                last_bracket = c
                separators.append(separator)
                separator = ''
            elif c == '}' and last_bracket == '{':
                last_bracket = c
        separators.append(separator)
        return separators

    def get_attributes_from_value_with_format(self, value, attribute_format):
        """ Given a string datetime value and string format, extracts the values for year, month, etc. from the string.

            Parameters
            ----------
            value: String
                string datetime value (ex.: '2000-06-30')
            attribute_format: String
                datetime format (ex.: '{year}-{month}-{day}')

            Returns
            -------
            dict
                a dictionary with values for each element of the datetime
        """
        attributes = self.get_attributes_from_format(attribute_format)
        separators = self.get_separators_from_format(attribute_format)
        unique_separator = 'd0n0tm4tch'
        for separator in separators:
            if separator != '':
                value = value.replace(separator, unique_separator)
        value_attributes = value.split(unique_separator)

        values = {}
        for index in range(min(len(value_attributes), len(attributes))):
            attribute_type = attributes[index].split('.')[-1].lower()
            value = value_attributes[index]
            try:
                value = int(value)
            except (Exception,):
                pass
            values[attribute_type] = value
        return values

    def reverse_rule(self, rule_id):
        simple_rules = SimpleRules.get_all(id=rule_id)
        if simple_rules is not None:
            for simple_rule in simple_rules:
                reversed_operator = self.reverse_rule_operator(simple_rule.operator)
                reversed_group_operator = self.reverse_group_operator(simple_rule.group_operator)
                SimpleRules.update(id=rule_id, group_index=simple_rule.group_index, attribute_id=simple_rule.attribute_id,
                                   operator=simple_rule.operator, value_to_compare=simple_rule.value_to_compare, group_operator=simple_rule.group_operator,
                                   update_column=['operator', 'group_operator'],
                                   update_value=[reversed_operator, reversed_group_operator])

        complex_rules = ComplexRules.get_all(id=rule_id)
        if complex_rules is not None:
            for complex_rule in complex_rules:
                self.reverse_rule(complex_rule.condition_rule_id)
                reversed_group_operator = self.reverse_rule_operator(complex_rule.group_operator)
                ComplexRules.update(id=rule_id, group_index=complex_rule.group_index,
                                    update_column='group_operator',
                                    update_value=reversed_group_operator)

    @staticmethod
    def reverse_rule_operator(operator):
        match operator:
            case '>':
                return '<='
            case '<':
                return '>='
            case '==':
                return '!='
            case '>=':
                return '<'
            case '<=':
                return '>'
            case '!=':
                return '=='
            case 'MIN':
                return 'MAX'
            case 'MAX':
                return 'MIN'
            case default:
                return '!='

    @staticmethod
    def reverse_group_operator(operator):
        match operator:
            case 'AND':
                return 'OR'
            case 'OR':
                return 'AND'
            case default:
                return 'AND'
