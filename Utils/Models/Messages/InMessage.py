from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class InMessage(Base):

    id: float
    friendly: str
    cfgDoId: float
    technologyMsgId: float
    dataSet: str
    projectId: int
    url: str
    dataObjectConfigObjectId: float = field(metadata={'column': 'dataObjectConfig.objectId'})
    dataObjectConfigAttributes: str = field(metadata={'column': 'dataObjectConfig.attributes'})
    dataObjectConfigObjectName: str = field(metadata={'column': 'dataObjectConfig.objectName'})
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(InMessage, self).__init__(data)