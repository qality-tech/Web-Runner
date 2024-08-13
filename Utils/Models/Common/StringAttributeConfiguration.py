from dataclasses import dataclass, field

from Utils.Models.ModelBase import Base


@dataclass(init=False)
class StringAttributeConfiguration(Base):

    def __init__(self, data):
        super(StringAttributeConfiguration, self).__init__(data)