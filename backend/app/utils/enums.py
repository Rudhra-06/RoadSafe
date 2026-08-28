from enum import Enum


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    RESPONDER = "RESPONDER"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"


class ResponderType(str, Enum):
    CAR_MECHANIC = "CAR_MECHANIC"
    BIKE_MECHANIC = "BIKE_MECHANIC"
    PARAMEDIC = "PARAMEDIC"
    TOWING_OPERATOR = "TOWING_OPERATOR"
    ROADSIDE_TECHNICIAN = "ROADSIDE_TECHNICIAN"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    EMERGENCY = "EMERGENCY"


class TicketStatus(str, Enum):
    REQUESTED = "REQUESTED"
    DISPATCHING = "DISPATCHING"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    EN_ROUTE = "EN_ROUTE"
    ARRIVED = "ARRIVED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_RESPONDER = "NO_RESPONDER"
    REASSIGN = "REASSIGN"
    FAILED = "FAILED"


# Allowed state transitions for validation logic
VALID_TICKET_TRANSITIONS = {
    TicketStatus.REQUESTED: {TicketStatus.DISPATCHING, TicketStatus.CANCELLED},
    TicketStatus.DISPATCHING: {TicketStatus.ASSIGNED, TicketStatus.NO_RESPONDER, TicketStatus.CANCELLED},
    TicketStatus.ASSIGNED: {TicketStatus.ACCEPTED, TicketStatus.REASSIGN, TicketStatus.CANCELLED},
    TicketStatus.ACCEPTED: {TicketStatus.EN_ROUTE, TicketStatus.CANCELLED, TicketStatus.REASSIGN},
    TicketStatus.EN_ROUTE: {TicketStatus.ARRIVED, TicketStatus.CANCELLED, TicketStatus.REASSIGN},
    TicketStatus.ARRIVED: {TicketStatus.IN_SERVICE, TicketStatus.CANCELLED, TicketStatus.REASSIGN},
    TicketStatus.IN_SERVICE: {TicketStatus.COMPLETED, TicketStatus.FAILED},
    TicketStatus.COMPLETED: set(),
    TicketStatus.CANCELLED: set(),
    TicketStatus.NO_RESPONDER: {TicketStatus.DISPATCHING, TicketStatus.REASSIGN},
    TicketStatus.REASSIGN: {TicketStatus.DISPATCHING},
    TicketStatus.FAILED: set(),
}


class AssignmentStatus(str, Enum):
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class InvoiceStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    VOID = "VOID"


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

