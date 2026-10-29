import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './Card';
import { Badge } from './Badge';
import { Alert, AlertTitle, AlertDescription } from './Alert';
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from './Table';

describe('Base UI Components (Card, Badge, Alert, Table) - Strict TDD', () => {
  describe('Card', () => {
    it('renders card with header, title, description, and content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Turno Odontológico</CardTitle>
            <CardDescription>Detalles del turno programado</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Paciente: Juan Pérez</p>
          </CardContent>
          <CardFooter>
            <button>Acción</button>
          </CardFooter>
        </Card>
      );
      expect(screen.getByText(/turno odontológico/i)).toBeInTheDocument();
      expect(screen.getByText(/detalles del turno programado/i)).toBeInTheDocument();
      expect(screen.getByText(/paciente: juan pérez/i)).toBeInTheDocument();
    });
  });

  describe('Badge', () => {
    it('renders state badges with domain specific dental variants', () => {
      const { rerender } = render(<Badge variant="solicitado">Solicitado</Badge>);
      expect(screen.getByText(/solicitado/i)).toHaveClass('bg-amber-100');

      rerender(<Badge variant="confirmado">Confirmado</Badge>);
      expect(screen.getByText(/confirmado/i)).toHaveClass('bg-emerald-100');

      rerender(<Badge variant="cancelado">Cancelado</Badge>);
      expect(screen.getByText(/cancelado/i)).toHaveClass('bg-rose-100');

      rerender(<Badge variant="presente">Presente</Badge>);
      expect(screen.getByText(/presente/i)).toHaveClass('bg-blue-100');

      rerender(<Badge variant="ausente">Ausente</Badge>);
      expect(screen.getByText(/ausente/i)).toHaveClass('bg-slate-200');
    });
  });

  describe('Alert', () => {
    it('renders alert and alert description with role="alert"', () => {
      render(
        <Alert variant="destructive">
          <AlertTitle>Error de Conexión</AlertTitle>
          <AlertDescription>No se pudo conectar con el servidor.</AlertDescription>
        </Alert>
      );
      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
      expect(screen.getByText(/error de conexión/i)).toBeInTheDocument();
      expect(screen.getByText(/no se pudo conectar con el servidor/i)).toBeInTheDocument();
    });
  });

  describe('Table', () => {
    it('renders semantic table structure with tabular figures', () => {
      render(
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Hora</TableHead>
              <TableHead>Paciente</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            <TableRow>
              <TableCell className="font-mono">09:00 - 09:30</TableCell>
              <TableCell>Ana Gomez</TableCell>
            </TableRow>
          </TableBody>
        </Table>
      );
      expect(screen.getByRole('table')).toBeInTheDocument();
      expect(screen.getByText('09:00 - 09:30')).toHaveClass('font-mono');
      expect(screen.getByText('Ana Gomez')).toBeInTheDocument();
    });
  });
});
