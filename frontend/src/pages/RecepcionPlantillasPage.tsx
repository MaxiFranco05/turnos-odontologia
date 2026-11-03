import React, { useMemo, useState } from 'react';
import {
  Clock,
  Plus,
  Pencil,
  Trash2,
  Filter,
  RotateCcw,
  CalendarDays,
  X,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/Alert';
import {
  usePlantillasQuery,
  useCreatePlantillaMutation,
  useUpdatePlantillaMutation,
  useDeletePlantillaMutation,
} from '@/hooks/usePlantillas';
import {
  extractApiErrorMessage,
  normalizeTimeHHMM,
} from '@/services/reception.service';
import {
  DIAS_SEMANA_LABELS,
  type PlantillaItem,
} from '@/types/reception';

export interface RecepcionPlantillasPageProps {
  initialOdontologoId?: number;
}

export const RecepcionPlantillasPage: React.FC<RecepcionPlantillasPageProps> = ({
  initialOdontologoId,
}) => {
  // Filter state
  const [filterOdontologoInput, setFilterOdontologoInput] = useState<string>(
    initialOdontologoId !== undefined ? String(initialOdontologoId) : ''
  );

  // Form state (supports both Create via POST and Partial Update via PATCH)
  const [editingPlantillaId, setEditingPlantillaId] = useState<number | null>(null);
  const [odontologoId, setOdontologoId] = useState<string>(
    initialOdontologoId !== undefined ? String(initialOdontologoId) : '2'
  );
  const [diaSemana, setDiaSemana] = useState<string>('0');
  const [horaInicio, setHoraInicio] = useState<string>('08:00');
  const [horaFin, setHoraFin] = useState<string>('12:00');
  const [duracionSlotMinutos, setDuracionSlotMinutos] = useState<string>('30');
  const [prestacion, setPrestacion] = useState<string>('');

  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const parsedFilterOdontologoId = useMemo<number | undefined>(() => {
    const trimmed = filterOdontologoInput.trim();
    if (!trimmed) return undefined;
    const num = Number(trimmed);
    return Number.isInteger(num) && num > 0 ? num : undefined;
  }, [filterOdontologoInput]);

  const plantillasQuery = usePlantillasQuery(parsedFilterOdontologoId);
  const createMutation = useCreatePlantillaMutation();
  const updateMutation = useUpdatePlantillaMutation();
  const deleteMutation = useDeletePlantillaMutation();

  const items: PlantillaItem[] = plantillasQuery.data ?? [];

  const groupedByDay = useMemo<Record<number, PlantillaItem[]>>(() => {
    const groups: Record<number, PlantillaItem[]> = {
      0: [],
      1: [],
      2: [],
      3: [],
      4: [],
      5: [],
      6: [],
    };
    for (const item of items) {
      if (!groups[item.dia_semana]) {
        groups[item.dia_semana] = [];
      }
      groups[item.dia_semana].push(item);
    }
    return groups;
  }, [items]);

  const resetFormToCreate = (): void => {
    setEditingPlantillaId(null);
    setDiaSemana('0');
    setHoraInicio('08:00');
    setHoraFin('12:00');
    setDuracionSlotMinutos('30');
    setPrestacion('');
  };

  const handleStartEdit = (plantilla: PlantillaItem): void => {
    setFormError(null);
    setFormSuccess(null);
    setEditingPlantillaId(plantilla.id);
    setOdontologoId(String(plantilla.odontologo_id));
    setDiaSemana(String(plantilla.dia_semana));
    setHoraInicio(normalizeTimeHHMM(plantilla.hora_inicio));
    setHoraFin(normalizeTimeHHMM(plantilla.hora_fin));
    setDuracionSlotMinutos(String(plantilla.duracion_slot_minutos));
    setPrestacion(plantilla.prestacion);
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    setFormError(null);
    setFormSuccess(null);

    const parsedOdontologo = Number(odontologoId);
    const parsedDia = Number(diaSemana);
    const parsedDuracion = Number(duracionSlotMinutos);
    const normalizedInicio = normalizeTimeHHMM(horaInicio);
    const normalizedFin = normalizeTimeHHMM(horaFin);
    const trimmedPrestacion = prestacion.trim();

    if (!Number.isInteger(parsedOdontologo) || parsedOdontologo <= 0) {
      setFormError('Ingresá un ID de odontólogo válido.');
      return;
    }
    if (!normalizedInicio || !normalizedFin || normalizedFin <= normalizedInicio) {
      setFormError('La hora de fin debe ser posterior a la hora de inicio.');
      return;
    }
    if (!Number.isInteger(parsedDuracion) || parsedDuracion <= 0) {
      setFormError('La duración del turno debe ser un número entero mayor a 0.');
      return;
    }
    if (!trimmedPrestacion) {
      setFormError('La prestación o especialidad es obligatoria.');
      return;
    }

    if (editingPlantillaId !== null) {
      updateMutation.mutate(
        {
          plantillaId: editingPlantillaId,
          payload: {
            dia_semana: parsedDia,
            hora_inicio: normalizedInicio,
            hora_fin: normalizedFin,
            duracion_slot_minutos: parsedDuracion,
            prestacion: trimmedPrestacion,
          },
        },
        {
          onSuccess: () => {
            setFormSuccess('Plantilla horaria actualizada correctamente.');
            resetFormToCreate();
          },
          onError: (err: unknown) => {
            setFormError(
              extractApiErrorMessage(err, 'No se pudo actualizar la plantilla horaria.')
            );
          },
        }
      );
    } else {
      createMutation.mutate(
        {
          odontologo_id: parsedOdontologo,
          dia_semana: parsedDia,
          hora_inicio: normalizedInicio,
          hora_fin: normalizedFin,
          duracion_slot_minutos: parsedDuracion,
          prestacion: trimmedPrestacion,
        },
        {
          onSuccess: () => {
            setFormSuccess('Plantilla horaria registrada correctamente.');
            setPrestacion('');
          },
          onError: (err: unknown) => {
            setFormError(
              extractApiErrorMessage(err, 'No se pudo registrar la plantilla horaria.')
            );
          },
        }
      );
    }
  };

  const handleDelete = (plantillaId: number): void => {
    setFormError(null);
    setFormSuccess(null);
    setDeletingId(plantillaId);

    deleteMutation.mutate(plantillaId, {
      onSuccess: () => {
        setDeletingId(null);
        if (editingPlantillaId === plantillaId) {
          resetFormToCreate();
        }
        setFormSuccess('Plantilla horaria eliminada correctamente.');
      },
      onError: (err: unknown) => {
        setDeletingId(null);
        setFormError(
          extractApiErrorMessage(err, 'No se pudo eliminar la plantilla horaria.')
        );
      },
    });
  };

  const queryErrorMessage = plantillasQuery.isError
    ? extractApiErrorMessage(
        plantillasQuery.error,
        'No se pudieron cargar las plantillas de disponibilidad.'
      )
    : null;

  const isMutatingForm = createMutation.isPending || updateMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Encabezado */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">
          Plantillas de Disponibilidad Semanal
        </h1>
        <p className="mt-1 text-sm text-slate-600">
          Configurá los bloques horarios recurrentes de cada odontólogo por día de la semana.
          El motor de disponibilidad rechazará automáticamente cualquier superposición horaria
          (permitiendo bloques adyacentes donde fin == inicio).
        </p>
      </div>

      {/* Alertas accesibles */}
      {(formError || queryErrorMessage) && (
        <Alert variant="destructive">
          <AlertTitle>Error de validación o conflicto horario</AlertTitle>
          <AlertDescription>{formError || queryErrorMessage}</AlertDescription>
        </Alert>
      )}

      {formSuccess && !formError && (
        <Alert variant="success" role="status">
          <AlertDescription>{formSuccess}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Columna izquierda: Formulario de Alta / Edición Parcial */}
        <div className="lg:col-span-4">
          <Card className="sticky top-24">
            <CardHeader>
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  {editingPlantillaId !== null ? (
                    <>
                      <Pencil className="h-4 w-4 text-primary" />
                      <span>Editar Plantilla #{editingPlantillaId}</span>
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 text-primary" />
                      <span>Nueva Plantilla Horaria</span>
                    </>
                  )}
                </span>
                {editingPlantillaId !== null && (
                  <Button
                    type="button"
                    size="sm"
                    variant="ghost"
                    onClick={resetFormToCreate}
                  >
                    <X className="mr-1 h-3.5 w-3.5" />
                    <span>Cancelar</span>
                  </Button>
                )}
              </CardTitle>
              <CardDescription>
                {editingPlantillaId !== null
                  ? 'Actualizá los horarios, duración o prestación del bloque seleccionado (PATCH parcial).'
                  : 'Definí un nuevo bloque semanal sin superposición para un odontólogo.'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4" noValidate>
                <Input
                  id="plantilla-odontologo-id"
                  label="ID del odontólogo"
                  type="number"
                  min={1}
                  value={odontologoId}
                  disabled={editingPlantillaId !== null || isMutatingForm}
                  onChange={(e) => setOdontologoId(e.target.value)}
                />

                <div className="space-y-1.5 text-left">
                  <label
                    htmlFor="plantilla-dia-semana"
                    className="block text-sm font-medium leading-none text-slate-700"
                  >
                    Día de la semana
                  </label>
                  <select
                    id="plantilla-dia-semana"
                    value={diaSemana}
                    disabled={isMutatingForm}
                    onChange={(e) => setDiaSemana(e.target.value)}
                    className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    {Object.entries(DIAS_SEMANA_LABELS).map(([dayIndex, label]) => (
                      <option key={dayIndex} value={dayIndex}>
                        {label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <Input
                    id="plantilla-hora-inicio"
                    label="Hora de inicio"
                    type="time"
                    value={horaInicio}
                    disabled={isMutatingForm}
                    onChange={(e) => setHoraInicio(e.target.value)}
                  />
                  <Input
                    id="plantilla-hora-fin"
                    label="Hora de fin"
                    type="time"
                    value={horaFin}
                    disabled={isMutatingForm}
                    onChange={(e) => setHoraFin(e.target.value)}
                  />
                </div>

                <Input
                  id="plantilla-duracion"
                  label="Duración del turno (min)"
                  type="number"
                  min={5}
                  step={5}
                  value={duracionSlotMinutos}
                  disabled={isMutatingForm}
                  onChange={(e) => setDuracionSlotMinutos(e.target.value)}
                />

                <Input
                  id="plantilla-prestacion"
                  label="Prestación o especialidad"
                  type="text"
                  placeholder="ej. Consulta general, Endodoncia..."
                  value={prestacion}
                  disabled={isMutatingForm}
                  onChange={(e) => setPrestacion(e.target.value)}
                />

                <Button
                  type="submit"
                  className="w-full"
                  loading={isMutatingForm}
                  disabled={isMutatingForm}
                >
                  {editingPlantillaId !== null
                    ? 'Actualizar plantilla'
                    : 'Guardar plantilla'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>

        {/* Columna derecha: Tablero semanal de bloques configurados */}
        <div className="space-y-4 lg:col-span-8">
          <Card>
            <CardContent className="p-4 pt-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div className="w-full sm:max-w-xs">
                  <Input
                    id="filtro-plantillas-odontologo"
                    label="Filtrar listado por ID de odontólogo"
                    type="number"
                    min={1}
                    placeholder="Todos los odontólogos"
                    value={filterOdontologoInput}
                    onChange={(e) => setFilterOdontologoInput(e.target.value)}
                  />
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setFilterOdontologoInput('')}
                  >
                    <RotateCcw className="mr-1.5 h-3.5 w-3.5" />
                    <span>Ver todos</span>
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center justify-between text-base">
                <span className="flex items-center gap-2">
                  <CalendarDays className="h-4 w-4 text-primary" />
                  <span>Cronograma Semanal Configurado</span>
                </span>
                <Badge variant="secondary">{items.length} bloques activos</Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {plantillasQuery.isLoading ? (
                <div className="py-10 text-center text-sm text-slate-500">
                  Cargando plantillas de disponibilidad...
                </div>
              ) : items.length === 0 ? (
                <div className="rounded-lg border border-dashed border-slate-200 py-10 text-center">
                  <Filter className="mx-auto h-8 w-8 text-slate-400" />
                  <p className="mt-2 text-sm font-medium text-slate-700">
                    No hay plantillas horarias registradas para este criterio.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(DIAS_SEMANA_LABELS).map(([dayKey, dayLabel]) => {
                    const dayIdx = Number(dayKey);
                    const dayItems = groupedByDay[dayIdx] ?? [];
                    if (dayItems.length === 0) return null;

                    return (
                      <div
                        key={dayIdx}
                        className="rounded-lg border border-slate-200 bg-slate-50/50 p-4"
                      >
                        <div className="mb-3 flex items-center justify-between">
                          <h4 className="text-sm font-semibold text-slate-900">
                            {dayLabel}
                          </h4>
                          <span className="text-xs text-slate-500">
                            {dayItems.length}{' '}
                            {dayItems.length === 1 ? 'bloque' : 'bloques'}
                          </span>
                        </div>
                        <div className="space-y-2.5">
                          {dayItems.map((plantilla) => {
                            const isDeleting =
                              deleteMutation.isPending && deletingId === plantilla.id;
                            return (
                              <div
                                key={plantilla.id}
                                data-testid={`plantilla-item-${plantilla.id}`}
                                className="flex flex-col justify-between gap-3 rounded-md border border-slate-200 bg-white p-3 shadow-sm sm:flex-row sm:items-center"
                              >
                                <div className="space-y-1">
                                  <div className="flex flex-wrap items-center gap-2">
                                    <span className="inline-flex items-center gap-1 font-semibold text-slate-900">
                                      <Clock className="h-3.5 w-3.5 text-primary" />
                                      {normalizeTimeHHMM(plantilla.hora_inicio)} –{' '}
                                      {normalizeTimeHHMM(plantilla.hora_fin)}
                                    </span>
                                    <Badge variant="secondary">
                                      {plantilla.duracion_slot_minutos} min
                                    </Badge>
                                    <Badge variant="outline">
                                      Odontólogo #{plantilla.odontologo_id}
                                    </Badge>
                                  </div>
                                  <p className="text-sm text-slate-600">
                                    {plantilla.prestacion}
                                  </p>
                                </div>

                                <div className="flex items-center gap-2">
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleStartEdit(plantilla)}
                                  >
                                    <Pencil className="mr-1 h-3.5 w-3.5" />
                                    <span>Editar</span>
                                  </Button>
                                  <Button
                                    type="button"
                                    size="sm"
                                    variant="destructive"
                                    loading={isDeleting}
                                    disabled={deleteMutation.isPending}
                                    onClick={() => handleDelete(plantilla.id)}
                                  >
                                    <Trash2 className="mr-1 h-3.5 w-3.5" />
                                    <span>Eliminar</span>
                                  </Button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RecepcionPlantillasPage;
