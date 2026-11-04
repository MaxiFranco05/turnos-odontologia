# Design: Responsive Glassmorphism Navigation & High-End Visual Identity

## Context

El layout actual [`AppLayout.tsx`](file:///c:/Users/maxif/OneDrive/Facultad/PROG3/Metodología/turnos-odontologia/frontend/src/layouts/AppLayout.tsx) implementa una barra lateral fija (`w-64`) para los roles de recepción, odontólogo y paciente. Cada rol solo utiliza entre 1 y 2 enlaces, por lo que el sidebar desperdicia ancho de pantalla crítico para las tablas de turnos y agendas médicas. Asimismo, el login actual carece de una identidad clínica pulida.

Tras la aprobación de la maqueta interactiva en [mockups-redesign.html](file:///c:/Users/maxif/.gemini/antigravity/brain/e9e79247-294b-4f14-afec-eece198d560d/mockups-redesign.html), este diseño documenta la arquitectura de componentes y estilos.

## Goals / Non-Goals

**Goals:**
- Implementar la Cápsula Flotante de Cristal (*Floating Glass Capsule*) en Desktop (`hidden md:flex`, `sticky top-4`, `rounded-full`, `backdrop-blur-xl`).
- Implementar el Dock Flotante Inferior (*Floating Thumb Dock*) en Mobile (`flex md:hidden`, `fixed bottom-4 inset-x-4`) con indicador de burbuja activa elevada.
- Rediseñar `AuthLayout` y `LoginPage` con tarjeta de cristal translúcida, aura dental suave y botones tipo chip para prueba instantánea de credenciales.
- Garantizar touch targets conformes a WCAG 2.5.5 (mínimo 44x44px) y micro-interacciones (`scale(0.96)` en estado activo).
- Mantener 100% de tests unitarios y de integración pasando sin regresiones.

**Non-Goals:**
- Modificar el sistema de autenticación JWT ni alterar roles y permisos RBAC.
- PWA offline o frameworks externos de animación pesados (se utiliza Tailwind nativo y transiciones CSS aceleradas por GPU).

## Decisions

### 1. Eliminación del Sidebar y Adopción de Floating Glass Capsule
- **Decisión**: Eliminar el elemento `aside` vertical estático. En su lugar, el shell ubica una cápsula centrada en la parte superior:
  ```html
  <nav class="glass-surface w-full max-w-4xl rounded-full px-4 py-2 flex items-center justify-between">
    <!-- Brand / Isotipo -->
    <!-- Segmented Nav Links (Pills con activo cian) -->
    <!-- User Capsule, ThemeToggle & Logout -->
  </nav>
  ```
- **Razón**: Aprovecha el ancho completo de la ventana para las agendas clínicas complejas y moderniza radicalmente la estética.

### 2. Dock Móvil Inferior con Indicador Elevado
- **Decisión**: Para viewports móviles (`< 768px`), la navegación se coloca en la parte inferior (`fixed bottom-4 inset-x-4 z-40`). La solapa activa cuenta con una burbuja circular elevada que sobresale levemente del marco, siguiendo la referencia aprobada.
- **Razón**: Máxima accesibilidad ergonómica para el pulgar en teléfonos móviles.

### 3. Rediseño del Login Clínico de Alta Gama
- **Decisión**: `AuthLayout` se centra en una tarjeta con bordes suaves, desenfoque de fondo y un resplandor ambiental (*ambient radial glow*). En `LoginPage` se incorporan chips de acceso rápido (`Recepción (Camila)`, `Odontólogo (Dr. Ruiz)`, `Paciente (Lucía)`) que autocompletan las credenciales para evaluación ágil.
- **Razón**: Crea una identidad estética sofisticada, superando el diseño de caja partida genérico sin perder velocidad de demostración.

### 4. Directrices de Física y Micro-interacciones (Emil Kowalski)
- **Decisión**: Botones e interactivos incorporan `active:scale-[0.96]` y transiciones con curva `cubic-bezier(0.23, 1, 0.32, 1)` de 160ms. Tiempos de animación por debajo de 200ms.
- **Razón**: Sensación de respuesta táctil inmediata y fluidez.

## UI Mockups

- Prototipo interactivo aprobado: [`mockups-redesign.html`](file:///c:/Users/maxif/.gemini/antigravity/brain/e9e79247-294b-4f14-afec-eece198d560d/mockups-redesign.html)
- Capturas de referencia de usuario integradas: `media_1793760201798_f25868e2.png`

## Risks / Trade-offs

- [Riesgo: Dock móvil tapando botones de acción en el pie de página] → **Mitigación**: Añadir un espaciado inferior seguro (`pb-24`) en el contenedor `<main>` para que ningún elemento quede oculto detrás de la barra flotante.
- [Riesgo: Contraste insuficiente en fondos transparentes] → **Mitigación**: Usar tokens `glass-surface` con opacidad controlada (`rgba(255,255,255,0.75)` en light y `rgba(18,18,22,0.8)` en dark) y bordes definidos para garantizar legibilidad en todo momento.
