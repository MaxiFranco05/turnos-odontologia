import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Filter,
  RotateCcw,
  Stethoscope,
  User,
  X,
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
  useDisponibilidadQuery,
  useCreateTurnoMutation,
  useOdontologosQuery,
} from '@/hooks/usePatientPortal';
import {
  extractApiErrorMessage,
  formatLocalDateISO,
  formatTimeFromISO,
} from '@/services/reception.service';
import type { SlotDisponibleItem } from '@/types/patient';

export interface OdontologoOption {
  id: number;
  nombre: string;
  especialidad: string;
  matricula: string;
  avatarText: string;
}

export const ODONTOLOGOS_DISPONIBLES: OdontologoOption[] = [
  {
    id: 2,
    nombre: 'Dra. Sofía Martín',
    especialidad: 'Odontología General y Prevención',
    matricula: 'MN-48291',
    avatarText: 'SM',
  },
  {
    id: 3,
    nombre: 'Dr. Lucas García',
    especialidad: 'Ortodoncia y Prótesis',
    matricula: 'MN-51204',
    avatarText: 'LG',
  },
  {
    id: 5,
    nombre: 'Dr. Martín Ruiz',
    especialidad: 'Odontología General y Cirugía',
    matricula: 'MN-43110',
    avatarText: 'MR',
  },
];

export interface PacienteDisponibilidadPageProps {
  initialOdontologoId?: number;
  initialFecha?: string;
}

export const PacienteDisponibilidadPage: React.FC<
  PacienteDisponibilidadPageProps
> = ({ initialOdontologoId, initialFecha }) => {
  const odontologosQuery = useOdontologosQuery();

  const dentistsList = useMemo<OdontologoOption[]>(() => {
    if (odontologosQuery.data && odontologosQuery.data.length > 0) {
      return odontologosQuery.data.map((doc) => {
        const initials = doc.nombre
          .split(' ')
          .map((p) => p[0])
          .filter(Boolean)
          .slice(0, 2)
          .join('')
          .toUpperCase();
        return {
          id: doc.id,
          nombre: doc.nombre,
          especialidad: doc.especialidad || 'Odontología General',
          matricula: doc.nro_socio || `MN-${48000 + doc.id * 100}`,
          avatarText: initials || 'DR',
        };
      });
    }
    return ODONTOLOGOS_DISPONIBLES;
  }, [odontologosQuery.data]);

  const [userSelectedId, setUserSelectedId] = useState<string | null>(
    initialOdontologoId !== undefined ? String(initialOdontologoId) : null
  );

  const odontologoIdInput = useMemo<string>(() => {
    if (userSelectedId !== null) return userSelectedId;
    if (odontologosQuery.data && odontologosQuery.data.length > 0) {
      return String(odontologosQuery.data[0].id);
    }
    return String(ODONTOLOGOS_DISPONIBLES[0].id);
  }, [userSelectedId, odontologosQuery.data]);

  const [isCustomId, setIsCustomId] = useState<boolean>(() => {
    if (initialOdontologoId === undefined) return false;
    return !ODONTOLOGOS_DISPONIBLES.some((doc) => doc.id === initialOdontologoId);
  });

  const [fecha, setFecha] = useState<string>(
    () => initialFecha || formatLocalDateISO()
  );
  const [selectedSlot, setSelectedSlot] = useState<SlotDisponibleItem | null>(
    null
  );
  const [motivo, setMotivo] = useState<string>('');
  const [motivoError, setMotivoError] = useState<string | null>(null);
  const [mutationSuccess, setMutationSuccess] = useState<string | null>(null);
  const [mutationError, setMutationError] = useState<string | null>(null);

  const parsedOdontologoId = useMemo<number | undefined>(() => {
    const trimmed = odontologoIdInput.trim();
    if (!trimmed) return undefined;
    const num = Number(trimmed);
    return Number.isInteger(num) && num > 0 ? num : undefined;
  }, [odontologoIdInput]);

  const currentDoctor = useMemo<OdontologoOption | null>(() => {
    if (!parsedOdontologoId) return null;
    return (
      dentistsList.find((doc) => doc.id === parsedOdontologoId) || null
    );
  }, [parsedOdontologoId, dentistsList]);

  const disponibilidadQuery = useDisponibilidadQuery({
    odontologoId: parsedOdontologoId,
    fecha,
  });

  const createTurnoMutation = useCreateTurnoMutation();

  const slots: SlotDisponibleItem[] = disponibilidadQuery.data ?? [];

  const handleSelectSlot = (slot: SlotDisponibleItem): void => {
    setSelectedSlot(slot);
    setMotivo('');
    setMotivoError(null);
    setMutationError(null);
    setMutationSuccess(null);
  };

  const handleCancelSelection = (): void => {
    setSelectedSlot(null);
    setMotivo('');
    setMotivoError(null);
  };

  const handleSubmitBooking = (e: React.FormEvent): void => {
    e.preventDefault();
    if (!selectedSlot || !parsedOdontologoId) return;

    const trimmedMotivo = motivo.trim();
    if (!trimmedMotivo) {
      setMotivoError('El motivo de consulta es obligatorio.');
      return;
    }
    setMotivoError(null);
    setMutationError(null);

    createTurnoMutation.mutate(
      {
        odontologo_id: parsedOdontologoId,
        inicio: selectedSlot.inicio,
        fin: selectedSlot.fin,
        motivo: trimmedMotivo,
      },
      {
        onSuccess: () => {
          setSelectedSlot(null);
          setMotivo('');
          setMutationSuccess(
            '¡Solicitud de turno enviada con éxito! Quedó en estado solicitado a la espera de confirmación.'
          );
        },
        onError: (err: unknown) => {
          const message = extractApiErrorMessage(
            err,
            'No se pudo completar la solicitud de turno.'
          );
          setMutationError(message);
        },
      }
    );
  };

  const handleResetFilters = (): void => {
    setIsCustomId(false);
    setUserSelectedId(null);
    setFecha(formatLocalDateISO());
    setSelectedSlot(null);
    setMutationError(null);
    setMutationSuccess(null);
  };

  const queryErrorMessage = disponibilidadQuery.isError
    ? extractApiErrorMessage(
        disponibilidadQuery.error,
        'No se pudo consultar la disponibilidad de turnos.'
      )
    : null;

  return (
    <div className="space-y-6">
      {/* Encabezado clínico del paciente */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Reserva de Turnos Online
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Buscá horarios libres con tu profesional y solicitá tu turno al instante.
          </p>
        </div>
      </div>

      {/* Filtros de búsqueda */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-2 text-base">
            <Filter className="h-4 w-4 text-primary" />
            <span>Buscar Disponibilidad</span>
          </CardTitle>
          <CardDescription>
            Elegí tu odontólogo de preferencia y la fecha deseada para ver los turnos libres.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end">
            <div>
              <label
                htmlFor="paciente-odontologo-select"
                className="block text-sm font-medium text-foreground mb-1.5"
              >
                Odontólogo / Profesional
              </label>
              <select
                id="paciente-odontologo-select"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm text-foreground ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={isCustomId ? 'custom' : odontologoIdInput}
                onChange={(e) => {
                  const val = e.target.value;
                  if (val === 'custom') {
                    setIsCustomId(true);
                  } else {
                    setIsCustomId(false);
                    setUserSelectedId(val);
                  }
                  setSelectedSlot(null);
                  setMutationError(null);
                  setMutationSuccess(null);
                }}
              >
                {dentistsList.map((doc) => (
                  <option key={doc.id} value={String(doc.id)}>
                    {doc.nombre} ({doc.especialidad})
                  </option>
                ))}
                <option value="custom">Ingresar otro ID numérico...</option>
              </select>

              {isCustomId && (
                <div className="mt-2 animate-in fade-in duration-150">
                  <Input
                    id="paciente-odontologo-id"
                    label="ID de Odontólogo"
                    type="number"
                    min={1}
                    placeholder="Ej. 2, 3, 5..."
                    value={odontologoIdInput}
                    onChange={(e) => {
                      setUserSelectedId(e.target.value);
                      setSelectedSlot(null);
                      setMutationError(null);
                      setMutationSuccess(null);
                    }}
                  />
                </div>
              )}
            </div>

            <div>
              <Input
                id="paciente-disponibilidad-fecha"
                label="Fecha de consulta"
                type="date"
                min={formatLocalDateISO()}
                value={fecha}
                onChange={(e) => {
                  setFecha(e.target.value);
                  setSelectedSlot(null);
                  setMutationError(null);
                  setMutationSuccess(null);
                }}
              />
            </div>

            <div>
              <Button
                type="button"
                variant="outline"
                onClick={handleResetFilters}
                className="w-full md:w-auto"
              >
                <RotateCcw className="mr-1.5 h-4 w-4" />
                <span>Restablecer</span>
              </Button>
            </div>
          </div>

          {/* Banner de profesional seleccionado */}
          {currentDoctor ? (
            <div className="mt-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-primary/20 bg-primary/5 p-3.5">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 font-bold text-sm">
                  {currentDoctor.avatarText}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground text-sm">
                      {currentDoctor.nombre}
                    </span>
                    <Badge variant="secondary" className="text-[10px] font-medium">
                      {currentDoctor.matricula}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {currentDoctor.especialidad}
                  </p>
                </div>
              </div>
              <div className="flex items-center text-xs text-muted-foreground">
                <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 mr-1.5" />
                Atención con turno previo
              </div>
            </div>
          ) : parsedOdontologoId ? (
            <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground bg-muted/40 p-2.5 rounded-lg border border-border">
              <User className="h-4 w-4 text-primary" />
              <span>Consultando agenda para profesional con ID #{parsedOdontologoId}</span>
            </div>
          ) : null}
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

      {/* Modal de Confirmación de Turno Seleccionado */}
      {selectedSlot && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-confirmar-turno-title"
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-in fade-in duration-150"
        >
          <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl animate-in zoom-in-95 duration-150">
            {/* Header */}
            <div className="flex items-start justify-between pb-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Stethoscope className="h-5 w-5" />
                </div>
                <div>
                  <h2
                    id="modal-confirmar-turno-title"
                    className="text-lg font-bold text-foreground"
                  >
                    Confirmar Reserva de Turno
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    Revisá los detalles de la consulta antes de enviar tu solicitud.
                  </p>
                </div>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCancelSelection}
                className="h-8 w-8 p-0 rounded-lg text-muted-foreground hover:text-foreground"
                aria-label="Cerrar selección"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Cerrar selección</span>
              </Button>
            </div>

            {/* Doctor & Appointment Summary */}
            <div className="my-5 rounded-xl border border-border bg-muted/30 p-4 space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 font-bold text-sm">
                  {currentDoctor ? currentDoctor.avatarText : 'DR'}
                </div>
                <div>
                  <div className="font-semibold text-foreground text-sm">
                    {currentDoctor
                      ? currentDoctor.nombre
                      : `Odontólogo ID #${parsedOdontologoId}`}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {currentDoctor
                      ? `${currentDoctor.especialidad} · ${currentDoctor.matricula}`
                      : 'Profesional Odontológico'}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2.5 border-t border-border/60 text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">
                    Fecha
                  </span>
                  <span className="font-semibold text-foreground">{fecha}</span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">
                    Horario
                  </span>
                  <span className="font-mono font-bold text-primary">
                    {formatTimeFromISO(selectedSlot.inicio)} –{' '}
                    {formatTimeFromISO(selectedSlot.fin)}
                  </span>
                </div>
                <div className="col-span-2 pt-1">
                  <span className="text-muted-foreground block text-[11px]">
                    Prestación prevista
                  </span>
                  <span className="font-medium text-foreground">
                    {selectedSlot.prestacion}
                  </span>
                </div>
              </div>
            </div>

            {/* Formulario de Motivo */}
            <form onSubmit={handleSubmitBooking} className="space-y-4">
              <div>
                <Input
                  id="reserva-motivo"
                  label="Motivo de consulta *"
                  placeholder="Ej. Control general, limpieza dental, dolor en muela..."
                  value={motivo}
                  onChange={(e) => {
                    setMotivo(e.target.value);
                    if (motivoError) setMotivoError(null);
                  }}
                  error={motivoError ?? undefined}
                  autoFocus
                />
                <p className="mt-1 text-[11px] text-muted-foreground">
                  El profesional utilizará este motivo para preparar el instrumental necesario.
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end gap-3 pt-3 border-t border-border">
                <Button
                  type="button"
                  variant="outline"
                  disabled={createTurnoMutation.isPending}
                  onClick={handleCancelSelection}
                >
                  Cancelar
                </Button>
                <Button
                  type="submit"
                  loading={createTurnoMutation.isPending}
                  disabled={createTurnoMutation.isPending}
                >
                  <CheckCircle2 className="mr-1.5 h-4 w-4" />
                  <span>Confirmar solicitud</span>
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Grilla de Huecos Disponibles */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Turnos Disponibles ({fecha})</span>
            </span>
            <span className="text-xs font-normal text-muted-foreground">
              {slots.length} horario(s) libre(s)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {disponibilidadQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-muted-foreground">
              Consultando horarios disponibles...
            </div>
          ) : slots.length === 0 ? (
            <div className="rounded-lg border border-dashed border-border py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-muted-foreground" />
              <p className="mt-2 text-sm font-medium text-foreground">
                No hay turnos disponibles para la fecha u odontólogo seleccionado.
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                Probá seleccionando otro profesional o una fecha posterior.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {slots.map((slot, index) => {
                const isSelected =
                  selectedSlot?.inicio === slot.inicio &&
                  selectedSlot?.fin === slot.fin;

                return (
                  <div
                    key={`${slot.inicio}-${slot.fin}-${index}`}
                    data-testid={`slot-card-${index}`}
                    className={`flex flex-col justify-between rounded-lg border p-4 transition-all ${
                      isSelected
                        ? 'border-primary bg-primary/10 shadow-sm'
                        : 'border-border bg-card hover:border-slate-500'
                    }`}
                  >
                    <div>
                      <div className="font-mono text-base font-bold text-foreground">
                        {formatTimeFromISO(slot.inicio)} –{' '}
                        {formatTimeFromISO(slot.fin)}
                      </div>
                      <Badge variant="outline" className="mt-1.5 text-xs font-normal">
                        {slot.prestacion}
                      </Badge>
                    </div>

                    <div className="mt-4">
                      <Button
                        type="button"
                        size="sm"
                        variant={isSelected ? 'secondary' : 'default'}
                        className="w-full"
                        onClick={() => handleSelectSlot(slot)}
                      >
                        {isSelected ? 'Seleccionado' : 'Reservar'}
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
  );
};

export default PacienteDisponibilidadPage;
