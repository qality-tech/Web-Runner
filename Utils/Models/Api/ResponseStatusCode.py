from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class ResponseStatusCode(Base):

    entityId: int
    comparisonValue: str
    conditionOperator: str
    requestId: int
    statusCodeId: int
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(ResponseStatusCode, self).__init__(data)