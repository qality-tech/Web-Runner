from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class InputAttribute(Base):

    id: int = field(metadata={'column': 'id'})
    friendly: str
    selector_id: float = field(metadata={'column': 'selector.selectorId'})
    elementType: str
    attributeId: float = field(metadata={'column': 'dataAttributeId'})
    componentId: int
    existenceCondition: str = field(metadata={'column': 'existenceCondition.id'})
    validDataCondition: str = field(metadata={'column': 'validDataCondition.id'})
    disabled: str = field(metadata={'column': 'elementDisabled'})
    required: bool = field(metadata={'column': 'elementRequired'})
    prepopulated: str = field(metadata={'column': 'elementPrePopulated'})
    c: int
    r: int
    u: int
    d: int
    attributeValue: str
    elementGroup: str
    class_index: int
    object_index: int
    unique_id: float
    node_instance_index: int
    attribute_instance_index: int
    original_object_id: float
    referenceAttribute: float
    attribute_type: float
    subType: str
    elementEvents: list
    desiredAttributes: list
    main_attribute_type: int
    dropdown_option_element: float = field(metadata={'column': 'elementTypeConfig.dropdownSubtypeElementId'}, default=None)
    generated: bool = False
    elementOptionsMeta: str = field(metadata={'column': 'elementOptions.meta'}, default=None)
    actor: int = None
    level: int = None

    def __init__(self, data):
        super(InputAttribute, self).__init__(data)
