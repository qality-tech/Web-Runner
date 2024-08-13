from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class ElementsGroup(Base):

    id: int = field(metadata={'column': 'elementGroupId'})
    friendly: str
    actors: str
    interactWithSelector: str
    isMultiple: bool
    elements: str
    elements_ids: list
    existenceCondition: str
    validDataCondition: str
    componentId: int
    rules: str
    generated: str
    class_index: int
    object_index: int
    unique_id: float
    technologyWebId: float
    desiredAttributes: list
    generated: bool = False
    actor: int = None
    level: int = None

    def __init__(self, data):
        super(ElementsGroup, self).__init__(data)