import json

from Utils.Models.Repository import *
from Utils.Models.Web.ComponentSettings.ElementSettings import ElementType
from Utils.Models.Web.ComponentSettings.FormSettings import FormSettings


class Form:
    def __init__(self, component: Component, helpers, handlers):
        self.h = helpers
        self.handlers = handlers
        self.component = component
        self.settings = FormSettings(json.loads(component.componentSettings))

    def validate(self, parent_element):
        if parent_element is None:
            parent_element = self.handlers.web.driver

        form_element = self.validate_tag(parent_element)
        if form_element is None:
            form_element = parent_element
        self.validate_body(form_element)
        self.validate_action_buttons(form_element)

    def validate_tag(self, parent_element):
        if not self.settings.tag.id:
            return None
        if self.settings.tag.type == ElementType.ELEMENT.value:
            form_element = InputAttributes.get(id=self.settings.tag.id)
            self.handlers.web.validators.validate_element(form_element, parent_element)
        elif self.settings.tag.type == ElementType.ELEMENT_GROUP.value:
            form_element = ElementsGroups.get(id=self.settings.tag.id)
            self.handlers.web.validators.validate_element_group(form_element, parent_element)
        else:
            return None
        return self.handlers.get_html_element(form_element, parent_element)

    def validate_body(self, parent_element):
        if self.settings.inputs is None:
            return
        for body_input in self.settings.inputs:
            if not body_input.id:
                continue
            if body_input.type == ElementType.ELEMENT.value:
                body_input = InputAttributes.get(id=body_input.id)
                # will be handled later in the path
                # self.handlers.web.validators.validate_element(body_input, parent_element)
            else:
                body_input = ElementsGroups.get(id=body_input.id)
                # will be handled later in the path
                # self.handlers.web.validators.validate_element_group(body_input, parent_element)

    def validate_action_buttons(self, parent_element):
        if not self.settings.submit.id:
            return
        if self.settings.submit.type == ElementType.ELEMENT.value:
            action_button = InputAttributes.get(id=self.settings.submit.id)
            # will be handled later in the path
            # self.handlers.web.validators.validate_element(action_button, parent_element)
        elif self.settings.submit.type == ElementType.ELEMENT_GROUP.value:
            action_button = ElementsGroups.get(id=self.settings.submit.id)
            # will be handled later in the path
            self.handlers.web.validators.validate_element_group(action_button, parent_element)
