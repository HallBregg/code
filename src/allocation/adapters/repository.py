import abc

from allocation.domain import model


# Port
class AbstractRepository(abc.ABC):

    def __init__(self):
        self.seen: set[model.Product] = set()

    def add(self, product):
        self._add(product)
        self.seen.add(product)

    def get(self, sku) -> model.Product:
        if product := self._get(sku):
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError


# Adapter
class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()
