import abc

from allocation.domain import model


# Port
class AbstractRepository(abc.ABC):

    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

    def list(self):
        pass


# Adapter
class SqlAlchemyRepository(AbstractRepository):

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        # Return exactly one result or raise an exception.
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()


# Adapter
class SqlRepository(AbstractRepository):
    # No need to use ORM :)

    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.execute(
            'INSERT INTO batches (reference, sku, _purchased_quantity, eta)'
            'VALUES (:reference, :sku, :_purchased_quantity, :eta)',
            dict(
                reference=batch.reference,
                sku=batch.sku,
                _purchased_quantity=batch._purchased_quantity,
                eta=batch.eta,
            )
        )

    def get(self, reference):
        try:
            [data] = self.session.execute(
                'SELECT * FROM batches WHERE reference=:reference',
                dict(reference=reference)
            )
        except ValueError:
            raise ValueError('Caught error :) No object, or too many objects')
        else:
            # Won't work because of id
            return model.Batch(*data)
