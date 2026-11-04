# Design: Dark Mode Theme Support

## Context

La aplicación cliente de gestión odontológica utiliza React 19, TypeScript estricto, Vite y Tailwind CSS. Los componentes base (`Button`, `Card`, `Input`, `Table`, `Alert`) y los portales por rol (`AppLayout`, `AuthLayout`) utilizan utilidades semánticas respaldadas por variables CSS HSL definidas en `frontend/src/index.css`.

El diseño debe alejarse explícitamente de estéticas genéricas "IA-slop" (grises planos uniformes `#121212`, contrastes pobres o neones saturados sin jerarquía). En su lugar, se adopta una paleta Midnight Obsidian / Deep Slate con profundidad óptica, superficies estratificadas y acentos clínicos Teal/Cyan de alta legibilidad WCAG AA. Asimismo, el control de alternancia debe ser un toggle interactivo moderno con microinteracciones táctiles y feedback visual inmediato.

Para mayor detalle de motivación y alcance, consultar `proposal.md`. Para especificaciones de comportamiento normativo, consultar `specs/ui-dark-mode-theme/spec.md`.

## Goals / Non-Goals

**Goals:**
- Proveer soporte de modo oscuro completo (`dark mode`) con una dirección visual artesanal y refinada (paleta Midnight Obsidian con elevación óptica por capas: fondo `#090d16`, tarjetas `#111827`, bordes sutiles `rgba(255,255,255,0.08)` y textos níveos `#f8fafc`).
- Evitar colores "IA-slop" mediante tokens HSL balanceados con contraste superior a 7:1 en textos principales y 4.5:1 en textos secundarios.
- Implementar un componente `ThemeToggle` moderno: switch tipo píldora deslizante con microinteracciones fluidas (`ease-out`, `active:scale-95`), iconos vectoriales de Sol/Luna y accesibilidad plena (`role="switch"`, `aria-checked`, foco de teclado).
- Implementar un proveedor de contexto `ThemeProvider` y un hook `useTheme` que gestione los estados `'light'`, `'dark'` y `'system'` con persistencia en `localStorage` (clave `clinic-theme`).
- Integrar el control en `AppLayout` y `AuthLayout`.

**Non-Goals:**
- Múltiples temas extravagantes (ej. degradados estridentes o paletas cyberpunk fuera del dominio odontológico).
- Persistir la preferencia de tema en la base de datos backend (se resuelve en el cliente mediante `localStorage`).

## Decisions

### 1. Dirección Cromática Artesanal: Midnight Slate vs. "IA-Slop"
- **Decisión**: Utilizar una paleta con tinte azul profundo / obsidiana en `.dark`:
  - `--background`: `222 47% 6%` (negro obsidiana profundo, no gris plano lavado)
  - `--card`: `222 40% 10%` (superficie elevada distinguible del lienzo)
  - `--popover`: `222 40% 12%`
  - `--border`: `217 33% 18%` (separaciones finas translúcidas)
  - `--foreground`: `210 40% 98%` (blanco nítido de máximo contraste)
  - `--muted-foreground`: `215 20% 65%` (gris pizarra legible para metadatos)
  - `--primary`: `199 89% 48%` / `187 85% 43%` (cian odontológico luminoso y nítido)
- **Alternativa considerada**: Negro puro `#000000` o gris neutro Tailwind `bg-neutral-900`. Se descartó por ser la típica fórmula genérica sin profundidad ni elegancia clínica.
- **Razón**: Transmite serenidad, higiene y modernidad propia de un software médico de primer nivel, reduciendo la fatiga visual del odontólogo y la recepcionista.

### 2. Componente `ThemeToggle` Moderno con Micro-interacciones
- **Decisión**: Diseñar un switch tipo cápsula/píldora con deslizador animado (sliding thumb), iconos vectoriales minimalistas (Sol dorado cálido y Luna índigo/azulada con micro-brillo) y retroalimentación táctil:
  - Transición fluida `transform 200ms cubic-bezier(0.16, 1, 0.3, 1)`.
  - Microinteracción al presionar: `active:scale-95`.
  - Anillo de foco accesible para teclado (`focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2`).
  - Atributos semánticos: `role="switch"`, `aria-checked={theme === 'dark'}`, `aria-label="Cambiar a modo claro/oscuro"`.
- **Alternativa considerada**: Un botón circular simple con un emoji o icono estático sin animación.
- **Razón**: Responde al requerimiento del usuario de contar con un componente estéticamente pulido, moderno y gratificante de interactuar.

### 3. Conmutación manual y de sistema mediante `darkMode: 'class'`
- **Decisión**: Configurar `darkMode: 'class'` en `frontend/tailwind.config.js`.
- **Razón**: Otorga control explícito al usuario en la barra de navegación respetando a su vez el fallback del sistema (`prefers-color-scheme`).

## UI Mockups

Decision: no (project policy)

## Risks / Trade-offs

- [Riesgo: Parpadeo de tema (FOUC) al recargar la aplicación] → **Mitigación**: Inicializar el estado leyendo inmediatamente de `localStorage` y aplicando la clase al elemento raíz de forma síncrona antes del primer renderizado visual.
- [Riesgo: Animaciones excesivas que entorpezcan la agilidad operativa] → **Mitigación**: Se utiliza una transición rápida y seca de 200ms orientada a feedback táctil sin demoras innecesarias.
