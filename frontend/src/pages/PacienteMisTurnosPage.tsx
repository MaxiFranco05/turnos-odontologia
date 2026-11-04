import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  Clock,
  Filter,
  RotateCcw,
  Stethoscope,
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
import {
  useMisTurnosPacienteQuery,
  useCancelarTurnoMutation,
} from '@/hooks/usePatientPortal';
import {
  extractApiErrorMessage,
  formatTimeFromISO,
} from '@/services/reception.service';
import {
  ESTADO_TURNO_LABELS,
  ORIGEN_TURNO_LABELS,
  type EstadoTurno,
} from '@/types/reception';
import type { MisTurnosPacienteItem } from '@/types/patient';

/**
 * Formats an ISO datetime into 'DD/MM/YYYY' for display.
 */
function formatDateDisplay(isoString: string): string {
  if (!isoString) return '';
  const dateMatch = isoString.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (dateMatch) {
    const [, y, m, d] = dateMatch;
    return `${d}/${m}/${y}`;
  }
  const date = new Date(isoString);
  if (Number.isNaN(date.getTime())) return isoString;
  const d = String(date.getDate()).padStart(2, '0');
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const y = date.getFullYear();
  return `${d}/${m}/${y}`;
}

export const PacienteMisTurnosPage: React.FC = () => {
  const [fechaDesde, setFechaDesde] = useState<string>('');
  const [fechaHasta, setFechaHasta] = useState<string>('');
  const [estadoFilter, setEstadoFilter] = useState<EstadoTurno | 'todos'>('todos');
  const [mutationSuccess, setMutationSuccess] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [activeTurnoId, setActiveTurnoId] = useState<number | null>(null);

  const misTurnosQuery = useMisTurnosPacienteQuery({
    fecha_desde: fechaDesde || undefined,
    fecha_hasta: fechaHasta || undefined,
  });

  const cancelarMutation = useCancelarTurnoMutation();

  const items: MisTurnosPacienteItem[] = misTurnosQuery.data ?? [];

  const filteredItems = useMemo<MisTurnosPacienteItem[]>(() => {
    if (estadoFilter === 'todos') return items;
    return items.filter((item) => item.estado === estadoFilter);
  }, [items, estadoFilter]);

  const stats = useMemo(() => {
    let pendientes = 0;
    let confirmados = 0;
    let cancelados = 0;
    for (const item of items) {
      if (item.estado === 'solicitado') pendientes += 1;
      else if (item.estado === 'confirmado') confirmados += 1;
      else if (item.estado === 'cancelado' || item.estado === 'anulado') {
        cancelados += 1;
      }
    }
    return {
      total: items.length,
      pendientes,
      confirmados,
      cancelados,
    };
  }, [items]);

  const handleCancelar = (turnoId: number): void => {
    setMutationError(null);
    setMutationSuccess(null);
    setActiveTurnoId(turnoId);

    cancelarMutation.mutate(turnoId, {
      onSuccess: () => {
        setActiveTurnoId(null);
        setMutationSuccess('Turno cancelado correctamente.');
      },
      onError: (err: unknown) => {
        setActiveTurnoId(null);
        const message = extractApiErrorMessage(
          err,
          'No se pudo cancelar el turno.'
        );
        setMutationError(message);
      },
    });
  };

  const handleResetFilters = (): void => {
    setFechaDesde('');
    setFechaHasta('');
    setEstadoFilter('todos');
    setMutationError(null);
    setMutationSuccess(null);
  };

  const queryErrorMessage = misTurnosQuery.isError
    ? extractApiErrorMessage(
        misTurnosQuery.error,
        'No se pudieron cargar tus turnos.'
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Encabezado clínico */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Mis Turnos Odontológicos
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Consultá tu historial de turnos y gestioná cancelaciones con al menos 24 horas de anticipación.
          </p>
        </div>
      </div>

      {/* Tarjetas de resumen */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="border-border bg-card">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Total de turnos
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">{stats.total}</p>
          </CardContent>
        </Card>
        <Card className="border-amber-200 dark:border-amber-800/50 bg-amber-50/50 dark:bg-amber-950/20">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-amber-800 dark:text-amber-400">
              Pendientes de confirmación
            </p>
            <p className="mt-1 text-2xl font-bold text-amber-900 dark:text-amber-200">{stats.pendientes}</p>
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
        <Card className="border-border bg-muted/30">
          <CardContent className="p-4 pt-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              Cancelados / Anulados
            </p>
            <p className="mt-1 text-2xl font-bold text-foreground">{stats.cancelados}</p>
          </CardContent>
        </Card>
      </div>

      {/* Filtros de búsqueda */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4 text-primary" />
            <span>Filtrar Mis Turnos</span>
          </CardTitle>
          <CardDescription>
            Filtrá por rango de fechas o por estado del turno.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4 md:items-end">
            <div>
              <Input
                id="mis-turnos-fecha-desde"
                label="Fecha desde"
                type="date"
                value={fechaDesde}
                onChange={(e) => setFechaDesde(e.target.value)}
              />
            </div>

            <div>
              <Input
                id="mis-turnos-fecha-hasta"
                label="Fecha hasta"
                type="date"
                value={fechaHasta}
                onChange={(e) => setFechaHasta(e.target.value)}
              />
            </div>

            <div className="space-y-1.5 text-left">
              <label
                htmlFor="mis-turnos-estado-filter"
                className="block text-sm font-medium leading-none text-slate-700"
              >
                Estado
              </label>
              <select
                id="mis-turnos-estado-filter"
                value={estadoFilter}
                onChange={(e) =>
                  setEstadoFilter(e.target.value as EstadoTurno | 'todos')
                }
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="todos">Todos los estados</option>
                <option value="solicitado">Solicitado</option>
                <option value="confirmado">Confirmado</option>
                <option value="presente">Presente</option>
                <option value="ausente">Ausente</option>
                <option value="cancelado">Cancelado</option>
                <option value="anulado">Anulado</option>
              </select>
            </div>

            <div>
              <Button
                type="button"
                variant="outline"
                onClick={handleResetFilters}
                className="w-full md:w-auto"
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                <span>Limpiar filtros</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Alertas */}
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

      {/* Listado de Turnos */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Mis Turnos</span>
            </span>
            <span className="text-xs font-normal text-slate-500">
              Mostrando {filteredItems.length} de {items.length} turnos
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {misTurnosQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-slate-500">
              Cargando tus turnos...
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                No tenés turnos registrados con los filtros seleccionados.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Podés solicitar uno nuevo desde la sección "Buscar turno".
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-sm">
                <thead>
                  <tr className="border-b border-border text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    <th className="py-3 pr-4">Fecha y Horario</th>
                    <th className="px-4 py-3">Odontólogo</th>
                    <th className="px-4 py-3">Motivo</th>
                    <th className="px-4 py-3">Origen</th>
                    <th className="px-4 py-3">Estado</th>
                    <th className="py-3 pl-4 text-right">Acción</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {filteredItems.map((turno) => {
                    const canCancel =
                      turno.estado === 'solicitado' ||
                      turno.estado === 'confirmado';
                    const isMutating =
                      cancelarMutation.isPending && activeTurnoId === turno.id;

                    return (
                      <tr
                        key={turno.id}
                        data-testid={`mis-turnos-row-${turno.id}`}
                        className="transition-colors hover:bg-slate-100/60 dark:hover:bg-neutral-800/60"
                      >
                        <td className="whitespace-nowrap py-3.5 pr-4 font-medium text-foreground">
                          <div>{formatDateDisplay(turno.inicio)}</div>
                          <div className="font-mono text-xs text-muted-foreground">
                            {formatTimeFromISO(turno.inicio)} –{' '}
                            {formatTimeFromISO(turno.fin)}
                          </div>
                        </td>
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-1.5 font-medium text-foreground">
                            <Stethoscope className="h-3.5 w-3.5 text-muted-foreground" />
                            <span>{turno.odontologo.nombre}</span>
                          </div>
                          {turno.odontologo.email && (
                            <div className="text-xs text-muted-foreground">
                              {turno.odontologo.email}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-slate-700 dark:text-neutral-300">
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
                          {canCancel ? (
                            <Button
                              type="button"
                              size="sm"
                              variant="destructive"
                              loading={isMutating}
                              disabled={cancelarMutation.isPending}
                              onClick={() => handleCancelar(turno.id)}
                            >
                              <XCircle className="mr-1 h-3.5 w-3.5" />
                              <span>Cancelar turno</span>
                            </Button>
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

export default PacienteMisTurnosPage;
