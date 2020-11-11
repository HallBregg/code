from typing import Callable, Union
import logging

from tenacity import Retrying, stop_after_attempt, wait_exponential, RetryError

from allocation.service_layer import unit_of_work

from allocation.domain import events, commands
from allocation.service_layer import handlers


logger = logging.getLogger(__name__)

Message = Union[commands.Command, events.Event]


def handle_event(
    event: events.Event,
    queue: list[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            for attempt in Retrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential()
            ):
                with attempt:
                    logger.debug(f'handling event {event} with handler {handler}')
                    handler(event, uow=uow)
                    queue.extend(uow.collect_new_events())
        except RetryError as retry_failure:
            logger.exception(
                f'Failed to handle event {event} {retry_failure.last_attempt.attempt_number} times'
            )
            continue


def handle_command(
    command: commands.Command,
    queue: list[Message],
    uow: unit_of_work.AbstractUnitOfWork
):
    logger.debug(f'Handling command {command}')
    try:
        handler = COMMAND_HANDLER[type(command)]
        result = handler(command, uow=uow)
        queue.extend(uow.collect_new_events())
        return result
    except Exception:
        logger.exception(f'Exception handling command {command}')
        raise


def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    results = []
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            cmd_result = handle_command(message, queue, uow)
            results.append(cmd_result)
        else:
            raise Exception(f'{message} was not an Event or Command')
    return results


EVENT_HANDLERS: dict[type[events.Event], list[Callable]] = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.Allocated: [handlers.publish_allocated_event]
}

COMMAND_HANDLER: dict[type[commands.Command], Callable] = {
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
    commands.Allocate: handlers.allocate,
}
