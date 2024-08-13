from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class UrlAttribute(Base):

    orderIndex: int
    attributeId: int
    pageId: int
    paramType: str
    isOptional: str
    paramQueryKey: str
    class_index: int
    object_index: int
    unique_id: int
    type: str
    queryParamKey: str
    main_attribute_type: int
    attributeType: int
    meta: str = field(metadata={'column': 'metadata'})
    ruleId: int

    def __init__(self, data):
        super(UrlAttribute, self).__init__(data)