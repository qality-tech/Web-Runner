from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class OutputAttribute(Base):

    attributeId: float
    componentId: float
    friendly: str
    class_index: str
    object_index: str
    unique_id: int
    attributeValue: str
    c: float
    r: float
    u: float
    d: float
    api_node: float
    trigger_element_id: float
    node_instance_index: int
    attribute_instance_index: int
    original_object_id: int
    referenceAttribute: int
    attribute_type: int

    def __init__(self, data):
        super(OutputAttribute, self).__init__(data)