import React, { useMemo, useState } from 'react';
import {
  Calendar as CalendarIcon,
  CheckCircle2,
  Clock,
  Filter,
  RotateCcw,
  Stethoscope,
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
} from '@/hooks/usePatientPortal';
import {
  extractApiErrorMessage,
  formatLocalDateISO,
  formatTimeFromISO,
} from '@/services/reception.service';
import type { SlotDisponibleItem } from '@/types/patient';

export interface PacienteDisponibilidadPageProps {
  initialOdontologoId?: number;
  initialFecha?: string;
}

export const PacienteDisponibilidadPage: React.FC<
  PacienteDisponibilidadPageProps
> = ({ initialOdontologoId, initialFecha }) => {
  const [odontologoIdInput, setOdontologoIdInput] = useState<string>(
    initialOdontologoId !== undefined ? String(initialOdontologoId) : '2'
  );
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
    setOdontologoIdInput('2');
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
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">
            Reserva de Turnos Online
          </h1>
          <p className="mt-1 text-sm text-slate-600">
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
            Ingresá el número de profesional y la fecha deseada para ver los turnos libres.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3 md:items-end">
            <div>
              <Input
                id="paciente-odontologo-id"
                label="ID de Odontólogo"
                type="number"
                min={1}
                value={odontologoIdInput}
                onChange={(e) => {
                  setOdontologoIdInput(e.target.value);
                  setSelectedSlot(null);
                  setMutationError(null);
                  setMutationSuccess(null);
                }}
              />
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

      {/* Formulario de Confirmación de Turno Seleccionado */}
      {selectedSlot && (
        <Card className="border-primary/40 bg-primary/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base text-primary">
                <Stethoscope className="h-5 w-5" />
                <span>Confirmar Reserva de Turno</span>
              </CardTitle>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCancelSelection}
                className="h-8 w-8 p-0"
              >
                <X className="h-4 w-4" />
                <span className="sr-only">Cerrar selección</span>
              </Button>
            </div>
            <CardDescription>
              Horario:{' '}
              <strong className="font-mono text-slate-800">
                {formatTimeFromISO(selectedSlot.inicio)} –{' '}
                {formatTimeFromISO(selectedSlot.fin)}
              </strong>{' '}
              · Prestación: <strong>{selectedSlot.prestacion}</strong>
            </CardDescription>
          </CardHeader>
          <CardContent>
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
                />
              </div>

              <div className="flex items-center gap-3">
                <Button
                  type="submit"
                  loading={createTurnoMutation.isPending}
                  disabled={createTurnoMutation.isPending}
                >
                  <CheckCircle2 className="mr-1.5 h-4 w-4" />
                  <span>Confirmar solicitud</span>
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={createTurnoMutation.isPending}
                  onClick={handleCancelSelection}
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Grilla de Huecos Disponibles */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center justify-between text-base">
            <span className="flex items-center gap-2">
              <CalendarIcon className="h-4 w-4 text-primary" />
              <span>Turnos Disponibles ({fecha})</span>
            </span>
            <span className="text-xs font-normal text-slate-500">
              {slots.length} horario(s) libre(s)
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {disponibilidadQuery.isLoading ? (
            <div className="py-10 text-center text-sm text-slate-500">
              Consultando horarios disponibles...
            </div>
          ) : slots.length === 0 ? (
            <div className="rounded-lg border border-dashed border-slate-200 py-10 text-center">
              <Clock className="mx-auto h-8 w-8 text-slate-400" />
              <p className="mt-2 text-sm font-medium text-slate-700">
                No hay turnos disponibles para la fecha u odontólogo seleccionado.
              </p>
              <p className="mt-1 text-xs text-slate-500">
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
                        ? 'border-primary bg-primary/5 shadow-sm'
                        : 'border-slate-200 bg-white hover:border-slate-300'
                    }`}
                  >
                    <div>
                      <div className="font-mono text-base font-bold text-slate-900">
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
