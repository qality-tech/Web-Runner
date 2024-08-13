from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class SelectorsAttribute(Base):

    attributeId: int
    orderIndex: int
    meta: str
    isOptional: str
    ruleId: float
    selectorId: int
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(SelectorsAttribute, self).__init__(data)