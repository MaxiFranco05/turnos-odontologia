import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  XCircle,
  Filter,
  RotateCcw,
  Clock,
  Globe,
  Building2,
} from 'lucide-react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import { useOptionalAuth } from '@/context/AuthContext';
import {
  useDentistAgendaQuery,
  useUpdateAsistenciaMutation,
} from '@/hooks/useDentistAgenda';
import {
  extractApiErrorMessage,
  formatLocalDateISO,
  formatTimeFromISO,
} from '@/services/reception.service';
import {
  ESTADO_TURNO_LABELS,
  ORIGEN_TURNO_LABELS,
  type EstadoTurno,
} from '@/types/reception';
import type {
  MisTurnosOdontologoItem,
  TurnoAsistenciaEstado,
} from '@/types/dentist';

export interface OdontologoAgendaPageProps {
  initialFecha?: string;
}

export const OdontologoAgendaPage: React.FC<OdontologoAgendaPageProps> = ({
  initialFecha,
}) => {
  const auth = useOptionalAuth();
  const user = auth?.user ?? null;

  const [fecha, setFecha] = useState<string>(
    () => initialFecha || formatLocalDateISO()
  );
  const [estadoFilter, setEstadoFilter] = useState<EstadoTurno | 'todos'>(
    'todos'
  );
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [mutationSuccess, setMutationSuccess] = useState<string | null>(null);
  const [activeTurnoId, setActiveTurnoId] = useState<number | null>(null);

  const agendaQuery = useDentistAgendaQuery(fecha);
  const updateAsistenciaMutation = useUpdateAsistenciaMutation();

  const items: MisTurnosOdontologoItem[] = agendaQuery.data ?? [];

  const filteredItems = useMemo<MisTurnosOdontologoItem[]>(() => {
    if (estadoFilter === 'todos') return items;
    return items.filter((item) => item.estado === estadoFilter);
  }, [items, estadoFilter]);

  const stats = useMemo(() => {
    let confirmados = 0;
    let presentes = 0;
    let ausentes = 0;
    for (const item of items) {
      if (item.estado === 'confirmado') confirmados += 1;
      else if (item.estado === 'presente') presentes += 1;
      else if (item.estado === 'ausente') ausentes += 1;
    }
    return {
      total: items.length,
      confirmados,
      presentes,
      ausentes,
    };
  }, [items]);

  const handleAsistencia = (
    turnoId: number,
    nuevoEstado: TurnoAsistenciaEstado,
    pacienteNombre: string
  ): void => {
    setMutationError(null);
    setMutationSuccess(null);
    setActiveTurnoId(turnoId);

    updateAsistenciaMutation.mutate(
      { turnoId, estado: nuevoEstado },
      {
        onSuccess: () => {
          setActiveTurnoId(null);
          setMutationSuccess(
            `Asistencia de ${pacienteNombre} registrada como ${nuevoEstado} correctamente.`
          );
        },
        onError: (err: unknown) => {
          setActiveTurnoId(null);
          const message = extractApiErrorMessage(
            err,
            'No se pudo registrar la asistencia del turno.'
          );
          setMutationError(message);
        },
      }
    );
  };

  const handleResetFilter = (): void => {
    setEstadoFilter('todos');
    setMutationError(null);
  };

  const queryErrorMessage = agendaQuery.isError
    ? extractApiErrorMessage(
        agendaQuery.error,
        'No se pudo consultar tu agenda del día seleccionado.'
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Encabezado del portal profesional */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Mi Agenda del Día (Odontólogo)
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {user?.nombre
              ? `Agenda clínica de ${user.nombre}. `
              : ''}
            Consultá tus turnos programados del día y registrá la asistencia real
            (Presente / Ausente) sobre los turnos confirmados.
          </p>
        </div>
      </div>

      {/* Tarjetas de resumen diario */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Total del día
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">
              {stats.total}
            </p>
          </CardContent>
        </Card>
        <Card className="border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-emerald-800 dark:text-emerald-400">
              Confirmados por atender
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-900 dark:text-emerald-200">
              {stats.confirmados}
            </p>
          </CardContent>
        </Card>
        <Card className="border-sky-200 dark:border-sky-800/50 bg-sky-50/50 dark:bg-sky-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-sky-800 dark:text-sky-400">
              Presentes
            </p>
            <p className="mt-1 text-2xl font-bold text-sky-900 dark:text-sky-200">
              {stats.presentes}
            </p>
          </CardContent>
        </Card>
        <Card className="border-rose-200 dark:border-rose-800/50 bg-rose-50/50 dark:bg-rose-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-rose-800 dark:text-rose-400">
              Ausentes
            </p>
            <p className="mt-1 text-2xl font-bold text-rose-900 dark:text-rose-200">
              {stats.ausentes}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Barra de filtros */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4 text-primary" />
            <span>Fecha y Estado</span>
          </CardTitle>
          <CardDescription>
            Seleccioná la fecha de atención para consultar tus turnos asignados.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end">
            <div>
              <Input
                id="dentist-agenda-fecha"
                label="Fecha de agenda"
                type="date"
                value={fecha}
                onChange={(e) => {
                  setFecha(e.target.value);
                  setMutationError(null);
                  setMutationSuccess(null);
                }}
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label
                htmlFor="dentist-agenda-estado-filter"
                className="block text-sm font-medium leading-none text-slate-700"
              >
                Filtrar por estado
              </label>
              <select
                id="dentist-agenda-estado-filter"
                value={estadoFilter}
                onChange={(e) =>
                  setEstadoFilter(e.target.value as EstadoTurno | 'todos')
                }
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="todos">Todos los estados</option>
                <option value="confirmado">Confirmado</option>
                <option value="presente">Presente</option>
                <option value="ausente">Ausente</option>
                <option value="solicitado">Solicitado</option>
                <option value="cancelado">Cancelado</option>
                <option value="anulado">Anulado</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleResetFilter}
                className="w-full md:w-auto"
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                <span>Ver todos</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alertas de error o éxito */}
      {(queryErrorMessage || mutationError) && (
        <Alert variant="destructive">
          <AlertTitle>Atención</AlertTitle>
          <AlertDescription>
            {mutationError || queryErrorMessage}
          </AlertDescription>
        </Alert>
      )}

      {mutationSuccess && !mutationError && (
        <Alert variant="success" role="status">
          <AlertDescription>{mutationSuccess}</AlertDescription>
        </Alert>
      )}

      {/* Tabla cronológica de turnos propios */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Mis Turnos del {fecha}</span>
            </span>
            <span className="text-xs font-normal text-slate-500">
              Mostrando {filteredItems.length} de {items.length} turnos
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agendaQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-slate-500">
              Cargando tu agenda del día...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                No tenés turnos programados para la fecha seleccionada.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Probá eligiendo otra fecha operativa o cambiando el filtro de
                estado.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <th className="py-3 pr-4">Horario</th>
                    <th className="px-4 py-3">Paciente</th>
                    <th className="px-4 py-3">Motivo / Prestación</th>
                    <th className="px-4 py-3">Origen</th>
                    <th className="px-4 py-3">Estado</th>
                    <th className="py-3 pl-4 text-right">
                      Asistencia (Presente / Ausente)
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredItems.map((turno) => {
                    const isConfirmado = turno.estado === 'confirmado';
                    const isRowMutating =
                      updateAsistenciaMutation.isPending &&
                      activeTurnoId === turno.id;

                    return (
                      <tr
                        key={turno.id}
                        data-testid={`dentist-agenda-row-${turno.id}`}
                        className="transition-colors hover:bg-slate-100/60 dark:hover:bg-neutral-800/60"
                      >
                        <td className="whitespace-nowrap py-3.5 pr-4 font-mono font-medium text-foreground">
                          {formatTimeFromISO(turno.inicio)} –{' '}
                          {formatTimeFromISO(turno.fin)}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-medium text-foreground">
                            {turno.paciente.nombre}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {turno.paciente.nro_socio
                              ? `Socio: ${turno.paciente.nro_socio}`
                              : 'Sin N.º socio'}
                            {turno.paciente.email
                              ? ` · ${turno.paciente.email}`
                              : ''}
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-700">
                          {turno.motivo}
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant="outline" className="gap-1 font-normal">
                            {turno.origen === 'online' ? (
                              <Globe className="h-3 w-3 text-sky-600" />
                            ) : (
                              <Building2 className="h-3 w-3 text-slate-500" />
                            )}
                            <span>{ORIGEN_TURNO_LABELS[turno.origen]}</span>
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          <Badge variant={turno.estado}>
                            {ESTADO_TURNO_LABELS[turno.estado]}
                          </Badge>
                        </td>
                        <td className="whitespace-nowrap py-3.5 pl-4 text-right">
                          {isConfirmado ? (
                            <div className="flex items-center justify-end gap-2">
                              <Button
                                type="button"
                                size="sm"
                                variant="default"
                                loading={isRowMutating}
                                disabled={updateAsistenciaMutation.isPending}
                                onClick={() =>
                                  handleAsistencia(
                                    turno.id,
                                    'presente',
                                    turno.paciente.nombre
                                  )
                                }
                              >
                                <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                                <span>Presente</span>
                              </Button>
                              <Button
                                type="button"
                                size="sm"
                                variant="destructive"
                                loading={isRowMutating}
                                disabled={updateAsistenciaMutation.isPending}
                                onClick={() =>
                                  handleAsistencia(
                                    turno.id,
                                    'ausente',
                                    turno.paciente.nombre
                                  )
                                }
                              >
                                <XCircle className="mr-1 h-3.5 w-3.5" />
                                <span>Ausente</span>
                              </Button>
                            </div>
                          ) : (
                            <span className="text-xs italic text-slate-400">
                              {turno.estado === 'presente' ||
                              turno.estado === 'ausente'
                                ? 'Asistencia registrada'
                                : 'Sin acciones disponibles'}
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default OdontologoAgendaPage;
