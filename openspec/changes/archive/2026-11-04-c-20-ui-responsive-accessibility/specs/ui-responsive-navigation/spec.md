# Spec Delta: UI Responsive Navigation & Visual Identity

## Purpose

Provee sistema de navegación responsivo con cápsula flotante de cristal en desktop, dock flotante inferior en mobile, layout de ancho completo y login clínico modernizado conforme a las especificaciones aprobadas.

## ADDED Requirements

### Requirement: Desktop Floating Glass Capsule Navigation
The system SHALL provide a centered floating glassmorphic capsule navbar for viewports 768px and wider, containing the clinic emblem, segmented pill navigation links corresponding to the authenticated user's role, theme toggle, user badge, and logout control.

#### Scenario: Display role-specific navigation pills in desktop capsule
- **WHEN** a user logs in with role `'recepcion'`, `'odontologo'`, or `'paciente'` in desktop view
- **THEN** the system SHALL render the navigation capsule at the top of the viewport with links matching that role.

#### Scenario: Highlight active route with animated pill state
- **WHEN** the current route matches a navigation item
- **THEN** the corresponding pill item SHALL display the active primary highlight with white/contrasting text.

#### Scenario: Trigger logout from user capsule
- **WHEN** the user activates the logout button in the navigation capsule
- **THEN** the session SHALL be terminated and the user redirected to `/login`.

### Requirement: Mobile Floating Bottom Dock Navigation
The system SHALL provide a floating bottom dock for viewports narrower than 768px, positioned in the thumb zone, with an elevated active indicator bubble and touch targets conforming to WCAG 2.5.5 (>= 44x44px).

#### Scenario: Display mobile bottom dock with role links
- **WHEN** viewing the application in a mobile viewport (< 768px)
- **THEN** the bottom dock SHALL be fixed at the bottom with touch targets for all role-allowed routes.

#### Scenario: Elevate active tab bubble
- **WHEN** a mobile route is active
- **THEN** that item SHALL render an elevated bubble indicator with contrasting icon and label.

### Requirement: Modernized Clinical Auth & Login View
The system SHALL provide a clinical authentication card featuring subtle ambient illumination, clinic brand mark, accessibility-compliant input fields, and quick 1-click test credentials selector.

#### Scenario: Quick fill credentials from demo role chips
- **WHEN** a user clicks on any demo role chip (Recepción, Odontólogo, Paciente) on the login page
- **THEN** the identifier and password fields SHALL be automatically populated with the corresponding test credentials.
