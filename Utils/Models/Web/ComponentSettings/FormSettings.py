from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base
from Utils.Models.Web.ComponentSettings.ElementSettings import ElementSettings


@dataclass(init=False)
class FormSettings(Base):

    id: int = field(metadata={'column': 'componentId'}, default=None)
    tag: ElementSettings = field(metadata={'column': 'formTag'}, default=None)
    reset: ElementSettings = field(metadata={'column': 'formReset'}, default=None)
    cancel: ElementSettings = field(metadata={'column': 'formCancel'}, default=None)
    inputs: list[ElementSettings] = field(metadata={'column': 'formInputs'}, default=None)
    submit: ElementSettings = field(metadata={'column': 'formSubmit'}, default=None)

    def __init__(self, data):
        super(FormSettings, self).__init__(data)
        self.__post_init__()

    def __post_init__(self):
        self.tag = ElementSettings(self.tag)
        self.reset = ElementSettings(self.reset)
        self.cancel = ElementSettings(self.cancel)
        if self.inputs:
            self.inputs = [ElementSettings(input) for input in self.inputs]
        self.submit = ElementSettings(self.submit)
