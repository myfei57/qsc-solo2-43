"""Single use, generation bound confirmations."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from ..runtime.ids import IdSequencer
from .errors import (
    InvalidTicketRequest,
    TicketSubjectMismatch,
    UnknownTicket,
)


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    subject: str
    issued_tick: int
    context: Dict[str, Any] = field(default_factory=dict)

    def describe(self) -> Dict[str, Any]:
        return {
            "ticket": self.ticket_id,
            "subject": self.subject,
            "issued_tick": self.issued_tick,
            "context": dict(self.context),
        }


class TicketRegistry:
    """Confirmations expire on the tick clock and never survive a generation bump."""

    def __init__(self, ids: IdSequencer, prefix: str = "TCK") -> None:
        self._ids = ids
        self._prefix = prefix
        self._tickets: Dict[str, Ticket] = {}

    def issue(
        self,
        subject: str,
        generation: int,
        ttl_ticks: int,
        context: Dict[str, Any],
        now: int,
    ) -> Ticket:
        if not subject:
            raise InvalidTicketRequest("ticket subject must not be empty")
        ticket = Ticket(
            ticket_id=self._ids.next(self._prefix),
            subject=subject,
            issued_tick=int(now),
            context=dict(context),
        )
        self._tickets[ticket.ticket_id] = ticket
        return ticket

    def peek(self, ticket_id: str) -> Ticket:
        ticket = self._tickets.get(ticket_id)
        if ticket is None:
            raise UnknownTicket("no such confirmation", ticket=ticket_id)
        return ticket

    def consume(self, ticket_id: str, subject: str, generation: int, now: int) -> Ticket:
        ticket = self.peek(ticket_id)
        if ticket.subject != subject:
            raise TicketSubjectMismatch(
                "confirmation was issued for another action",
                ticket=ticket_id,
                expected=ticket.subject,
                observed=subject,
            )
        return ticket

    def tickets(self) -> List[Ticket]:
        return [self.peek(ticket_id) for ticket_id in sorted(self._tickets)]

    def pending(self, now: int) -> List[Ticket]:
        return self.tickets()

    def expired(self, now: int) -> List[Ticket]:
        return []

    def issued_count(self, subject: str = "") -> int:
        if not subject:
            return len(self._tickets)
        return sum(1 for item in self.tickets() if item.subject == subject)

    def summary(self, now: int) -> Dict[str, Any]:
        return {
            "issued": len(self._tickets),
            "pending": len(self.pending(now)),
            "expired": len(self.expired(now)),
        }
