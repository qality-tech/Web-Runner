from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Attribute(Base):
    id: int = field(metadata={'column': 'attributeId'})
    friendly: str
    dataValidation: str
    fakerApiConfig: str
    referenceAttribute: str
    referenceObjectId: str
    parent_object_id: int
    projectId: int
    main_attribute_id: float
    depth: int
    list_items: str
    class_index: int
    object_index: int
    unique_id: int
    rule: int
    main_attribute_id: int
    main_attribute_type: int

    def __init__(self, data):
        super(Attribute, self).__init__(data)
