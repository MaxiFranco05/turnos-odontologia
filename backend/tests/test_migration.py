import os
import tempfile
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_and_downgrade():
    """Verifies that alembic upgrade head and downgrade cb3f1b606883 execute cleanly on real DB."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        sqlite_url = f"sqlite:///{tmp_path}"
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

        alembic_cfg = Config(alembic_ini_path)
        alembic_cfg.set_main_option("sqlalchemy.url", sqlite_url)

        # 1. Upgrade to head
        command.upgrade(alembic_cfg, "head")

        # 2. Inspect created tables
        engine = create_engine(sqlite_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        assert "usuarios" in tables
        assert "plantillas_disponibilidad" in tables
        assert "turnos" in tables

        # Inspect columns of usuarios
        user_cols = {col["name"] for col in inspector.get_columns("usuarios")}
        assert {"id", "nombre", "email", "nro_socio", "password_hash", "debe_cambiar_password", "perfil_completo", "rol"}.issubset(user_cols)

        # Inspect check constraints of plantillas_disponibilidad
        plantilla_cols = {col["name"] for col in inspector.get_columns("plantillas_disponibilidad")}
        assert {"id", "odontologo_id", "dia_semana", "hora_inicio", "hora_fin", "duracion_slot_minutos"}.issubset(plantilla_cols)

        # Inspect indexes of turnos
        turno_indexes = {ix["name"] for ix in inspector.get_indexes("turnos")}
        assert "ix_turnos_odontologo_inicio" in turno_indexes
        assert "ix_turnos_paciente_inicio" in turno_indexes

        engine.dispose()

        # 3. Downgrade back to baseline
        command.downgrade(alembic_cfg, "cb3f1b606883")

        engine2 = create_engine(sqlite_url)
        inspector2 = inspect(engine2)
        tables_after_downgrade = inspector2.get_table_names()
        assert "usuarios" not in tables_after_downgrade
        assert "plantillas_disponibilidad" not in tables_after_downgrade
        assert "turnos" not in tables_after_downgrade
        engine2.dispose()

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
