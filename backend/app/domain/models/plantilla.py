import datetime
from typing import TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, SmallInteger, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.domain.models.usuario import Usuario


class PlantillaDisponibilidad(Base, TimestampMixin):
    """Weekly recurring availability template defined per dentist."""

    __tablename__ = "plantillas_disponibilidad"
    __table_args__ = (
        CheckConstraint("hora_fin > hora_inicio", name="ck_plantilla_horario_valido"),
        CheckConstraint("duracion_slot_minutos > 0", name="ck_plantilla_duracion_positiva"),
        CheckConstraint("dia_semana >= 0 AND dia_semana <= 6", name="ck_plantilla_dia_semana_valido"),
        Index("ix_plantillas_odontologo_dia", "odontologo_id", "dia_semana"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    odontologo_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    dia_semana: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    hora_inicio: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    duracion_slot_minutos: Mapped[int] = mapped_column(Integer, nullable=False)
    prestacion: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    odontologo: Mapped["Usuario"] = relationship(
        "Usuario",
        back_populates="plantillas",
        lazy="selectin",
    )
