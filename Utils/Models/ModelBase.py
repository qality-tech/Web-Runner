from dataclasses import dataclass, field, fields
import numpy as np


@dataclass(init=False)
class Base(object):
    def __init__(self, data):
        if data is None:
            return

        fields_dict = {}
        for cls_field in fields(self):
            try:
                fields_dict[cls_field.metadata['column']] = {'name': cls_field.name, 'type': cls_field.type}
            except (Exception,):
                fields_dict[cls_field.name] = {'name': cls_field.name, 'type': cls_field.type}

        for key, value in data.items():
            if key in fields_dict.keys():
                if type(value) == float and np.isnan(value):
                    setattr(self, fields_dict[key]['name'], None)
                else:
                    setattr(self, fields_dict[key]['name'], value)

    @classmethod
    def get_fields_dict(cls):
        fields_dict = {}
        for cls_field in fields(cls):
            try:
                fields_dict[cls_field.name] = cls_field.metadata['column']
            except (Exception,):
                fields_dict[cls_field.name] = cls_field.name
        return fields_dict
