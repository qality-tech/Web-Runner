from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class ResponseAttribute(Base):

    responseObjectAttributeId: int
    attributeId: int
    referenceObjectId: str
    referenceAttribute: str
    parent_object_id: int
    required: bool
    ai: bool
    ag: bool
    au: bool
    responseObjectId: float
    attributeValue: str
    node_instance_index_res: int
    attribute_instance_index: int
    depth: int
    provider: bool
    class_index: int
    object_index: int
    unique_id: int
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
    projectId: int
    absoluteUrl: str
    relativeUrl: str
    bodyObjectId: float
    bodyIsList: bool
    responseAsList: bool
    friendlyUrl: str
    node_instance_index_node: int
    class_index_node: int
    object_index_node: int
    unique_id_node: int
    friendly: str
    dataValidation: str
    fakerApiConfig: str
    rawName: str
    main_attribute_id: float
    list_items: str
    controllerId: int
    endpointId: int
    response_id: int
    status_code_id: int
    parent_id: int
    main_attribute_type: int

    def __init__(self, data):
        super(ResponseAttribute, self).__init__(data)
