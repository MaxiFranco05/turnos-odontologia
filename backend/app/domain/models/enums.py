from enum import Enum


class RolUsuario(str, Enum):
    """User roles defining system capabilities and access levels."""
    PACIENTE = "paciente"
    RECEPCION = "recepcion"
    ODONTOLOGO = "odontologo"


class EstadoTurno(str, Enum):
    """Lifecycle states of an appointment."""
    SOLICITADO = "solicitado"
    CONFIRMADO = "confirmado"
    ANULADO = "anulado"
    CANCELADO = "cancelado"
    PRESENTE = "presente"
    AUSENTE = "ausente"


class OrigenTurno(str, Enum):
    """Origin channel of an appointment booking."""
    ONLINE = "online"
    MANUAL = "manual"
