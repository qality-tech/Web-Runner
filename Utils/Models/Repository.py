from typing import List

from Utils.Models.Api.ApiUrlAttribute import ApiUrlAttribute
from Utils.Models.Api.Attribute import Attribute
from Utils.Models.Api.HeaderAttribute import HeaderAttribute
from Utils.Models.Api.Endpoint import Endpoint
from Utils.Models.Api.RequestAttribute import RequestAttribute
from Utils.Models.Api.RequestStatusCode import RequestStatusCode
from Utils.Models.Api.ResponseAttribute import ResponseAttribute
from Utils.Models.Api.ResponseStatusCode import ResponseStatusCode
from Utils.Models.Api.StatusCode import StatusCode
from Utils.Models.Api.SuiteAttribute import SuiteAttribute
from Utils.Models.Common.ComplexRule import ComplexRule
from Utils.Models.Common.DataType import DataType
from Utils.Models.Common.DateAttributeConfiguration import DateAttributeConfiguration
from Utils.Models.Common.NamingAttribute import NamingAttribute
from Utils.Models.Common.SimpleRule import SimpleRule
from Utils.Models.Common.StringAttributeConfiguration import StringAttributeConfiguration
from Utils.Models.Messages.InMessage import InMessage
from Utils.Models.Messages.InMessagesAttribute import InMessagesAttribute
from Utils.Models.Messages.OutMessage import OutMessage
from Utils.Models.Messages.OutMessagesAttribute import OutMessagesAttribute
from Utils.Models.RepositoryBase import Base
from Utils.Models.Web.Component import Component
from Utils.Models.Web.ElementsGroup import ElementsGroup
from Utils.Models.Web.Hook import Hook
from Utils.Models.Web.InputAttribute import InputAttribute
from Utils.Models.Web.OutputAttribute import OutputAttribute
from Utils.Models.Web.Page import Page
from Utils.Models.Web.Selector import Selector
from Utils.Models.Common.DataObject import DataObject
from Utils.Models.Web.SelectorsAttribute import SelectorsAttribute
from Utils.Models.Web.UrlAttribute import UrlAttribute


class Components(Base):
    model = Component

    @classmethod
    def get(cls, **kwargs) -> Component | None:
        return super(cls, Components).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Component] | None:
        return super(cls, Components).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Component] | None:
        return super(cls, Components).update(**kwargs)


class Selectors(Base):
    model = Selector

    @classmethod
    def get(cls, **kwargs) -> Selector | None:
        return super(cls, Selectors).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Selector] | None:
        return super(cls, Selectors).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Selector] | None:
        return super(cls, Selectors).update(**kwargs)


class Pages(Base):
    model = Page

    @classmethod
    def get(cls, **kwargs) -> Page | None:
        return super(cls, Pages).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Page] | None:
        return super(cls, Pages).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Page] | None:
        return super(cls, Pages).update(**kwargs)


# =========== Common ===========
class DataObjects(Base):
    model = DataObject

    @classmethod
    def get(cls, **kwargs) -> DataObject | None:
        return super(cls, DataObjects).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[DataObject] | None:
        return super(cls, DataObjects).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[DataObject] | None:
        return super(cls, DataObjects).update(**kwargs)


class DataTypes(Base):
    model = DataType

    @classmethod
    def get(cls, **kwargs) -> DataType | None:
        return super(cls, DataTypes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[DataType] | None:
        return super(cls, DataTypes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[DataType] | None:
        return super(cls, DataTypes).update(**kwargs)


class InputAttributes(Base):
    model = InputAttribute

    @classmethod
    def get(cls, **kwargs) -> InputAttribute | None:
        return super(cls, InputAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[InputAttribute] | None:
        return super(cls, InputAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[InputAttribute] | None:
        return super(cls, InputAttributes).update(**kwargs)


# =========== Api ===========
class Endpoints(Base):
    model = Endpoint

    @classmethod
    def get(cls, **kwargs) -> Endpoint | None:
        return super(cls, Endpoints).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Endpoint] | None:
        return super(cls, Endpoints).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Endpoint] | None:
        return super(cls, Endpoints).update(**kwargs)


class RequestAttributes(Base):
    model = RequestAttribute

    @classmethod
    def get(cls, **kwargs) -> RequestAttribute | None:
        return super(cls, RequestAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[RequestAttribute] | None:
        return super(cls, RequestAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[RequestAttribute] | None:
        return super(cls, RequestAttributes).update(**kwargs)


class ResponseAttributes(Base):
    model = ResponseAttribute

    @classmethod
    def get(cls, **kwargs) -> ResponseAttribute | None:
        return super(cls, ResponseAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[ResponseAttribute] | None:
        return super(cls, ResponseAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[ResponseAttribute] | None:
        return super(cls, ResponseAttributes).update(**kwargs)


class Attributes(Base):
    model = Attribute

    @classmethod
    def get(cls, **kwargs) -> Attribute | None:
        return super(cls, Attributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Attribute] | None:
        return super(cls, Attributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Attribute] | None:
        return super(cls, Attributes).update(**kwargs)


class SuiteAttributes(Base):
    model = SuiteAttribute

    @classmethod
    def get(cls, **kwargs) -> SuiteAttribute | None:
        return super(cls, SuiteAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[SuiteAttribute] | None:
        return super(cls, SuiteAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[SuiteAttribute] | None:
        return super(cls, SuiteAttributes).update(**kwargs)


class StatusCodes(Base):
    model = StatusCode

    @classmethod
    def get(cls, **kwargs) -> StatusCode | None:
        return super(cls, StatusCodes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[StatusCode] | None:
        return super(cls, StatusCodes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[StatusCode] | None:
        return super(cls, StatusCodes).update(**kwargs)


class ResponseStatusCodes(Base):
    model = ResponseStatusCode

    @classmethod
    def get(cls, **kwargs) -> ResponseStatusCode | None:
        return super(cls, ResponseStatusCodes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[ResponseStatusCode] | None:
        return super(cls, ResponseStatusCodes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[ResponseStatusCode] | None:
        return super(cls, ResponseStatusCodes).update(**kwargs)


class RequestStatusCodes(Base):
    model = RequestStatusCode

    @classmethod
    def get(cls, **kwargs) -> RequestStatusCode | None:
        return super(cls, RequestStatusCodes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[RequestStatusCode] | None:
        return super(cls, RequestStatusCodes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[RequestStatusCode] | None:
        return super(cls, RequestStatusCodes).update(**kwargs)


class InMessages(Base):
    model = InMessage

    @classmethod
    def get(cls, **kwargs) -> InMessage | None:
        return super(cls, InMessages).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[InMessage] | None:
        return super(cls, InMessages).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[InMessage] | None:
        return super(cls, InMessages).update(**kwargs)


class OutMessages(Base):
    model = OutMessage

    @classmethod
    def get(cls, **kwargs) -> OutMessage | None:
        return super(cls, OutMessages).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[OutMessage] | None:
        return super(cls, OutMessages).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[OutMessage] | None:
        return super(cls, OutMessages).update(**kwargs)


class InMessagesAttributes(Base):
    model = InMessagesAttribute

    @classmethod
    def get(cls, **kwargs) -> InMessagesAttribute | None:
        return super(cls, InMessagesAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[InMessagesAttribute] | None:
        return super(cls, InMessagesAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[InMessagesAttribute] | None:
        return super(cls, InMessagesAttributes).update(**kwargs)


class OutMessagesAttributes(Base):
    model = OutMessagesAttribute

    @classmethod
    def get(cls, **kwargs) -> OutMessagesAttribute | None:
        return super(cls, OutMessagesAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[OutMessagesAttribute] | None:
        return super(cls, OutMessagesAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[OutMessagesAttribute] | None:
        return super(cls, OutMessagesAttributes).update(**kwargs)


class HeaderAttributes(Base):
    model = HeaderAttribute

    @classmethod
    def get(cls, **kwargs) -> HeaderAttribute | None:
        return super(cls, HeaderAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[HeaderAttribute] | None:
        return super(cls, HeaderAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[HeaderAttribute] | None:
        return super(cls, HeaderAttributes).update(**kwargs)


class ApiUrlAttributes(Base):
    model = ApiUrlAttribute

    @classmethod
    def get(cls, **kwargs) -> ApiUrlAttribute | None:
        return super(cls, ApiUrlAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[ApiUrlAttribute] | None:
        return super(cls, ApiUrlAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[ApiUrlAttribute] | None:
        return super(cls, ApiUrlAttributes).update(**kwargs)


class UrlAttributes(Base):
    model = UrlAttribute

    @classmethod
    def get(cls, **kwargs) -> UrlAttribute | None:
        return super(cls, UrlAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[UrlAttribute] | None:
        return super(cls, UrlAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[UrlAttribute] | None:
        return super(cls, UrlAttributes).update(**kwargs)


class SelectorsAttributes(Base):
    model = SelectorsAttribute

    @classmethod
    def get(cls, **kwargs) -> SelectorsAttribute | None:
        return super(cls, SelectorsAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[SelectorsAttribute] | None:
        return super(cls, SelectorsAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[SelectorsAttribute] | None:
        return super(cls, SelectorsAttributes).update(**kwargs)


class SimpleRules(Base):
    model = SimpleRule

    @classmethod
    def get(cls, **kwargs) -> SimpleRule | None:
        return super(cls, SimpleRules).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[SimpleRule] | None:
        return super(cls, SimpleRules).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[SimpleRule] | None:
        return super(cls, SimpleRules).update(**kwargs)


class ComplexRules(Base):
    model = ComplexRule

    @classmethod
    def get(cls, **kwargs) -> ComplexRule | None:
        return super(cls, ComplexRules).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[ComplexRule] | None:
        return super(cls, ComplexRules).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[ComplexRule] | None:
        return super(cls, ComplexRules).update(**kwargs)


class StringAttributesConfiguration(Base):
    model = StringAttributeConfiguration

    @classmethod
    def get(cls, **kwargs) -> StringAttributeConfiguration | None:
        return super(cls, StringAttributesConfiguration).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[StringAttributeConfiguration] | None:
        return super(cls, StringAttributesConfiguration).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[StringAttributeConfiguration] | None:
        return super(cls, StringAttributesConfiguration).update(**kwargs)


class DateAttributesConfiguration(Base):
    model = DateAttributeConfiguration

    @classmethod
    def get(cls, **kwargs) -> DateAttributeConfiguration | None:
        return super(cls, DateAttributesConfiguration).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[DateAttributeConfiguration] | None:
        return super(cls, DateAttributesConfiguration).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[DateAttributeConfiguration] | None:
        return super(cls, DateAttributesConfiguration).update(**kwargs)


class ElementsGroups(Base):
    model = ElementsGroup

    @classmethod
    def get(cls, **kwargs) -> ElementsGroup | None:
        return super(cls, ElementsGroups).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[ElementsGroup] | None:
        return super(cls, ElementsGroups).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[ElementsGroup] | None:
        return super(cls, ElementsGroups).update(**kwargs)


class OutputAttributes(Base):
    model = OutputAttribute

    @classmethod
    def get(cls, **kwargs) -> OutputAttribute | None:
        return super(cls, OutputAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[OutputAttribute] | None:
        return super(cls, OutputAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[OutputAttribute] | None:
        return super(cls, OutputAttributes).update(**kwargs)


class Hooks(Base):
    model = Hook

    @classmethod
    def get(cls, **kwargs) -> Hook | None:
        return super(cls, Hooks).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[Hook] | None:
        return super(cls, Hooks).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[Hook] | None:
        return super(cls, Hooks).update(**kwargs)


class NamingAttributes(Base):
    model = NamingAttribute

    @classmethod
    def get(cls, **kwargs) -> NamingAttribute | None:
        return super(cls, NamingAttributes).get(**kwargs)

    @classmethod
    def get_all(cls, **kwargs) -> List[NamingAttribute] | None:
        return super(cls, NamingAttributes).get_all(**kwargs)

    @classmethod
    def update(cls, **kwargs) -> List[NamingAttribute] | None:
        return super(cls, NamingAttributes).update(**kwargs)