from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class DataObject(Base):

    id: int = field(metadata={'column': 'objectId'})
    friendly: str
    isEnum: bool
    dataAttributes: str
    projectId: int
    rawName: str

    def __init__(self, data):
        super(DataObject, self).__init__(data)
