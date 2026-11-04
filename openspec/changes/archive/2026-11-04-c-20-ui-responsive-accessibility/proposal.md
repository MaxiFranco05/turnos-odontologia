# Proposal: Responsive Glassmorphism Navigation & High-End Visual Identity

## Why

Actualmente, el shell de la aplicación (`AppLayout`) utiliza una barra lateral fija tradicional de 256px (`w-64`) con estética de backoffice anticuado, desperdiciando espacio horizontal en una aplicación donde cada rol tiene únicamente 1 o 2 enlaces de navegación. Asimismo, en dispositivos móviles no existe una barra de navegación adaptada a la ergonomía del pulgar, y la pantalla de inicio de sesión (`AuthLayout` / `LoginPage`) presenta un aspecto corporativo estándar sin identidad clínica distintiva.

Tras la aprobación del prototipo visual interactivo en el laboratorio de diseño (`mockups-redesign.html`), es momento de implementar el rediseño integral:
1. Reemplazar la barra lateral por una **Cápsula Flotante de Cristal (*Floating Glass Capsule*)** en Desktop (estilo iOS / Dynamic Island), liberando el 100% del ancho para las grillas de turnos y agendas médicas.
2. Incorporar un **Dock Flotante Inferior (*Floating Thumb Dock*)** en Mobile (`< 768px`) con burbuja activa elevada y retroalimentación táctil elástica (conforme a WCAG 2.5.5, >= 44x44px).
3. Rediseñar la pantalla de **Login y Autenticación** con identidad clínica de alta gama: contenedor de cristal esmerilado, iluminación ambiental dental suave y selectores rápidos tipo chips de acceso para demostración.

## What Changes

- **Desktop Navigation**: Nueva barra superior centrada flotante tipo cápsula redondeada (`rounded-full`), con efecto *frosted glass* (`backdrop-blur-xl`), emblema clínico dental, solapas segmentadas tipo píldora (*segmented pill tabs*), cápsula de usuario y cierre de sesión accesible.
- **Mobile Navigation**: Dock flotante en el pie de pantalla (`fixed bottom-4 inset-x-4`) con diseño de vidrio redondeado y solapa activa con burbuja elevada (*floating bubble indicator*), adaptado a la zona natural del pulgar.
- **Auth & Login Redesign**: Nueva maqueta de `AuthLayout` y `LoginPage` con tarjeta de cristal esmerilado, aura de luz dental sutil (sin azules pesados ni estética IA-slop) y selector rápido de credenciales de prueba por rol (Recepción, Odontólogo, Paciente).
- **Responsive Layout**: Eliminación del margen y columna de sidebar en `AppLayout`, otorgando ancho completo responsivo a las páginas de agenda y tablas clínicas con desplazamiento horizontal contenido.
- **Touch Targets & Accessibility**: Cumplimiento estricto de WCAG 2.5.5 (mínimo 44x44px) en todos los controles interactivos y micro-interacciones inspiradas en las directrices de Emil Kowalski (`active:scale-[0.96]`, `transition-all 160ms cubic-bezier`).

## Capabilities

### New Capabilities
- `ui-responsive-navigation`: Provee sistema de navegación responsivo de alta gama con cápsula flotante de cristal en desktop, dock flotante inferior en mobile, layout de ancho completo y login clínico modernizado.

### Modified Capabilities
<!-- No requirement changes to existing domain capabilities -->

## Impact

- **Frontend**:
  - `frontend/src/layouts/AppLayout.tsx`: Reemplazo del sidebar vertical por cápsula flotante desktop y dock inferior móvil.
  - `frontend/src/layouts/AuthLayout.tsx` & `frontend/src/pages/LoginPage.tsx`: Rediseño con tarjeta de cristal, aura clínica y chips de acceso rápido.
  - `frontend/src/index.css`: Clases utilitarias y tokens para efecto *frosted glass* y auras luminosas.
  - `frontend/src/layouts/Layouts.test.tsx` y tests de páginas: Actualización de selectores y aserciones para la nueva estructura de navegación.
- **Dependencias**: Cero dependencias externas adicionales.
- **APIs / Backend**: Sin impacto en backend ni base de datos (Gobernanza BAJA).
