from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class Endpoint(Base):
    id: int = field(metadata={'column': 'status_code_id'})
    crud: str
    verb: str
    encodedRequestType: str
    requireAuthorization: bool
    actors: str
    timeout: str
    technologyApiId: int
    projectId: int
    relativeUrl: str
    responseAsList: bool
    friendlyUrl: str
    node_instance_index: int
    class_index: int
    object_index: int
    unique_id: int
    actor: int
    level: int
    controller_id: int
    controller_friendly: str
    projectUrl: str
    endpoint_friendly: str
    statusCode: int
    outcome: str
    endpoint_id: int
    status_code_friendly: str
    status_code_url: str
    response_id: int
    request_id: int
    rule: int
    actor: int
    level: int
    desiredAttributes: list

    def __init__(self, data):
        super(Endpoint, self).__init__(data)
