from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class ApiUrlAttribute(Base):

    endpoint_id: int
    controller_id: int
    orderIndex: int
    attributeId: int
    attributeType: int
    main_attribute_id: int
    main_attribute_type: int
    isOptional: bool
    class_index: int
    object_index: int
    unique_id: int
    query_param_key: str = field(metadata={'column': 'paramQueryKey'})
    param_type: str = field(metadata={'column': 'paramType'})

    def __init__(self, data):
        super(ApiUrlAttribute, self).__init__(data)
