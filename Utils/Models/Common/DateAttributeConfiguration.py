from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class DateAttributeConfiguration(Base):

    dateFormat: str
    attributeId: int
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(DateAttributeConfiguration, self).__init__(data)