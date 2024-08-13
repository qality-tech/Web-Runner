from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class InMessagesAttribute(Base):

    attributeId: int
    attributeName: str
    attributeValue: str
    fakerApiConfig: str
    attributeDataType: int
    attributeDataTypeConfig: str
    node_instance_index: int
    attribute_instance_index: int
    parent_instance_index: int
    required: bool
    responseObjectAttributeId: str
    responseObjectId: str
    node_id: int
    url: str
    class_index: int
    object_index: int
    unique_id: int
    attributeType: int
    friendly: str
    dataValidation: str
    referenceAttribute: str
    referenceObjectId: str
    parent_object_id: int
    projectId: int
    main_attribute_id: float
    depth: int
    list_items: str
    unique_id_node: int

    def __init__(self, data):
        super(InMessagesAttribute, self).__init__(data)