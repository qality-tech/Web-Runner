import json

from Utils.Models.Repository import *
from Utils.Models.Web.ComponentSettings.FormSettings import FormSettings


class Table:
    def __init__(self, component: Component, helpers, handlers):
        self.h = helpers
        self.handlers = handlers
        self.component = component
        pass