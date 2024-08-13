from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class NamingAttribute(Base):

    techNames: list[dict]
    attributeId: int
    originalName: str
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(NamingAttribute, self).__init__(data)