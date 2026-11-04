# Spec Delta

## Purpose

Provee el motor de temas visuales para la aplicación web odontológica, permitiendo seleccionar y alternar entre modo claro, oscuro o sincronizado con el sistema operativo, persistiendo la preferencia en el navegador y aplicando tokens semánticos accesibles con contraste WCAG AA.

## ADDED Requirements

### Requirement: Theme mode selection and persistence
The system SHALL allow users to switch between light, dark, and system theme modes, persisting the preference in local storage and synchronizing with system color scheme preferences.

#### Scenario: Switch from light to dark mode
- **WHEN** the user triggers the theme toggle while in light mode
- **THEN** the system SHALL add the `dark` class to `document.documentElement` and persist `'dark'` in localStorage.

#### Scenario: Switch from dark to light mode
- **WHEN** the user triggers the theme toggle while in dark mode
- **THEN** the system SHALL remove the `dark` class from `document.documentElement` and persist `'light'` in localStorage.

#### Scenario: Restore persisted theme on application startup
- **WHEN** the application initializes and finds a stored theme preference in localStorage
- **THEN** the system SHALL apply that theme mode to `document.documentElement` without resetting to system default.

#### Scenario: Honor system dark preference when no stored preference exists
- **WHEN** the application initializes without a stored theme preference and the operating system prefers dark mode
- **THEN** the system SHALL activate the `dark` class on `document.documentElement`.

### Requirement: Accessible theme toggle controls in layouts
The system SHALL provide accessible theme toggle controls in both application and authentication layouts, with clear visual icons and accessible labels for assistive technologies.

#### Scenario: Theme toggle rendered in AppLayout header
- **WHEN** an authenticated user navigates any portal view within `AppLayout`
- **THEN** the navigation header SHALL render an interactive theme toggle button displaying the opposite mode icon and accessible label.

#### Scenario: Theme toggle rendered in AuthLayout
- **WHEN** an unauthenticated visitor navigates to `/login` or `/cambiar-password` within `AuthLayout`
- **THEN** the authentication container header SHALL display the theme toggle control.

#### Scenario: Keyboard and screen reader accessibility
- **WHEN** a user navigates to the theme toggle button using keyboard focus
- **THEN** the button SHALL receive visible focus styling and expose an explicit accessible `aria-label`.

#### Scenario: Modern toggle switch semantics and state reflection
- **WHEN** the theme toggle switch is rendered
- **THEN** it SHALL expose `role="switch"` and `aria-checked` reflecting whether dark mode is currently active.
