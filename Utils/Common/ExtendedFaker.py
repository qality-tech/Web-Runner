import os
from contextlib import suppress

from faker import Faker
from faker_datasets import Provider, add_dataset
from pathlib import Path


@add_dataset("cars", os.path.join(os.path.dirname(__file__), 'faker_data/cars.json'), picker="car")
class Cars(Provider):
    pass


class ExtendedFaker:
    def __init__(self):
        self.faker = Faker()
        with suppress(Exception):
            self.faker.add_provider(Cars)

