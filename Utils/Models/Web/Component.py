from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Component(Base):

    id: int = field(metadata={'column': 'componentId'})
    associatedElementId: float
    friendly: str
    interactWithSelector: bool
    existenceCondition: str
    validDataCondition: str
    componentLocation: str
    # messages: str
    technologyWebId: int
    pageId: float
    projectId: int
    type: str
    componentSettings: str
    OnInit_Messages: str
    OnInit_Requests: str
    AfterViewInit_Messages: str
    AfterViewInit_Requests: str
    AfterContentInit_Messages: str
    AfterContentInit_Requests: str
    OnDestroy_Messages: str
    OnDestroy_Requests: str
    componentLocationLocation: str = field(metadata={'column': 'componentLocation.location'})
    componentLocationComponentId: str = field(metadata={'column': 'componentLocation.componentId'})
    componentLocationModalComponentId: str = field(metadata={'column': 'componentLocation.modalComponentId'})
    # componentLocationIframeTagElementId: str = field(metadata={'column': 'componentLocation.iframeTag.elementId'})
    # componentLocationIframeTagElementType: str = field(metadata={'column': 'componentLocation.iframeTag.elementType'})
    requireAuthorization: int
    reachable: bool
    elementGroupId: str
    elementGroupId_eg: str
    actors: str
    interactWithSelector_eg: str
    isMultiple: str
    rules: str
    generated: str
    subType: str
    paginationId: str = field(metadata={'column': 'componentFilteringAndPagination.componentPaginationId'})
    filterId: str = field(metadata={'column': 'componentFilteringAndPagination.componentFilterId'})
    desiredAttributes: list
    actor: int = None
    level: int = None

    def __init__(self, data):
        super(Component, self).__init__(data)
