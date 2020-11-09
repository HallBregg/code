from dataclasses import dataclass
from typing import Optional, NoReturn, Union
from datetime import date

from allocation.domain import events, commands


class OutOfStock(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(
        self, ref: str, sku: str, qty: int, eta: Optional[date]
    ):
        self.reference = ref
        self.sku = sku
        self.eta = eta  # Estimated time of arrival
        self._purchased_quantity = qty
        self._allocations: set[OrderLine] = set()

    # https://hynek.me/articles/hashes-and-equality/
    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False
        return self.reference == other.reference

    # Enables use of comparison and sort on Batch objects
    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __hash__(self):
        return hash(self.reference)

    @property
    def allocated_quantity(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def allocate(self, line: OrderLine) -> NoReturn:
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine) -> NoReturn:
        if line in self._allocations:
            self._allocations.remove(line)

    def can_allocate(self, line: OrderLine) -> bool:
        return self.sku == line.sku and self.available_quantity >= line.qty

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()


class Product:

    def __init__(self, sku: str, batches: list[Batch], version_number: int = 0):
        self.sku: str = sku
        self.batches = batches
        self.version_number = version_number
        self.events: list[Union[commands.Command, events.Event]] = []

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            # We dont need to raise exceptions because events will handle that.
            # raise OutOfStock(f'Out of stock for sku {line.sku}')
        else:
            return batch.reference

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(b for b in self.batches if b.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(commands.Allocate(line.orderid, line.sku, line.qty))
