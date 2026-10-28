"""create_core_tables

Revision ID: 002_create_core_tables
Revises: cb3f1b606883
Create Date: 2026-10-27 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_create_core_tables'
down_revision: Union[str, Sequence[str], None] = 'cb3f1b606883'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Table: usuarios
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(length=120), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('nro_socio', sa.String(length=50), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('debe_cambiar_password', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('perfil_completo', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('rol', sa.String(length=20), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('(email IS NOT NULL) OR (nro_socio IS NOT NULL)', name='ck_usuario_identificador_presente'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_usuarios_email'),
        sa.UniqueConstraint('nro_socio', name='uq_usuarios_nro_socio'),
    )
    op.create_index('ix_usuarios_email', 'usuarios', ['email'], unique=True)
    op.create_index('ix_usuarios_nro_socio', 'usuarios', ['nro_socio'], unique=True)

    # 2. Table: plantillas_disponibilidad
    op.create_table(
        'plantillas_disponibilidad',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('odontologo_id', sa.Integer(), nullable=False),
        sa.Column('dia_semana', sa.SmallInteger(), nullable=False),
        sa.Column('hora_inicio', sa.Time(), nullable=False),
        sa.Column('hora_fin', sa.Time(), nullable=False),
        sa.Column('duracion_slot_minutos', sa.Integer(), nullable=False),
        sa.Column('prestacion', sa.String(length=200), nullable=True),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('hora_fin > hora_inicio', name='ck_plantilla_horario_valido'),
        sa.CheckConstraint('duracion_slot_minutos > 0', name='ck_plantilla_duracion_positiva'),
        sa.CheckConstraint('dia_semana >= 0 AND dia_semana <= 6', name='ck_plantilla_dia_semana_valido'),
        sa.ForeignKeyConstraint(['odontologo_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_plantillas_disponibilidad_odontologo_id', 'plantillas_disponibilidad', ['odontologo_id'], unique=False)
    op.create_index('ix_plantillas_odontologo_dia', 'plantillas_disponibilidad', ['odontologo_id', 'dia_semana'], unique=False)

    # 3. Table: turnos
    op.create_table(
        'turnos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('odontologo_id', sa.Integer(), nullable=False),
        sa.Column('inicio', sa.DateTime(timezone=True), nullable=False),
        sa.Column('fin', sa.DateTime(timezone=True), nullable=False),
        sa.Column('motivo', sa.String(length=255), nullable=False),
        sa.Column('estado', sa.String(length=20), server_default='solicitado', nullable=False),
        sa.Column('origen', sa.String(length=20), server_default='online', nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('fin > inicio', name='ck_turno_fin_mayor_inicio'),
        sa.ForeignKeyConstraint(['odontologo_id'], ['usuarios.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['paciente_id'], ['usuarios.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_turnos_odontologo_id', 'turnos', ['odontologo_id'], unique=False)
    op.create_index('ix_turnos_paciente_id', 'turnos', ['paciente_id'], unique=False)
    op.create_index('ix_turnos_odontologo_inicio', 'turnos', ['odontologo_id', 'inicio'], unique=False)
    op.create_index('ix_turnos_paciente_inicio', 'turnos', ['paciente_id', 'inicio'], unique=False)

    # 4. Anti-overlap invariant enforcement
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
        op.execute("""
            ALTER TABLE turnos
            ADD CONSTRAINT excl_turno_odontologo_no_overlap
            EXCLUDE USING gist (
                odontologo_id WITH =,
                tstzrange(inicio, fin, '[)') WITH &&
            )
            WHERE (estado NOT IN ('cancelado', 'anulado'));
        """)
    elif bind.dialect.name == "sqlite":
        op.execute("""
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
        op.execute("""
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


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TABLE turnos DROP CONSTRAINT IF EXISTS excl_turno_odontologo_no_overlap;")
    elif bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_prevent_turno_overlap_update;")
        op.execute("DROP TRIGGER IF EXISTS trg_prevent_turno_overlap_insert;")

    op.drop_index('ix_turnos_paciente_inicio', table_name='turnos')
    op.drop_index('ix_turnos_odontologo_inicio', table_name='turnos')
    op.drop_index('ix_turnos_paciente_id', table_name='turnos')
    op.drop_index('ix_turnos_odontologo_id', table_name='turnos')
    op.drop_table('turnos')

    op.drop_index('ix_plantillas_odontologo_dia', table_name='plantillas_disponibilidad')
    op.drop_index('ix_plantillas_disponibilidad_odontologo_id', table_name='plantillas_disponibilidad')
    op.drop_table('plantillas_disponibilidad')

    op.drop_index('ix_usuarios_nro_socio', table_name='usuarios')
    op.drop_index('ix_usuarios_email', table_name='usuarios')
    op.drop_table('usuarios')
