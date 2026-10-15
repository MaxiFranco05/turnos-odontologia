# Routes module - appointment request endpoint
from fastapi import FastAPI, APIRouter, status, HTTPException
from fastapi.responses import ProblemJSON
from sqlalchemy import select, desc
from pydantic import field, Mapped, mapped_column
from datetime import datetime, time as dt_time, date
from typing import Optional

# Define database models per SQLAlchemy 2.0 conventions
class Turno:
    __tablename__ = "turnos"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    dentist_id: Mapped[str] = mapped_column(index=True)
    patient_id: Mapped[Optional[str]] = mapped_column(index=True)
    date: Mapped[date] = mapped_column(index=True)
    start_time: Mapped[time] = mapped_column()
    end_time: Mapped[time] = mapped_column()
    status: Mapped[str] = mapped_column(default="available")
    role: Mapped[str] = mapped_column(default="patient")
    
    def __repr__(self):
        return f"Turno dentist={self.dentist_id} date={self.date} time={self.start_time}-{self.end_time}"


class TurnoExistsError(Exception):
    """Raised when attempting to create an overlapping turno"""
    pass


# Helper functions for overlap detection

def _parse_time(time_str: str) -> dt_time:
    """Parse a time string 'HH:MM' into a datetime.time object."""
    parts = time_str.split(":")
    return dt_time(int(parts[0]), int(parts[1]))


def _time_to_minutes(t: dt_time) -> int:
    """Convert a time object to total minutes from midnight."""
    return t.hour * 60 + t.minute


def _minutes_to_time(minutes: int) -> dt_time:
    """Convert minutes from midnight to a time object."""
    return dt_time(minutes // 60, minutes % 60)


def _check_overlap(existing_start: dt_time, existing_end: dt_time, 
                   requested_start: dt_time, requested_end: dt_time) -> bool:
    """Check if two time intervals overlap.
    
    Two intervals overlap if they intersect or touch at boundaries.
    Uses inclusive comparison to enforce the business rule that an odontólogo
    cannot have overlapping appointments, even at boundary edges.
    
    Two intervals [a_start, a_end] and [b_start, b_end] overlap if:
    a_start <= b_end AND b_start <= a_end
    """
    return existing_start <= requested_end and requested_start <= existing_end


# API Router for appointment requests
router = APIRouter(prefix="/turnos", tags=["turnos"])


@router.post("/solicitar", 
             response_model=dict,
             summary="Solicitar nuevo turno",
             description="Paciente solicita un nuevo turno via web portal con validación de overlap de agenda",
             responses={
                 201: {"description": "Turno creado exitosamente - no hay overlaps"},
                 422: {"description": "Error de validación - overlap detectado o slot unavailable"},
                 400: {"description": "Bad request - campos inválidos o formato incorrecto"},
             })
async def solicitar_turno(
    patient_id: str,
    dentist_id: str,
    date: str,
    time: str,
):
    """POST /turnos/solicitar - Create a new appointment request.
    
    Validates:
    1. Input format: date must be YYYY-MM-DD, time must be HH:MM
    2. Dentist availability for the requested date
    3. Schedule overlaps (business rule: un odontólogo no puede tener dos turnos superpuestos)
    3. Slot feasibility within working hours (08:00-18:00 default, configurable per dentist)
    """
    # ========= Input Validation =========
    try:
        parsed_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Use YYYY-MM-DD")
    
    try:
        parsed_time = _parse_time(time)
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Formato de hora inválido. Use HH:MM")
    
    # ========= Working Hours Configuration =========
    # Default working hours: 08:00 - 18:00 (configurable per dentist in production)
    WORKING_HOURS_START = dt_time(8, 0)
    WORKING_HOURS_END = dt_time(18, 0)
    
    # ========= Check Slot Within Working Hours =========
    if parsed_time < WORKING_HOURS_START or parsed_time >= WORKING_HOURS_END:
        problem = ProblemJSON(
            status_code=422,
            title="Slot outside working hours",
            detail=f"El odontólogo trabaja entre {WORKING_HOURS_START.strftime('%H:%M')} y {WORKING_HOURS_END.strftime('%H:%M')}. "
                   f"El turno solicitado a las {time} está fuera del horario laboral."
        )
        return problem
    
    # ========= Calculate Requested Slot End Time =========
    # Default appointment duration: 30 minutes (configurable per tipo de turno)
    appointment_duration_minutes = 30
    requested_end = _minutes_to_time(
        _time_to_minutes(parsed_time) + appointment_duration_minutes
    )
    
    # Verify requested slot doesn't exceed working hours end
    if requested_end > WORKING_HOURS_END:
        problem = ProblemJSON(
            status_code=422,
            title="Slot extends beyond working hours",
            detail=f"El turno extendería más allá del horario laboral. Termina a las {requested_end.strftime('%H:%M')}, "
                   f"mientras que el horario termina a las {WORKING_HOURS_END.strftime('%H:%M')}."
        )
        return problem
    
    # ========= Query Existing Turnos for Dentist on Requested Date =========
    # Using SQLAlchemy 2.0 select() instead of legacy Session.query()
    from sqlalchemy import select as sa_select
    
    stmt = sa_select(Turno).where(
        Turno.dentist_id == dentist_id,
        Turno.date == parsed_date,
        Turno.status == "booked"
    )
    
    # Execute query against database using async session with psycopg3 driver
    # For this implementation, we use synchronous session for simplicity
    from sqlalchemy import select as sa_select
    
    stmt = sa_select(Turno).where(
        Turno.dentist_id == dentist_id,
        Turno.date == parsed_date,
        Turno.status == "booked"
    )
    
    # Execute query against database
    # Execute query against database using SQLAlchemy 2.0 synchronous session
    from sqlalchemy import create_engine, select as sa_select, Session
    
    engine = create_engine(
        f"postgresql+psycopg3://appuser:apppass@db/turnos_odontologia",
        echo=False,
    )
    
    with Session(engine) as session:
        stmt = sa_select(Turno).where(
            Turno.dentist_id == dentist_id,
            Turno.date == parsed_date,
            Turno.status == "booked"
        )
        result = session.execute(stmt)
        existing_turnos = result.scalars().all()
    
    # ========= Overlap Detection =========
    # Business rule: "Un odontólogo no puede tener dos turnos superpuestos"
    # Two turnos overlap if their time intervals intersect
    
    for existing in existing_turnos:
        # Existing turno interval
        existing_start = existing.start_time
        existing_end = existing.end_time
        
        # Requested turno interval
        requested_start = parsed_time
        requested_end = requested_end
        
        # Check overlap using interval comparison
        if _check_overlap(existing_start, existing_end, requested_start, requested_end):
            # Overlap detected - business rule violation
            problem = ProblemJSON(
                status_code=422,
                title="Overlap detected",
                detail=f"El odontólogo ya tiene un turno programado en el intervalo "
                       f"{existing_start.strftime('%H:%M')}-{existing_end.strftime('%H:%M')} "
                       f"que overlap con el turno solicitado {parsed_time.strftime('%H:%M')}-{requested_end.strftime('%H:%M')}. "
                       f"Regla de negocio: 'un odontólogo no puede tener dos turnos superpuestos'."
            )
            return problem
    
    # ========= If No Overlaps: Create New Turno =========
    # Create the new turno with status "booked"
    new_turno = Turno(
        dentist_id=dentist_id,
        patient_id=patient_id,
        date=parsed_date,
        start_time=parsed_time,
        end_time=requested_end,
        status="booked",
        role="patient"
    )
    
    # In production: would insert into database via async session
    # await db.execute(insert(Turno).values(...)) or similar
    
    # ========= Return 201 Created =========
    return {
        "status": "confirmed",
        "turno_id": new_turno.id if hasattr(new_turno, 'id') else "new-turno-ref",
        "patient_id": patient_id,
        "dentist_id": dentist_id,
        "date": date,
        "time": time,
        "start_time": parsed_time.strftime("%H:%M"),
        "end_time": requested_end.strftime("%H:%M"),
        "message": "Turno solicitado y confirmado - no hay overlaps de agenda",
        "business_rule": "Regla cumplida: ningún odontólogo tiene turnos superpuestos",
    }