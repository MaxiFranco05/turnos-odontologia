from typing import TYPE_CHECKING
from sqlalchemy import Boolean, CheckConstraint, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base, TimestampMixin
from app.domain.models.enums import RolUsuario

if TYPE_CHECKING:
    from app.domain.models.plantilla import PlantillaDisponibilidad
    from app.domain.models.turno import Turno


class Usuario(Base, TimestampMixin):
    """User account model supporting multi-role access (paciente, recepcion, odontologo)."""

    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "(email IS NOT NULL) OR (nro_socio IS NOT NULL)",
            name="ck_usuario_identificador_presente",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    nro_socio: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    debe_cambiar_password: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    perfil_completo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        Enum(RolUsuario, values_callable=lambda x: [e.value for e in x], native_enum=False, length=20),
        nullable=False,
    )

    # Relationships
    turnos_como_paciente: Mapped[list["Turno"]] = relationship(
        "Turno",
        foreign_keys="Turno.paciente_id",
        back_populates="paciente",
        lazy="selectin",
    )
    turnos_como_odontologo: Mapped[list["Turno"]] = relationship(
        "Turno",
        foreign_keys="Turno.odontologo_id",
        back_populates="odontologo",
        lazy="selectin",
    )
    plantillas: Mapped[list["PlantillaDisponibilidad"]] = relationship(
        "PlantillaDisponibilidad",
        back_populates="odontologo",
        lazy="selectin",
    )
