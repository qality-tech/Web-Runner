from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Hook(Base):

    hookId: int
    friendly: str
    hookType: str
    endpoints_ids: str
    messages: str
    componentId: int
    class_index: int
    object_index: int
    unique_id: int

    def __init__(self, data):
        super(Hook, self).__init__(data)