import datetime
import logging
from zoneinfo import ZoneInfo
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.enums import EstadoTurno, OrigenTurno, RolUsuario
from app.domain.models.plantilla import PlantillaDisponibilidad
from app.domain.models.turno import Turno
from app.domain.models.usuario import Usuario
from app.infrastructure.config import get_settings
from app.infrastructure.security import hash_password

logger = logging.getLogger("seed")


def _get_timezone_str() -> str:
    try:
        return get_settings().TIMEZONE
    except Exception:
        return "America/Argentina/Buenos_Aires"


async def seed_data(
    session: AsyncSession,
    reset: bool = False,
    base_date: datetime.date | None = None,
    timezone_str: str | None = None,
) -> dict[str, int]:
    """Idempotently seeds baseline accounts, templates, and demonstration appointments.

    Complies with:
    - Hard Rule #2: Pure SQLAlchemy 2.0 select() and delete().
    - Hard Rule #3: Synchronous password hashing and date calculations.
    - Hard Rule #12: 100% synthetic demonstration data.
    - Hard Rule #13: Strict non-overlapping intervals on dentist agenda.
    - RN-AU-01 & US-001: Reception account created with debe_cambiar_password=True.
    - RN-AG-01: Non-overlapping weekday templates.
    """
    tz_name = timezone_str or _get_timezone_str()
    tz = ZoneInfo(tz_name)

    if reset:
        logger.info("Resetting existing database records...")
        bind = session.get_bind()
        if bind is not None and bind.dialect.name == "postgresql":
            await session.execute(
                text(
                    "TRUNCATE TABLE turnos, plantillas_disponibilidad, usuarios RESTART IDENTITY CASCADE"
                )
            )
        else:
            await session.execute(delete(Turno))
            await session.execute(delete(PlantillaDisponibilidad))
            await session.execute(delete(Usuario))
        await session.flush()

    # -------------------------------------------------------------
    # 1. Accounts Seeding
    # -------------------------------------------------------------
    users_spec = [
        {
            "nombre": "Recepción Central",
            "email": "recepcion@turnosodontologia.com",
            "nro_socio": None,
            "password": "Admin1234!",
            "rol": RolUsuario.RECEPCION,
            "debe_cambiar_password": True,
            "perfil_completo": True,
        },
        {
            "nombre": "Dra. Sofía Martín",
            "email": "sofia.martin@turnosodontologia.com",
            "nro_socio": "ODO-001",
            "password": "Dentist1234!",
            "rol": RolUsuario.ODONTOLOGO,
            "debe_cambiar_password": False,
            "perfil_completo": True,
            "specialty": "Odontología General",
        },
        {
            "nombre": "Dr. Lucas García",
            "email": "lucas.garcia@turnosodontologia.com",
            "nro_socio": "ODO-002",
            "password": "Dentist1234!",
            "rol": RolUsuario.ODONTOLOGO,
            "debe_cambiar_password": False,
            "perfil_completo": True,
            "specialty": "Ortodoncia y Prótesis",
        },
        {
            "nombre": "Carlos Benítez",
            "email": "carlos.benitez@example.com",
            "nro_socio": "SOC-101",
            "password": "Patient1234!",
            "rol": RolUsuario.PACIENTE,
            "debe_cambiar_password": False,
            "perfil_completo": True,
        },
        {
            "nombre": "Lucía Gómez",
            "email": "lucia.gomez@example.com",
            "nro_socio": "SOC-102",
            "password": "Patient1234!",
            "rol": RolUsuario.PACIENTE,
            "debe_cambiar_password": False,
            "perfil_completo": True,
        },
    ]

    users_by_email: dict[str, Usuario] = {}
    for u_spec in users_spec:
        # Check if user already exists by email or nro_socio
        conditions = []
        if u_spec["email"]:
            conditions.append(Usuario.email == u_spec["email"])
        if u_spec["nro_socio"]:
            conditions.append(Usuario.nro_socio == u_spec["nro_socio"])

        existing_user: Usuario | None = None
        if conditions:
            from sqlalchemy import or_
            stmt = select(Usuario).where(or_(*conditions))
            existing_user = await session.scalar(stmt)

        if existing_user is None:
            user = Usuario(
                nombre=u_spec["nombre"],
                email=u_spec["email"],
                nro_socio=u_spec["nro_socio"],
                password_hash=hash_password(u_spec["password"]),
                rol=u_spec["rol"],
                debe_cambiar_password=u_spec["debe_cambiar_password"],
                perfil_completo=u_spec["perfil_completo"],
            )
            session.add(user)
            await session.flush()
            users_by_email[u_spec["email"]] = user
        else:
            users_by_email[u_spec["email"]] = existing_user

    # -------------------------------------------------------------
    # 2. Recurring Weekly Availability Templates Seeding (RN-AG-01)
    # -------------------------------------------------------------
    dentists_info = [
        ("sofia.martin@turnosodontologia.com", "Odontología General"),
        ("lucas.garcia@turnosodontologia.com", "Ortodoncia y Prótesis"),
    ]

    for email, prestacion in dentists_info:
        dentist = users_by_email[email]
        # Monday (0) through Friday (4)
        for dia_semana in range(0, 5):
            # Morning Shift: 09:00 to 13:00 (30 min slot)
            morning_stmt = select(PlantillaDisponibilidad).where(
                PlantillaDisponibilidad.odontologo_id == dentist.id,
                PlantillaDisponibilidad.dia_semana == dia_semana,
                PlantillaDisponibilidad.hora_inicio == datetime.time(9, 0),
                PlantillaDisponibilidad.hora_fin == datetime.time(13, 0),
            )
            if await session.scalar(morning_stmt) is None:
                session.add(
                    PlantillaDisponibilidad(
                        odontologo_id=dentist.id,
                        dia_semana=dia_semana,
                        hora_inicio=datetime.time(9, 0),
                        hora_fin=datetime.time(13, 0),
                        duracion_slot_minutos=30,
                        prestacion=prestacion,
                    )
                )

            # Afternoon Shift: 14:00 to 18:00 (30 min slot)
            afternoon_stmt = select(PlantillaDisponibilidad).where(
                PlantillaDisponibilidad.odontologo_id == dentist.id,
                PlantillaDisponibilidad.dia_semana == dia_semana,
                PlantillaDisponibilidad.hora_inicio == datetime.time(14, 0),
                PlantillaDisponibilidad.hora_fin == datetime.time(18, 0),
            )
            if await session.scalar(afternoon_stmt) is None:
                session.add(
                    PlantillaDisponibilidad(
                        odontologo_id=dentist.id,
                        dia_semana=dia_semana,
                        hora_inicio=datetime.time(14, 0),
                        hora_fin=datetime.time(18, 0),
                        duracion_slot_minutos=30,
                        prestacion=prestacion,
                    )
                )

    await session.flush()

    # -------------------------------------------------------------
    # 3. Demonstration Appointments Seeding (Hard Rule #13)
    # -------------------------------------------------------------
    if base_date is None:
        today = datetime.date.today()
        # Find next Monday to ensure it falls on a template weekday
        days_ahead = (0 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target_date = today + datetime.timedelta(days=days_ahead)
    else:
        target_date = base_date

    sofia = users_by_email["sofia.martin@turnosodontologia.com"]
    lucas = users_by_email["lucas.garcia@turnosodontologia.com"]
    carlos = users_by_email["carlos.benitez@example.com"]
    lucia = users_by_email["lucia.gomez@example.com"]

    demo_turnos = [
        # Turno 1: Dra. Sofía, Carlos (09:00 - 09:30, confirmado, online)
        {
            "paciente_id": carlos.id,
            "odontologo_id": sofia.id,
            "inicio": datetime.datetime.combine(target_date, datetime.time(9, 0), tzinfo=tz),
            "fin": datetime.datetime.combine(target_date, datetime.time(9, 30), tzinfo=tz),
            "motivo": "Limpieza y control general",
            "estado": EstadoTurno.CONFIRMADO,
            "origen": OrigenTurno.ONLINE,
        },
        # Turno 2: Dra. Sofía, Lucía (10:00 - 10:30, solicitado, online)
        {
            "paciente_id": lucia.id,
            "odontologo_id": sofia.id,
            "inicio": datetime.datetime.combine(target_date, datetime.time(10, 0), tzinfo=tz),
            "fin": datetime.datetime.combine(target_date, datetime.time(10, 30), tzinfo=tz),
            "motivo": "Consulta odontológica general",
            "estado": EstadoTurno.SOLICITADO,
            "origen": OrigenTurno.ONLINE,
        },
        # Turno 3: Dr. Lucas, Carlos (14:00 - 14:30, cancelado, online - US-005 tracking)
        {
            "paciente_id": carlos.id,
            "odontologo_id": lucas.id,
            "inicio": datetime.datetime.combine(target_date, datetime.time(14, 0), tzinfo=tz),
            "fin": datetime.datetime.combine(target_date, datetime.time(14, 30), tzinfo=tz),
            "motivo": "Control de ortodoncia cancelado",
            "estado": EstadoTurno.CANCELADO,
            "origen": OrigenTurno.ONLINE,
        },
        # Turno 4: Dr. Lucas, Lucía (15:00 - 15:30, confirmado, manual)
        {
            "paciente_id": lucia.id,
            "odontologo_id": lucas.id,
            "inicio": datetime.datetime.combine(target_date, datetime.time(15, 0), tzinfo=tz),
            "fin": datetime.datetime.combine(target_date, datetime.time(15, 30), tzinfo=tz),
            "motivo": "Instalación de brackets",
            "estado": EstadoTurno.CONFIRMADO,
            "origen": OrigenTurno.MANUAL,
        },
    ]

    for t_spec in demo_turnos:
        turno_stmt = select(Turno).where(
            Turno.odontologo_id == t_spec["odontologo_id"],
            Turno.inicio == t_spec["inicio"],
            Turno.fin == t_spec["fin"],
        )
        if await session.scalar(turno_stmt) is None:
            session.add(
                Turno(
                    paciente_id=t_spec["paciente_id"],
                    odontologo_id=t_spec["odontologo_id"],
                    inicio=t_spec["inicio"],
                    fin=t_spec["fin"],
                    motivo=t_spec["motivo"],
                    estado=t_spec["estado"],
                    origen=t_spec["origen"],
                )
            )

    await session.commit()

    # Query current row counts
    count_users = len(list((await session.scalars(select(Usuario.id))).all()))
    count_templates = len(list((await session.scalars(select(PlantillaDisponibilidad.id))).all()))
    count_turnos = len(list((await session.scalars(select(Turno.id))).all()))

    return {
        "usuarios": count_users,
        "plantillas": count_templates,
        "turnos": count_turnos,
    }
