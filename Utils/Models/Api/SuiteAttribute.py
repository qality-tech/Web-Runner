from dataclasses import dataclass, field

from Utils.Common.Fake import Fake
from Utils.Models.ModelBase import Base


@dataclass(init=False)
class SuiteAttribute(Base):

    friendly: str
    attributeValue: str | Fake
    node_instance_index: float
    attribute_instance_index: float
    attributeId: float
    projectId: float
    fakerApiConfig: str
    parent_object_id: float
    responseObjectId: float
    responseObjectAttributeId: float
    depth: float
    referenceAttribute: str
    referenceObjectId: str
    required: str
    unique_id: int
    parent_instance_index: int
    original_object_id: str
    actor: float
    main_attribute_type: int
    main_attribute_id: int

    def __init__(self, data):
        super(SuiteAttribute, self).__init__(data)