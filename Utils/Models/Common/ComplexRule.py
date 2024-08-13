from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class ComplexRule(Base):

    id: int = field(metadata={'column': 'rule_id'})
    friendly: str
    group_index: int
    operator: str
    condition_rule_id: str
    attribute_id: int
    group_operator: str
    inner_group_operator: str = field(metadata={'column': 'group_conditions_operator'})

    def __init__(self, data):
        super(ComplexRule, self).__init__(data)
