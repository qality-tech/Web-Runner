from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class DataType(Base):

    id: int = field(metadata={'column': 'typeId'})
    friendly: str
    dataId: int
    class_index: int
    object_index: int
    unique_id: int
    typeId: int
    method: any

    def __init__(self, data):
        super(DataType, self).__init__(data)
