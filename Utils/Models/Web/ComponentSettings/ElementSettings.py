from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base
from enum import Enum


class ElementType(Enum):
    NONE = 'None'
    ELEMENT = "ELEMENT"
    ELEMENT_GROUP = "GROUP_ELEMENT"


@dataclass(init=False)
class ElementSettings(Base):

    id: int = field(metadata={'column': 'elementId'}, default=None)
    type: ElementType = field(metadata={'column': 'elementType'}, default=None)

    def __init__(self, data):
        super(ElementSettings, self).__init__(data)
