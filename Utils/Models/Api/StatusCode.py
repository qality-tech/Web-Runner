from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class StatusCode(Base):

    id: int = field(metadata={'column': 'scId'})
    statusCode: int
    friendly: str
    globalStatusCodeId: int
    technologyApiId: int
    dataObjectId: int
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(StatusCode, self).__init__(data)