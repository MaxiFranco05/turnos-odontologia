import React, { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock,
  Filter,
  RotateCcw,
  User,
  XCircle,
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
  useDentistCalendarQuery,
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
  CalendarioDiaResumen,
  MisTurnosOdontologoItem,
  TurnoAsistenciaEstado,
} from '@/types/dentist';
import { cn } from '@/lib/utils';

export interface OdontologoAgendaPageProps {
  initialFecha?: string;
  initialVista?: 'agenda' | 'calendario';
}

export const OdontologoAgendaPage: React.FC<OdontologoAgendaPageProps> = ({
  initialFecha,
  initialVista = 'agenda',
}) => {
  const auth = useOptionalAuth();
  const user = auth?.user ?? null;
  const location = useLocation();

  const [fecha, setFecha] = useState<string>(
    () => initialFecha || formatLocalDateISO()
  );

  const activeVista: 'agenda' | 'calendario' = useMemo(() => {
    if (location?.pathname?.includes('/calendario')) return 'calendario';
    if (location?.pathname?.includes('/agenda')) return 'agenda';
    return initialVista;
  }, [location?.pathname, initialVista]);

  const [viewMode, setViewMode] = useState<'agenda' | 'calendario'>(activeVista);

  useEffect(() => {
    setViewMode(activeVista);
  }, [activeVista]);

  // Month navigation for Calendar view
  const [calendarMonth, setCalendarMonth] = useState<Date>(() => {
    const parts = (initialFecha || formatLocalDateISO()).split('-');
    const y = Number(parts[0]) || 2026;
    const m = (Number(parts[1]) || 11) - 1;
    return new Date(y, m, 1);
  });

  const monthData = useMemo(() => {
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    const monthName = calendarMonth.toLocaleString('es-ES', {
      month: 'long',
      year: 'numeric',
    });
    const capitalizedMonthName =
      monthName.charAt(0).toUpperCase() + monthName.slice(1);

    const daysInMonth = new Date(year, month + 1, 0).getDate();
    // Monday as 0, Sunday as 6
    const firstDayIndex = (new Date(year, month, 1).getDay() + 6) % 7;

    const days: Array<{
      dayNumber: number;
      dateStr: string;
      isToday: boolean;
      isSelected: boolean;
    }> = [];
    const todayStr = formatLocalDateISO();

    for (let d = 1; d <= daysInMonth; d++) {
      const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
      days.push({
        dayNumber: d,
        dateStr,
        isToday: dateStr === todayStr,
        isSelected: dateStr === fecha,
      });
    }

    return {
      title: capitalizedMonthName,
      firstDayOffset: firstDayIndex,
      days,
    };
  }, [calendarMonth, fecha]);

  const handlePrevMonth = () => {
    setCalendarMonth(
      (prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1)
    );
  };

  const handleNextMonth = () => {
    setCalendarMonth(
      (prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1)
    );
  };

  const handleTodayClick = () => {
    const today = formatLocalDateISO();
    setFecha(today);
    setCalendarMonth(new Date());
  };
  const [estadoFilter, setEstadoFilter] = useState<EstadoTurno | 'todos'>(
    'todos'
  );
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [mutationSuccess, setMutationSuccess] = useState<string | null>(null);
  const [activeTurnoId, setActiveTurnoId] = useState<number | null>(null);

  const agendaQuery = useDentistAgendaQuery(fecha);
  const activeYear = calendarMonth.getFullYear();
  const activeMonth = calendarMonth.getMonth() + 1;
  const calendarQuery = useDentistCalendarQuery(activeYear, activeMonth);
  const updateAsistenciaMutation = useUpdateAsistenciaMutation();

  const calendarSummaryByDate = useMemo<Record<string, CalendarioDiaResumen>>(() => {
    const map: Record<string, CalendarioDiaResumen> = {};
    for (const item of calendarQuery.data?.dias ?? []) {
      map[item.fecha] = item;
    }
    return map;
  }, [calendarQuery.data]);

  const items: MisTurnosOdontologoItem[] = agendaQuery.data ?? [];

  const filteredItems = useMemo<MisTurnosOdontologoItem[]>(() => {
    if (estadoFilter === 'todos') return items;
    return items.filter((item) => item.estado === estadoFilter);
  }, [items, estadoFilter]);

  const confirmadosDelDia = useMemo(() => {
    return items.filter((item) => item.estado === 'confirmado');
  }, [items]);

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
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          {viewMode === 'agenda'
            ? 'Mi Agenda del Día (Odontólogo)'
            : 'Calendario de Turnos Confirmados'}
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {user?.nombre ? `Profesional: ${user.nombre}. ` : ''}
          {viewMode === 'agenda'
            ? 'Consultá tus turnos programados del día y registrá la asistencia real (Presente / Ausente) sobre los turnos confirmados.'
            : 'Visualizá los turnos confirmados por Recepción organizados en el calendario mensual.'}
        </p>
      </div>

      {viewMode === 'agenda' ? (
        <>
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
    </>
  ) : (
    <div className="space-y-6">
      {/* Card del Calendario Mensual Interactivo */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Navegación Mensual</span>
            </CardTitle>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground px-2">
                {monthData.title}
              </span>
              <div className="flex items-center border border-border rounded-lg overflow-hidden">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handlePrevMonth}
                  className="h-8 w-8 p-0 rounded-none border-r border-border"
                  aria-label="Mes anterior"
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={handleNextMonth}
                  className="h-8 w-8 p-0 rounded-none"
                  aria-label="Mes siguiente"
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleTodayClick}
                className="h-8 text-xs"
              >
                Hoy
              </Button>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pt-1">
            <CardDescription>
              Hacé clic en cualquier día para consultar los turnos confirmados por Recepción.
            </CardDescription>
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" aria-hidden="true" />
                Confirmados
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-400" aria-hidden="true" />
                Pend. recepción
              </span>
              <span className="inline-flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-sky-400" aria-hidden="true" />
                Atendidos
              </span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Grilla de Días de la Semana */}
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-semibold text-muted-foreground pb-2 border-b border-border">
            <span>Lun</span>
            <span>Mar</span>
            <span>Mié</span>
            <span>Jue</span>
            <span>Vie</span>
            <span>Sáb</span>
            <span>Dom</span>
          </div>

          {/* Grilla de Días del Mes */}
          <div className="grid grid-cols-7 gap-1 pt-2">
            {/* Días vacíos previos al día 1 */}
            {Array.from({ length: monthData.firstDayOffset }).map((_, i) => (
              <div key={`empty-${i}`} className="h-10 sm:h-12" />
            ))}

            {/* Días del mes */}
            {monthData.days.map((day) => {
              const summary = calendarSummaryByDate[day.dateStr];
              const tooltipParts: string[] = [];
              if (summary?.confirmados) {
                tooltipParts.push(`${summary.confirmados} confirmado(s)`);
              }
              if (summary?.solicitados) {
                tooltipParts.push(`${summary.solicitados} pendiente(s) de recepción`);
              }
              if (summary?.atendidos) {
                tooltipParts.push(`${summary.atendidos} atendido(s)`);
              }
              const dayAriaLabel =
                tooltipParts.length > 0
                  ? `${day.dateStr}: ${tooltipParts.join(', ')}`
                  : day.dateStr;

              return (
                <button
                  key={day.dateStr}
                  type="button"
                  onClick={() => setFecha(day.dateStr)}
                  aria-label={dayAriaLabel}
                  title={tooltipParts.length > 0 ? tooltipParts.join(' · ') : undefined}
                  className={cn(
                    'flex flex-col items-center justify-center h-10 sm:h-12 rounded-xl text-xs sm:text-sm transition-all duration-150',
                    day.isSelected
                      ? 'bg-primary text-primary-foreground font-bold shadow-md shadow-primary/30 scale-[1.02]'
                      : day.isToday
                      ? 'border border-primary text-primary font-bold hover:bg-primary/10'
                      : 'text-foreground hover:bg-muted'
                  )}
                >
                  <span>{day.dayNumber}</span>
                  {summary && (
                    <span className="flex items-center justify-center gap-1 mt-0.5">
                      {summary.confirmados > 0 && (
                        <span
                          data-testid={`calendar-dot-confirmados-${day.dateStr}`}
                          className={cn(
                            'w-1.5 h-1.5 rounded-full',
                            day.isSelected ? 'bg-white' : 'bg-emerald-400'
                          )}
                        />
                      )}
                      {summary.solicitados > 0 && (
                        <span
                          data-testid={`calendar-dot-solicitados-${day.dateStr}`}
                          className="w-1.5 h-1.5 rounded-full bg-amber-400"
                        />
                      )}
                      {summary.atendidos > 0 &&
                        summary.confirmados === 0 &&
                        summary.solicitados === 0 && (
                          <span
                            data-testid={`calendar-dot-atendidos-${day.dateStr}`}
                            className={cn(
                              'w-1.5 h-1.5 rounded-full',
                              day.isSelected ? 'bg-white/80' : 'bg-sky-400'
                            )}
                          />
                        )}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Listado de Pacientes Confirmados para la Fecha Seleccionada */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              <span>Turnos Confirmados por Recepción ({fecha})</span>
            </CardTitle>
            <Badge
              variant="outline"
              className="border-emerald-500/30 text-emerald-600 dark:text-emerald-400 w-fit"
            >
              {confirmadosDelDia.length} paciente(s) confirmado(s)
            </Badge>
          </div>
          <CardDescription>
            Pacientes confirmados por Recepción listos para atención clínica.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {agendaQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              Consultando turnos confirmados...
            </div>
          ) : confirmadosDelDia.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                No hay turnos confirmados por Recepción para el {fecha}.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Los turnos pendientes de confirmación o días sin citas no aparecen en este listado.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {confirmadosDelDia.map((turno) => {
                const isRowMutating =
                  updateAsistenciaMutation.isPending &&
                  activeTurnoId === turno.id;

                return (
                  <div
                    key={turno.id}
                    data-testid={`confirmed-card-${turno.id}`}
                    className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex flex-col justify-between gap-3 transition-all hover:border-emerald-500/40"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-base font-bold text-foreground">
                          {formatTimeFromISO(turno.inicio)} –{' '}
                          {formatTimeFromISO(turno.fin)}
                        </span>
                        <Badge
                          variant="outline"
                          className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-xs"
                        >
                          Confirmado por Recepción
                        </Badge>
                      </div>

                      <div className="mt-2.5 flex items-start gap-2.5">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary font-bold text-xs mt-0.5">
                          <User className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-foreground text-sm">
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
                        </div>
                      </div>

                      <p className="mt-2.5 text-xs text-muted-foreground bg-muted/40 p-2 rounded-lg border border-border">
                        <strong className="text-foreground">Motivo:</strong>{' '}
                        {turno.motivo}
                      </p>
                    </div>

                    {/* Attendance Actions */}
                    <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
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
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )}
    </div>
  );
};

export default OdontologoAgendaPage;
