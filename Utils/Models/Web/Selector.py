from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Selector(Base):

    id: int = field(metadata={'column': 'selectorId'})
    friendly: str
    index: str
    selector: str
    technologyWebId: int
    selectorAttributes: str
    selectorRules: str

    def __init__(self, data):
        super(Selector, self).__init__(data)
