from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class SimpleRule(Base):

    id: int = field(metadata={'column': 'rule_id'})
    friendly: str
    group_index: int
    operator: str
    value_to_compare: str
    attribute_id: int
    original_object_id: int
    reference_attribute: int = field(metadata={'column': 'referenceAttribute'})
    attribute_type: int = field(metadata={'column': 'attributeType'})
    group_operator: str
    inner_group_operator: str = field(metadata={'column': 'group_conditions_operator'})

    def __init__(self, data):
        super(SimpleRule, self).__init__(data)
