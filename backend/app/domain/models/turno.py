import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin
from app.domain.models.enums import EstadoTurno, OrigenTurno

if TYPE_CHECKING:
    from app.domain.models.usuario import Usuario


class Turno(Base, TimestampMixin):
    """Appointment reservation entity with state machine and time intervals."""

    __tablename__ = "turnos"
    __table_args__ = (
        CheckConstraint("fin > inicio", name="ck_turno_fin_mayor_inicio"),
        Index("ix_turnos_odontologo_inicio", "odontologo_id", "inicio"),
        Index("ix_turnos_paciente_inicio", "paciente_id", "inicio"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    paciente_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    odontologo_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    inicio: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    fin: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    motivo: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoTurno] = mapped_column(
        Enum(EstadoTurno, values_callable=lambda x: [e.value for e in x], native_enum=False, length=20),
        default=EstadoTurno.SOLICITADO,
        nullable=False,
    )
    origen: Mapped[OrigenTurno] = mapped_column(
        Enum(OrigenTurno, values_callable=lambda x: [e.value for e in x], native_enum=False, length=20),
        default=OrigenTurno.ONLINE,
        nullable=False,
    )

    # Relationships
    paciente: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[paciente_id],
        back_populates="turnos_como_paciente",
        lazy="selectin",
    )
    odontologo: Mapped["Usuario"] = relationship(
        "Usuario",
        foreign_keys=[odontologo_id],
        back_populates="turnos_como_odontologo",
        lazy="selectin",
    )


# Database-level anti-overlap enforcement for SQLite (used in test suite)
# Fulfills RN-AG-01 server-side invariant without mocks
from sqlalchemy import DDL, event

_sqlite_overlap_insert_trigger = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_prevent_turno_overlap_insert
BEFORE INSERT ON turnos
FOR EACH ROW
WHEN lower(NEW.estado) NOT IN ('cancelado', 'anulado')
BEGIN
    SELECT RAISE(ABORT, 'RN-AG-01: Invariante anti-solape violada para el odontologo')
    WHERE EXISTS (
        SELECT 1 FROM turnos
        WHERE odontologo_id = NEW.odontologo_id
          AND lower(estado) NOT IN ('cancelado', 'anulado')
          AND inicio < NEW.fin
          AND fin > NEW.inicio
    );
END;
""")

_sqlite_overlap_update_trigger = DDL("""
CREATE TRIGGER IF NOT EXISTS trg_prevent_turno_overlap_update
BEFORE UPDATE ON turnos
FOR EACH ROW
WHEN lower(NEW.estado) NOT IN ('cancelado', 'anulado')
BEGIN
    SELECT RAISE(ABORT, 'RN-AG-01: Invariante anti-solape violada para el odontologo')
    WHERE EXISTS (
        SELECT 1 FROM turnos
        WHERE odontologo_id = NEW.odontologo_id
          AND lower(estado) NOT IN ('cancelado', 'anulado')
          AND inicio < NEW.fin
          AND fin > NEW.inicio
          AND id != NEW.id
    );
END;
""")

event.listen(Turno.__table__, "after_create", _sqlite_overlap_insert_trigger.execute_if(dialect="sqlite"))
event.listen(Turno.__table__, "after_create", _sqlite_overlap_update_trigger.execute_if(dialect="sqlite"))
