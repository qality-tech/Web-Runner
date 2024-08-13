from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class OutMessage(Base):

    id: float
    friendly: str
    cfgDoId: float
    technologyMsgId: float
    inMessage: float
    dataSet: str
    projectId: int
    url: str
    class_index: int
    object_index: int
    unique_id: int
    inMessageId: float = field(metadata={'column': 'inMessage.id'})
    inMessageFriendly: str = field(metadata={'column': 'inMessage.friendly'})
    inMessageDataObjectConfigObjectId: float = field(metadata={'column': 'inMessage.dataObjectConfig.objectId'})
    inMessageDataObjectConfigAttributes: str = field(metadata={'column': 'inMessage.dataObjectConfig.attributes'})
    inMessageDataObjectConfigObjectName: str = field(metadata={'column': 'inMessage.dataObjectConfig.objectName'})
    inMessageCfgDoId: float = field(metadata={'column': 'inMessage.cfgDoId'})
    inMessageTechnologyMsgId: float = field(metadata={'column': 'inMessage.technologyMsgId'})
    inMessageDataSet: float = field(metadata={'column': 'inMessage.dataSet'})

    def __init__(self, data):
        super(OutMessage, self).__init__(data)