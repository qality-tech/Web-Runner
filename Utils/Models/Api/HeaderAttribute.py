from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class HeaderAttribute(Base):

    friendly: str
    attributeId: int = field(metadata={'column': 'id'})
    attributeType: int
    attributeValue: str
    dataValidation: str
    headerObjectId: str
    referenceObjectId: str
    referenceAttribute: str
    requestId: int
    headerObjectAttributeId: int
    class_index: str
    object_index: str
    unique_id: str
    referenceAttributeId: str
    status_code_id: int
    main_attribute_type: int
    main_attribute_id: int
    inherited: bool
    meta: str = field(metadata={'column': 'metadata'})
    ruleId: int

    def __init__(self, data):
        super(HeaderAttribute, self).__init__(data)