from Utils.Models.Repository import *


class Location:
    def __init__(self, component: Component, helpers, handlers):
        self.h = helpers
        self.handlers = handlers
        self.component = component

    def validate(self):
        if self.component.componentLocationLocation == 'MODAL':
            location_modal = Components.get(id=self.component.componentLocationModalComponentId)
            # TODO: manareala
            # self.handlers.handle_modal(location_modal)
            self.handlers.handle_iframe(location_modal)
        elif self.component.componentLocationLocation == 'IFRAME':
            location_modal = Components.get(id=self.component.componentLocationIframeTagElementId)
            self.handlers.handle_iframe(location_modal)

    def validate_out(self):
        if self.component.componentLocationLocation == 'IFRAME':
            # TODO: manareala
            # self.handlers.handle_iframe_out()
            pass
