import logging


class Fake(object):
    """
        Class that encapsulates values in an object. \n
        Used for adding arrays in dataframes cells.
    """

    def __init__(self, li_obj=None):
        self.value = li_obj
        logging.debug(li_obj)

    def get_type(self):
        return type(self.value)

    def get_value(self):
        return str(self.value)
