import logging
from Utils.Models.Repository import *
from Utils.Web.Handlers.Location import Location


class Validators:
    def __init__(self, helpers, handlers, web):
        self.h = helpers
        self.handlers = handlers
        self.web = web
        self.locations_handlers = {
            'LINK': self.handlers.handle_button_as_link,
            'BUTTON': self.handlers.handle_button_as_button,
            'CLICK': self.handlers.handle_button_as_button,
            'HOVER': self.handlers.handle_hover,
            'INPUT': self.handlers.handle_input,
            'ANY_TEXT': self.handlers.handle_any,
            'CONTAINER': self.handlers.handle_any,
            'DROPDOWN': self.handlers.handle_dropdown,
            'ELEMENT_GROUP': self.handlers.handle_any,
            'TABLE': self.handlers.handle_table,
            'CALENDAR': self.handlers.handle_calendar,
            'FORM': self.handlers.handle_form,
            'MODAL': self.handlers.handle_modal
        }

    def validate_component(self, component: Component):
        """ Validates and interacts with a component. \n
            - validates and handles hooks
            - validates and handles simple and complex rules
            - if the component has an associated element, it is validated and handled
            - if the associated element is of type 'submit', it is skipped, because it will be handled in a different
              test step

            Parameters
            ----------
            component: Series
                the component data, a row from the components dataframe
        """
        logging.debug(f'Begin component {component.friendly} validation')
        try:
            # handle component location
            location = Location(component, self.h, self.handlers)
            location.validate()

            hooks = Hooks.get_all(componentId=component.id)
            self.handlers.handle_hooks('OnInit', hooks)
            self.web.rules_handler.handle_condition(component, 'existenceCondition')

            # validate associated element
            if component.associatedElementId:
                try:
                    element = InputAttributes.get(id=component.associatedElementId)
                    self.validate_element(element)
                except Exception as e:
                    raise Exception(f'Element associated to {component.friendly} failed validation. {e}')

            if component.type:
                method_to_call = self.locations_handlers.get(component.type.upper(), None)
                if method_to_call:
                    method_to_call(component)
                elif hasattr(component, 'selector_id'):
                    self.handlers.handle_any(component)

            # self.web.rules_handler.handle_condition(component, 'validDataCondition')
            self.handlers.handle_hooks('OnDestroy', hooks)

            location.validate_out()
        except Exception as e:
            message = f'Component {component.friendly} validation failed. Error: {e}'
            logging.error(message)
            raise Exception(message)
        logging.debug(f'End component {component.friendly} validation')

    def validate_element(self, element: InputAttribute, trigger_type=None, parent_element=None):
        """ Validates and interacts with an element. \n
            - validates and handles simple and complex rules
            - depending on the type of element, interacts with it

            Parameters
            ----------
            element: Series
                the element data, a row from the elements dataframe
            trigger_type: String, optional
                if this element is triggered by another object,
                specifies the action of the trigger (click, hover)
        """
        if element.generated is True:
            return

        logging.debug(f'Begin element {element.friendly} validation.')
        if parent_element is None:
            parent_element = self.web.driver
        try:
            element_type = element.elementType.upper()
        except (Exception,):
            try:
                element_type = element.subType.upper()
            except (Exception,):
                element_type = trigger_type.upper()

        self.validate_events(element, 'input')
        method_to_call = self.locations_handlers.get(element_type, None)
        if method_to_call is not None:
            method_to_call(element, parent_element)
        else:
            self.handlers.handle_any(element, parent_element)
        self.web.rules_handler.handle_condition(element, element_col='existenceCondition')
        self.validate_events(element, 'output')
        logging.debug(f'End element {element.friendly} validation.')

    def validate_element_group(self, element_group: ElementsGroup, parent_element=None):
        """ Validates and interacts with an element group. \n
            - validates and handles the group as an element, because it has its own selector, rules
              and can be triggered by another objects
            - validates and handles each element of the group
            - if an element is of type 'submit', it is skipped, because it will be handled in a different
              test step

            Parameters
            ----------
            element_group: Series
                the element_group data, a row from the elementGroups dataframe
        """
        if element_group.generated:
            return

        logging.debug(f'Begin element group {element_group.friendly} validation')
        self.web.rules_handler.handle_condition(element_group, 'existenceCondition')
        logging.debug(f'End element group {element_group.friendly} validation')

    def validate_events(self, element: InputAttribute, event_type='input'):
        """ Handles input and output events for an element. \n
            Events supported: requests, element groups

            Parameters
            ----------
            element: Series
                element data, a row from the dataframe
            event_type: String, optional
                the type of event, input/output, default is 'inputEvents'
        """

        logging.debug(f'Begin handle {event_type} for element {element.friendly}')
        for event in element.elementEvents:
            if event['eventDirection'] != event_type.upper():
                continue

            trigger_type = event['triggerType']
            trigger_id = event['triggerEntityId']
            if trigger_type is None or trigger_id is None:
                continue

            if trigger_type == 'ENDPOINT':
                endpoints = Endpoints.get_all(endpoint_id=trigger_id)
                self.handlers.handle_endpoint(endpoints)
            elif trigger_type == 'MESSAGES':
                dataframe = InMessages if event_type == 'input' else OutMessages
                message = dataframe.get(id=trigger_id)
                message_type = 'in' if event_type == 'input' else 'out'
                self.handlers.handle_message(message, message_type)
            elif trigger_type in ['ELEMENT GROUPS', 'COMPONENT', 'PAGE']:
                # there's no need to validate these entities, because this should be a step in the path
                continue

        logging.debug(f'End handle {event_type} for element {element.friendly}')

    @staticmethod
    def validate_response():
        logging.debug(f'Begin')
        logging.debug(f'End')
