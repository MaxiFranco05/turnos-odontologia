# Proposal: Dark Mode Theme Support

## Why

La aplicación web de turnos odontológicos cuenta con layouts completos para autenticación y portales por rol (recepción, odontólogo, paciente), pero opera exclusivamente bajo un tema visual claro. El personal clínico y administrativo pasa jornadas prolongadas en consultorio con baja iluminación, requiriendo un modo oscuro que mitigue la fatiga visual. Asimismo, los pacientes y usuarios esperan una experiencia accesible que respete las preferencias de su sistema operativo y permita alternar manualmente entre modo claro y oscuro con persistencia y contraste WCAG AA.

## What Changes

- Soporte de conmutación de clases oscuras (`darkMode: 'class'`) en la configuración de Tailwind CSS.
- Definición de tokens de color semánticos de modo oscuro (`.dark`) en `frontend/src/index.css` basados en la paleta Slate/Zinc (fondos `Slate-950`/`Slate-900`, tarjetas y bordes de contraste, textos `Slate-100`/`Slate-200` y acentos de alto contraste).
- Contexto y hook de tema (`ThemeContext` / `useTheme`) con soporte para modos `'light'`, `'dark'` y `'system'`.
- Persistencia de la preferencia de tema en `localStorage` (clave `clinic-theme`).
- Componente interactivo y accesible `ThemeToggle` (Sol / Luna) con atributos ARIA y navegación por teclado.
- Integración del control `ThemeToggle` en el header global de `AppLayout` y en el encabezado de `AuthLayout`.
- Detección automática y reactiva ante cambios en la preferencia del sistema operativo (`prefers-color-scheme`) cuando el modo seleccionado es `'system'`.

## Capabilities

### New Capabilities
- `ui-dark-mode-theme`: Provee el motor de temas visuales (Light / Dark / System preference), persistencia en localStorage, reactividad ante eventos del sistema, tokens HSL dark de alto contraste accesibles y control interactivo ThemeToggle en los encabezados globales.

### Modified Capabilities
<!-- No requirement changes to existing capabilities -->

## Impact

- **Frontend**:
  - `frontend/tailwind.config.js`: incorporación de `darkMode: 'class'`.
  - `frontend/src/index.css`: definición de variables CSS para la clase `.dark`.
  - `frontend/src/context/ThemeContext.tsx` y `frontend/src/hooks/useTheme.ts`: nuevo contexto y hook de tema.
  - `frontend/src/components/ThemeToggle.tsx`: nuevo componente visual con iconos SVG accesibles.
  - `frontend/src/layouts/AppLayout.tsx` y `frontend/src/layouts/AuthLayout.tsx`: inclusión de `ThemeToggle`.
  - `frontend/src/App.tsx`: envoltura del árbol de componentes con `ThemeProvider`.
- **Dependencias**: Cero dependencias externas adicionales requeridas (CSS Variables estándar y React Context).
- **APIs / Backend**: Sin impacto en endpoints ni base de datos (Gobernanza BAJA).
