import base64
import json
import sys
import threading

import pandas as pd
import requests

from Utils.Common.Fake import Fake
from Utils.Models.Repository import *
from Utils.Common.DataGenerators import DataGenerators


class Helpers:
    primary_data_types = None
    object_data_types = None
    list_data_type = None
    enum_data_type = None
    data = None
    info = None

    class Attribute:
        def __init__(self, attribute, value):
            self.attribute = attribute
            self.value = value

    def __init__(self, test_path):
        with open(test_path) as f:
            content: dict = json.load(f)
            self.data = json.loads(content['payload'])
            for position in range(0, len(self.data['path'])):
                content['testSteps'][position]['subType'] = (self.data['path'][position].get('subType') or None)
                content['testSteps'][position]['tech'] = (self.data['path'][position].get('tech') or 'API')
            del content['payload']
            self.info = content

        # converts the dataframes that are received in payload to json and are saved as attributes of this class
        for dataframe in self.data['data']:
            json_dataframe = pd.json_normalize(json.loads(self.data['data'].get(dataframe) or '[]'))
            model_name = ''.join([word[0].upper() + word[1:] for word in dataframe.split('_')])
            try:
                getattr(sys.modules[__name__], model_name).set_dataframe(json_dataframe)
            except (Exception,):
                print(f'Model not implemented for {model_name}')

        # extracts primary, object and list data types from dataTypes dataframe
        self.primary_data_types = [dt.typeId for dt in DataTypes.get_all(friendly=['Number', 'String', 'Date', 'Boolean'])]
        self.object_data_types = [dt.typeId for dt in DataTypes.get_all(friendly='Object')]
        self.list_data_type = [dt.typeId for dt in DataTypes.get_all(friendly='List')]
        self.enum_data_type = DataTypes.get(friendly='Enum').typeId
        self.set_data_type = DataTypes.get(friendly='Set').typeId

    def generate_input_value(self, element: InputAttribute, rules_handler, node_instance_index=1, is_wrong_data_type=False, actor=None):
        conditions = self.get_conditions_from_element(element)
        if element.attributeId:
            try:
                element_temp = SuiteAttributes.get(attributeId=element.attributeId,
                                              node_instance_index=node_instance_index,
                                              actor=actor)
                if element_temp is None:
                    raise Exception
                element = element_temp
            except (Exception,):
                element = SuiteAttributes.get(attributeId=element.attributeId, node_instance_index=node_instance_index)
        if hasattr(element, 'attributeValue') and element.attributeValue and not is_wrong_data_type:
            return element.attributeValue

        if element.main_attribute_type is not None:
            properties = rules_handler.calculate_attributes_based_on_rules(conditions)
            properties = properties[element.friendly] if properties is not None and element.friendly in properties else None
            return DataTypes.get(typeId=element.main_attribute_type).method(element=element, properties=properties)

        return DataTypes.get(typeId=15670).method(element=element)

    @staticmethod
    def get_conditions_from_element(element: InputAttribute):
        conditions = set()
        conditions.add(element.validDataCondition)

        attribute = Attributes.get(id=element.attributeId)
        if attribute is not None:
            conditions.add(attribute.rule)
        return [_ for _ in conditions if not pd.isnull(_)]

    def update_naming_attributes(self, tech_id):
        NamingAttributes.df.apply(
            lambda naming_attribute: self.get_new_name_based_on_tech_id(NamingAttributes.to_model(naming_attribute), tech_id),
            axis=1
        )

    @staticmethod
    def get_new_name_based_on_tech_id(naming_attribute: NamingAttribute, tech_id):
        tech_names = naming_attribute.techNames
        new_name = [attribute for attribute in tech_names if attribute['technologyId'] == tech_id]
        if len(new_name) == 0:
            return
        new_name = new_name[0]
        if 'attributeTechName' in new_name and new_name['attributeTechName'] != naming_attribute.originalName:
            SuiteAttributes.update(attributeId=naming_attribute.attributeId, update_column='friendly', update_value=new_name['attributeTechName'])
            RequestAttributes.update(attributeId=naming_attribute.attributeId, update_column='friendly', update_value=new_name['attributeTechName'])
            ResponseAttributes.update(attributeId=naming_attribute.attributeId, update_column='friendly', update_value=new_name['attributeTechName'])

    @staticmethod
    def request_task(url, data, headers):
        to_print = []
        try:
            requests.post(url, json=data, headers=headers)
        except Exception as e:
            to_print.append('\n')
            to_print.append('Communication with the Runner failed with:')
            to_print.append(str(e))
            to_print.append('payload')
            to_print.append(str(data))
            to_print.append('header')
            to_print.append(str(headers))
        finally:
            print('\n'.join(to_print))

    def fire_and_forget(self, url, value, headers):
        threading.Thread(target=self.request_task, args=(url, value, headers)).start()

    @staticmethod
    def df_to_model(df, df_name):
        name_types = []
        df_name = df_name.replace('df_', '')
        df_name = df_name[0].upper() + df_name[1:]
        df_name = df_name[:-1] if df_name[-1] == 's' else df_name
        for name, dtype in df.dtypes.to_dict().items():
            dtype = str(dtype).replace('int64', 'int').replace('object', 'str').replace('float64', 'float')
            name_types.append(f'{name}: {dtype}')
        final_class = f'@dataclass(init=False) \nclass {df_name}(Base): \n'
        final_class = final_class + '\n\t' + '\n\t'.join(name_types)
        final_class = final_class + f'\n\n\tdef __init__(self, data): \n\t\tsuper({df_name}, self).__init__(data)'

        file = open('models.txt', 'a')
        file.write(final_class + '\n\n')
        file.close()

    def get_attribute_or_main_attribute(self, attribute_id, attribute_instance_index=None, node_instance_index=None, in_use=None, actor=None):
        attribute = self.get_attribute(attribute_id, attribute_instance_index, node_instance_index, in_use, actor)
        if attribute.attribute is not None and attribute.value is None:
            main_attribute_id = attribute.attribute['main_attribute_id']
            if not pd.isnull(main_attribute_id):
                attribute = self.get_attribute(main_attribute_id, attribute_instance_index, node_instance_index, in_use, actor)
        return attribute

    def get_attribute(self, attribute_id, attribute_instance_index=None, node_instance_index=None, in_use=None, actor=None):
        dataframe = SuiteAttributes.df[SuiteAttributes.df['attributeId'] == attribute_id]
        same_attribute_index = (dataframe['attribute_instance_index'] == attribute_instance_index) if attribute_instance_index is not None else pd.Series(True, index=dataframe.index)
        same_node_index = (dataframe['node_instance_index'] == node_instance_index) if node_instance_index is not None else pd.Series(True, index=dataframe.index)
        attribute_in_use = (dataframe['inUse'] == in_use) if ('inUse' in dataframe and in_use is not None) else pd.Series(True, index=dataframe.index)
        same_actor = (dataframe['actor'] == actor)

        dataframe_tmp = dataframe[(same_attribute_index & same_node_index & attribute_in_use & same_actor)]
        if dataframe_tmp.empty:
            dataframe = dataframe[(same_attribute_index & same_node_index & attribute_in_use)]
        else:
            dataframe = dataframe_tmp

        if dataframe.empty:
            return self.Attribute(None, None)
        for index, row in dataframe.iterrows():
            if row['attributeValue']:
                value = row['attributeValue'].value if type(row['attributeValue']) is Fake else row['attributeValue']
                return self.Attribute(row, value)
        return self.Attribute(dataframe.iloc[0], None)

    @staticmethod
    def generate_value(attribute_type):
        return Fake(DataTypes.get(typeId=attribute_type).method())

    # Generates values for every data type
    def get_dataType_method(self, dataType_row):
        data_generators = DataGenerators()
        if dataType_row["friendly"] == "String":
            return data_generators.make_string
        elif dataType_row["friendly"] == "Number":
            return data_generators.make_number
        elif dataType_row["friendly"] == "Boolean":
            return data_generators.make_bool
        elif dataType_row["friendly"] == "Date":
            return data_generators.make_date
        elif dataType_row["friendly"] == "List":
            return
        elif dataType_row["friendly"] == "Object":
            return data_generators.make_object
        elif dataType_row["friendly"] == "Enum":
            return None
        elif dataType_row["friendly"] == "Unknown":
            return None
        elif dataType_row["friendly"] == "Email":
            return data_generators.make_email
        elif dataType_row["friendly"] == 'Phone':
            return data_generators.make_phone
        else:
            return None

    def populate_data_type_method(self):
        # Populate dataTypes with methods generated
        DataTypes.df['method'] = DataTypes.df.apply(self.get_dataType_method, axis=1)

    @staticmethod
    def cast_attribute_value_to_object():
        if HeaderAttributes.df is not None and not HeaderAttributes.df.empty:
            HeaderAttributes.df['attributeValue'] = HeaderAttributes.df['attributeValue'].astype(object)
        if RequestAttributes.df is not None and not RequestAttributes.df.empty:
            RequestAttributes.df['attributeValue'] = RequestAttributes.df['attributeValue'].astype(object)
        if SuiteAttributes.df is not None and not SuiteAttributes.df.empty:
            SuiteAttributes.df['attributeValue'] = SuiteAttributes.df['attributeValue'].astype(object)

    def valorize_endpoint_url(self, endpoint: Endpoint, node_instance_index=1, attribute_instance_index=1, actor=None, attributes_to_ignore=None) -> list:
        """ Replaces url attributes in the url of an endpoint. \n

            Parameters
            ----------
            endpoint: Series
                request data, row of the requests dataframe
            node_instance_index: Number, optional
                the node instance of the test step, default is 1
            attribute_instance_index: Number, optional
                the url attribute index, if there are multiple values, default is 1

            Returns
            -------
            list
                all possible urls as list
        """
        if attributes_to_ignore is None:
            attributes_to_ignore = []

        try:
            relative_url = endpoint.relativeUrl if endpoint.relativeUrl else ''
            url = (endpoint.friendlyUrl + relative_url).strip()
            all_possible_urls = [url]
            order_index = 1
            while True:
                url_attribute = ApiUrlAttributes.get(endpoint_id=endpoint.endpoint_id, orderIndex=order_index)
                if url_attribute is None:
                    break

                if url_attribute.attributeId in attributes_to_ignore:
                    order_index += 1
                    continue

                attribute_value = self.get_attribute_or_main_attribute(
                    url_attribute.attributeId, attribute_instance_index, node_instance_index, actor=actor).value
                new_urls_1 = []
                new_urls_2 = []
                if attribute_value is not None:
                    value_to_replace = ''
                    if url_attribute.param_type == 'PARAM':
                        value_to_replace = str(attribute_value)
                    elif url_attribute.param_type == 'QUERY_PARAM':
                        value_to_replace = f'{url_attribute.query_param_key}={attribute_value}'
                    new_urls_1 = [url.replace('{' + str(order_index) + '}', str(value_to_replace)) for url in all_possible_urls]
                if url_attribute.isOptional:
                    for url in all_possible_urls:
                        attribute_end_position = url.find('{' + str(order_index) + '}') + len(
                            '{' + str(order_index) + '}')
                        last_delimiter_position = max(
                            url[:attribute_end_position].rfind('&'),
                            url[:attribute_end_position].rfind('/'),
                            url[:attribute_end_position].rfind('?')
                        )
                        new_url = url[:last_delimiter_position + 1] + url[attribute_end_position:]
                        new_url = new_url.replace('/&', '/').replace('?&', '?')
                        new_urls_2.append(new_url)
                if attribute_value is None and not url_attribute.isOptional:
                    raise Exception("Url attribute is not defined and is not optional")
                all_possible_urls = new_urls_1 + new_urls_2
                order_index += 1

            for index, url in enumerate(all_possible_urls):
                if len(url) > 0 and url[-1] in ['&', '?']:
                    all_possible_urls[index] = url[:-1]

            return all_possible_urls
        except Exception as e:
            message = f'Could not valorize url for request {endpoint.endpoint_friendly}.'
            raise Exception(message)
