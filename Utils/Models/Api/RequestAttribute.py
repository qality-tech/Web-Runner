from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class RequestAttribute(Base):

    bodyObjectAttributeId: int
    attributeId: int = field(metadata={'column': 'id'})
    referenceObjectId: str
    referenceAttribute: str
    parent_object_id: int
    dataValidation_req: str
    attributeValue: str
    required: bool
    bodyObjectId: int
    node_instance_index_req: float
    attribute_instance_index: int
    provider: bool
    depth: int
    class_index_req: float
    object_index_req: float
    unique_id_req: float
    node_id: int
    friendly_node: str
    codeOwner: str
    crud: str
    verb: str
    encodedRequestType: str
    requireAuthorization: bool
    actors: str
    timeout: str
    technologyApiId: int
    absoluteUrl: str
    relativeUrl: str
    bodyIsList: bool
    responseObjectId: float
    responseAsList: bool
    friendlyUrl: str
    node_instance_index_node: int
    class_index_node: int
    object_index_node: int
    unique_id_node: int
    friendly: str
    dataValidation_attr: str
    fakerApiConfig: str
    rawName: str
    list_items: str
    original_object_id: float
    excluded: int
    node_instance_index_res: str
    class_index: str
    object_index: str
    unique_id: str
    projectId: str
    dataValidation: str
    controllerId: int
    endpointId: int
    status_code_id: int
    parent_id: int
    request_id: int
    main_attribute_id: float
    main_attribute_type: int
    inherited: bool
    attributeType: float
    meta: str = field(metadata={'column': 'metadata'})
    ruleId: int

    def __init__(self, data):
        super(RequestAttribute, self).__init__(data)
