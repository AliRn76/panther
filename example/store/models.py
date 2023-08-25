from panther.db import Model


class Store(Model):
    name: str
    address: str
