from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Page(Base):
    id: str = field(metadata={'column': 'pageId'})
    friendly: str
    relativeUrl: str
    technologyWebId: int
    projectId: int
    absoluteUrl: str
    requireAuthorization: bool
    desiredAttributes: list
    subType: str = None
    projectUrl: str = None
    actor: int = None
    level: int = None

    def __init__(self, data):
        super(Page, self).__init__(data)
