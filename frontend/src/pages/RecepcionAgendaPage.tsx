import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  XCircle,
  Filter,
  RotateCcw,
  UserCheck,
  Clock,
  Globe,
  Building2,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import {
  useAgendaDiaQuery,
  useUpdateTurnoEstadoMutation,
} from '@/hooks/useReceptionAgenda';
import {
  extractApiErrorMessage,
  formatLocalDateISO,
  formatTimeFromISO,
} from '@/services/reception.service';
import {
  ESTADO_TURNO_LABELS,
  ORIGEN_TURNO_LABELS,
  type AgendaTurnoDiaItem,
  type EstadoTurno,
  type EstadoTurnoRecepcionTransicion,
  type ParticipanteOdontologoResumen,
} from '@/types/reception';

export interface RecepcionAgendaPageProps {
  initialFecha?: string;
  initialOdontologoId?: number;
}

export const RecepcionAgendaPage: React.FC<RecepcionAgendaPageProps> = ({
  initialFecha,
  initialOdontologoId,
}) => {
  const [fecha, setFecha] = useState<string>(() => initialFecha || formatLocalDateISO());
  const [odontologoIdInput, setOdontologoIdInput] = useState<string>(
    initialOdontologoId !== undefined ? String(initialOdontologoId) : ''
  );
  const [estadoFilter, setEstadoFilter] = useState<EstadoTurno | 'todos'>('todos');
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [mutationSuccess, setMutationSuccess] = useState<string | null>(null);
  const [activeTurnoId, setActiveTurnoId] = useState<number | null>(null);

  const parsedOdontologoId = useMemo<number | undefined>(() => {
    const trimmed = odontologoIdInput.trim();
    if (!trimmed) return undefined;
    const num = Number(trimmed);
    return Number.isInteger(num) && num > 0 ? num : undefined;
  }, [odontologoIdInput]);

  const agendaQuery = useAgendaDiaQuery({
    fecha,
    odontologoId: parsedOdontologoId,
  });

  const updateEstadoMutation = useUpdateTurnoEstadoMutation();

  const items: AgendaTurnoDiaItem[] = agendaQuery.data ?? [];

  const knownDentists = useMemo<ParticipanteOdontologoResumen[]>(() => {
    const map = new Map<number, ParticipanteOdontologoResumen>();
    for (const item of items) {
      if (item.odontologo && !map.has(item.odontologo.id)) {
        map.set(item.odontologo.id, item.odontologo);
      }
    }
    return Array.from(map.values());
  }, [items]);

  const filteredItems = useMemo<AgendaTurnoDiaItem[]>(() => {
    if (estadoFilter === 'todos') return items;
    return items.filter((item) => item.estado === estadoFilter);
  }, [items, estadoFilter]);

  const stats = useMemo(() => {
    let solicitados = 0;
    let confirmados = 0;
    let canceladosOAnulados = 0;
    for (const item of items) {
      if (item.estado === 'solicitado') solicitados += 1;
      else if (item.estado === 'confirmado') confirmados += 1;
      else if (item.estado === 'cancelado' || item.estado === 'anulado') {
        canceladosOAnulados += 1;
      }
    }
    return {
      total: items.length,
      solicitados,
      confirmados,
      canceladosOAnulados,
    };
  }, [items]);

  const handleTransition = (
    turnoId: number,
    nuevoEstado: EstadoTurnoRecepcionTransicion,
    pacienteNombre: string
  ): void => {
    setMutationError(null);
    setMutationSuccess(null);
    setActiveTurnoId(turnoId);

    updateEstadoMutation.mutate(
      { turnoId, estado: nuevoEstado },
      {
        onSuccess: () => {
          setActiveTurnoId(null);
          const accionLabel = nuevoEstado === 'confirmado' ? 'confirmado' : 'anulado';
          setMutationSuccess(`Turno de ${pacienteNombre} ${accionLabel} correctamente.`);
        },
        onError: (err: unknown) => {
          setActiveTurnoId(null);
          const message = extractApiErrorMessage(
            err,
            'No se pudo actualizar el estado del turno.'
          );
          setMutationError(message);
        },
      }
    );
  };

  const handleResetFilters = (): void => {
    setOdontologoIdInput('');
    setEstadoFilter('todos');
    setMutationError(null);
  };

  const queryErrorMessage = agendaQuery.isError
    ? extractApiErrorMessage(
        agendaQuery.error,
        'No se pudo cargar la agenda del día seleccionado.'
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Encabezado clínico */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Agenda del Día (Recepción)
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Consultá los turnos programados del consultorio, confirmá solicitudes pendientes o
            anulá turnos con al menos 24 horas de anticipación.
          </p>
        </div>
      </div>

      {/* Tarjetas de resumen operativo */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Total del día
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="border-amber-200 dark:border-amber-800/50 bg-amber-50/50 dark:bg-amber-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-amber-800 dark:text-amber-400">
              Pendientes (Solicitados)
            </p>
            <p className="mt-1 text-2xl font-bold text-amber-900 dark:text-amber-200">{stats.solicitados}</p>
          </CardContent>
        </Card>
        <Card className="border-emerald-200 dark:border-emerald-800/50 bg-emerald-50/50 dark:bg-emerald-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-emerald-800 dark:text-emerald-400">
              Confirmados
            </p>
            <p className="mt-1 text-2xl font-bold text-emerald-900 dark:text-emerald-200">{stats.confirmados}</p>
          </CardContent>
        </Card>
        <Card className="border-rose-200 dark:border-rose-800/50 bg-rose-50/50 dark:bg-rose-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-rose-800 dark:text-rose-400">
              Cancelados / Anulados
            </p>
            <p className="mt-1 text-2xl font-bold text-rose-900 dark:text-rose-200">{stats.canceladosOAnulados}</p>
          </CardContent>
        </Card>
      </div>

      {/* Barra de filtros */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4 text-primary" />
            <span>Filtros de Agenda</span>
          </CardTitle>
          <CardDescription>
            Seleccioná la fecha operativa y filtrá opcionalmente por odontólogo o estado del turno.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4 md:items-end">
            <div>
              <Input
                id="agenda-fecha"
                label="Fecha de agenda"
                type="date"
                value={fecha}
                onChange={(e) => {
                  setFecha(e.target.value);
                  setMutationError(null);
                }}
              />
            </div>

            <div>
              <Input
                id="agenda-odontologo-id"
                label="Filtrar por ID de odontólogo"
                type="number"
                min={1}
                placeholder="Todos los odontólogos"
                value={odontologoIdInput}
                onChange={(e) => {
                  setOdontologoIdInput(e.target.value);
                  setMutationError(null);
                }}
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label
                htmlFor="agenda-estado-filter"
                className="block text-sm font-medium leading-none text-slate-700"
              >
                Estado del turno
              </label>
              <select
                id="agenda-estado-filter"
                value={estadoFilter}
                onChange={(e) => setEstadoFilter(e.target.value as EstadoTurno | 'todos')}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="todos">Todos los estados</option>
                <option value="solicitado">Solicitado</option>
                <option value="confirmado">Confirmado</option>
                <option value="cancelado">Cancelado (Paciente)</option>
                <option value="anulado">Anulado (Recepción)</option>
                <option value="presente">Presente</option>
                <option value="ausente">Ausente</option>
              </select>
            </div>

            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleResetFilters}
                className="w-full md:w-auto"
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                <span>Limpiar filtro</span>
              </Button>
            </div>
          </div>

          {knownDentists.length > 0 && (
            <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-3">
              <span className="text-xs font-medium text-muted-foreground">
                Odontólogos en esta fecha:
              </span>
              <button
                type="button"
                onClick={() => setOdontologoIdInput('')}
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                  parsedOdontologoId === undefined
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-slate-100 dark:bg-neutral-800 text-slate-700 dark:text-neutral-200 hover:bg-slate-200 dark:hover:bg-neutral-700'
                }`}
              >
                Todos
              </button>
              {knownDentists.map((dentist) => (
                <button
                  key={dentist.id}
                  type="button"
                  onClick={() => setOdontologoIdInput(String(dentist.id))}
                  className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                    parsedOdontologoId === dentist.id
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-slate-100 dark:bg-neutral-800 text-slate-700 dark:text-neutral-200 hover:bg-slate-200 dark:hover:bg-neutral-700'
                  }`}
                >
                  {dentist.nombre} (#{dentist.id})
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Alertas de error o éxito */}
      {(queryErrorMessage || mutationError) && (
        <Alert variant="destructive">
          <AlertTitle>Atención</AlertTitle>
          <AlertDescription>{mutationError || queryErrorMessage}</AlertDescription>
        </Alert>
      )}

      {mutationSuccess && !mutationError && (
        <Alert variant="success" role="status">
          <AlertDescription>{mutationSuccess}</AlertDescription>
        </Alert>
      )}

      {/* Tabla / Listado de Turnos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Turnos del {fecha}</span>
            </span>
            <span className="text-xs font-normal text-slate-500">
              Mostrando {filteredItems.length} de {items.length} turnos
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {agendaQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-slate-500">
              Cargando agenda clínica del día...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                No hay turnos registrados para los filtros seleccionados.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Probá seleccionando otra fecha o restableciendo el filtro de odontólogo.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <th className="py-3 pr-4">Horario</th>
                    <th className="px-4 py-3">Paciente</th>
                    <th className="px-4 py-3">Odontólogo</th>
                    <th className="px-4 py-3">Motivo / Prestación</th>
                    <th className="px-4 py-3">Origen</th>
                    <th className="px-4 py-3">Estado</th>
                    <th className="py-3 pl-4 text-right">Acciones</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredItems.map((turno) => {
                    const canConfirm = turno.estado === 'solicitado';
                    const canAnnul =
                      turno.estado === 'solicitado' || turno.estado === 'confirmado';
                    const isRowMutating =
                      updateEstadoMutation.isPending && activeTurnoId === turno.id;

                    return (
                      <tr
                        key={turno.id}
                        data-testid={`agenda-row-${turno.id}`}
                        className="transition-colors hover:bg-slate-100/60 dark:hover:bg-neutral-800/60"
                      >
                        <td className="whitespace-nowrap py-3.5 pr-4 font-medium text-foreground">
                          {formatTimeFromISO(turno.inicio)} – {formatTimeFromISO(turno.fin)}
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="font-medium text-foreground">
                            {turno.paciente.nombre}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            {turno.paciente.nro_socio
                              ? `Socio: ${turno.paciente.nro_socio}`
                              : 'Sin N.º socio'}
                            {turno.paciente.email ? ` · ${turno.paciente.email}` : ''}
                          </div>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1.5 font-medium text-foreground">
                            <UserCheck className="h-3.5 w-3.5 text-muted-foreground" />
                            <span>{turno.odontologo.nombre}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">ID #{turno.odontologo.id}</div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-700 dark:text-neutral-300">{turno.motivo}</td>
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
                          {canConfirm || canAnnul ? (
                            <div className="flex items-center justify-end gap-2">
                              {canConfirm && (
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="default"
                                  loading={isRowMutating}
                                  disabled={updateEstadoMutation.isPending}
                                  onClick={() =>
                                    handleTransition(
                                      turno.id,
                                      'confirmado',
                                      turno.paciente.nombre
                                    )
                                  }
                                >
                                  <CheckCircle2 className="mr-1 h-3.5 w-3.5" />
                                  <span>Confirmar</span>
                                </Button>
                              )}
                              {canAnnul && (
                                <Button
                                  type="button"
                                  size="sm"
                                  variant="destructive"
                                  loading={isRowMutating}
                                  disabled={updateEstadoMutation.isPending}
                                  onClick={() =>
                                    handleTransition(
                                      turno.id,
                                      'anulado',
                                      turno.paciente.nombre
                                    )
                                  }
                                >
                                  <XCircle className="mr-1 h-3.5 w-3.5" />
                                  <span>Anular</span>
                                </Button>
                              )}
                            </div>
                          ) : (
                            <span className="text-xs italic text-slate-400">
                              Sin acciones disponibles
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

export default RecepcionAgendaPage;
