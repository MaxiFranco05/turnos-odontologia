# Informe de Discovery — turnos-odontologia

**Materia:** Metodología I
**Integrantes:** Máximo Franco
**Fecha de elaboración:** 2026-10-09

## Resumen Ejecutivo
Se investigó el mercado de sistemas de gestión de turnos odontológicos para diseñar un MVP competitivo en Argentina. Se relevaron 18 sistemas (nacionales e internacionales), evaluando su gestión de agenda, automatización, integraciones locales (Mercado Pago, ARCA) y experiencia del paciente. 

**Hallazgos principales:** 
El mercado local está fragmentado. La mayoría de los sistemas delegan la reserva al contacto manual o carecen de reglas estrictas de servidor para evitar solapamientos. Cobrar integraciones básicas (como WhatsApp) es común. 

**MVP Recomendado:**
Un sistema centrado en la inviolabilidad de la agenda. El núcleo será una reserva online con confirmación/anulación por roles estrictos (recepción vs. paciente) y un motor anti-solapamiento robusto. En etapas posteriores se integrarán cobranzas (Mercado Pago) y facturación (ARCA), manteniendo una propuesta de valor de transparencia en precios.

---

**Método**: Q&A de Discovery (11 puntos, sin supuestos) + investigación de mercado con fuentes exclusivamente verificables.
**Criterio metodológico**: solo se consigna como funcionalidad comprobada lo demostrado públicamente. Lo afirmado sin demostración es afirmación comercial. Lo no demostrado se consigna como **«No evidenciado»**.
## Resultado estructurado de discovery-research (checklist de once puntos)

### 1. Problema que resuelve

Los consultorios odontológicos coordinan turnos por WhatsApp y papel, lo que
genera dobles reservas y tiempo perdido confirmando manualmente cada turno.

### 2. Usuarios / roles

- **Paciente** (login con correo o N° de socio/afiliado + contraseña): solicita
  turnos y puede indicar ausentismo a través de estados.
- **Recepción**: confirma los turnos solicitados y los anula cuando corresponde.
- **Odontólogo**: ve la agenda de SUS turnos e indica su estado
  (presente/ausente).

### 3. Casos de uso

1. Como paciente, quiero ver los horarios libres y solicitar un turno para no
   tener que llamar ni escribir por WhatsApp.
2. Como recepción, quiero ver la agenda del día para confirmar o anular turnos
   solicitados.
3. Como odontólogo, quiero ver la agenda de mis turnos para saber a quién
   atiendo y a qué hora.
4. Como paciente, quiero avisar ausentismo sobre un turno para liberar el
   horario.
5. Como odontólogo, quiero indicar el estado de mis turnos (presente/ausente).

### 4. Competidores / soluciones existentes

La "competencia" ya no es solo el proceso manual (WhatsApp + papel): se
relevaron 18 sistemas (6 argentinos, 4 latinos con operación regional y 8
internacionales de referencia). Ver detalle completo en las secciones A–D de
este informe.

**Top 5 más relevantes para Argentina (ranking ponderado, ver §B):**

1. **OdontoClinIA (ClinIA, AR)** — reserva y reprogramación por WhatsApp con
   IA contra agenda real; odontograma FDI versionado; PUCO + factura
   electrónica ARCA.
2. **DentalCore (AR)** — factura ARCA + Mercado Pago + FHIR + auditoría y
   exportación completa; sin reserva online abierta (portal «Próximamente»).
3. **FLAP (perfil Odontología, AR)** — página de reservas 24/7, autoasignación
   por carga, lista de espera con avisos, señas con Mercado Pago, plan gratis.
4. **Doctocliq (LatAm)** — plan gratis hasta 30 citas/mes, WhatsApp Meta
   Partner por paquetes, odontograma + periodontograma; sin facturación AR.
5. **DentalSoft (AR)** — portal del paciente + página web que recibe turnos,
   órdenes a obras sociales con liquidación; sin precios ni FE/MP evidenciados.

### 5. Funcionalidades necesarias

- Solicitud de turno online por parte del paciente.
- Vista de agenda diaria para recepción y odontólogo (cada odontólogo ve SUS
  turnos).
- Confirmación y anulación de turnos por recepción.
- Indicación de ausentismo por el paciente y de presente/ausente por el
  odontólogo, vía estados del turno.

### 6. Funcionalidades opcionales

- Recordatorio automático antes del turno (canal a definir, post-MVP).

### 7. Reglas de negocio

- Un odontólogo no puede tener dos turnos superpuestos.
- La cancelación/anulación requiere una anticipación mínima (valor a definir).
- Los cambios de estado del turno respetan roles: el paciente solicita e
  indica ausentismo, recepción confirma/anula, el odontólogo marca
  presente/ausente sobre sus turnos.

### 8. Integraciones

- Ninguna integración externa obligatoria para la v1.

### 9. Restricciones

- Proyecto académico (materia Metodología), alcance acotado.

### 10. Riesgos

- **Supuesto sin probar**: que la disponibilidad cargada se mantenga
  actualizada — si no, el sistema muestra horarios que en realidad no están
  libres.
- **Riesgo**: pacientes que sigan resolviendo por WhatsApp por costumbre y no
  adopten la reserva online.

### 11. Preguntas abiertas

- Decidido: login de paciente con correo o N° de socio/afiliado + contraseña.
- ¿Cuántos odontólogos participan de la prueba inicial?
- ¿Cuál es el catálogo exacto de estados del turno y sus transiciones
  permitidas?

---

## A. Tabla comparativa (18 sistemas, ordenados por relevancia para Argentina)

Orden de relevancia: presencia y operación en Argentina → adaptación a obra
social / facturación / cobros locales → canal WhatsApp → reserva online
autogestionada → precio en pesos y facilidad de adopción → valor como
referencia de UX (sistemas internacionales).

| # | Producto | Empresa | País | Segmento | Modalidad | Agenda multi-profesional | Reserva online | Recordatorios / automatización | WhatsApp | Gestión clínica | Administración / cobros locales | Integraciones locales | Modelo comercial |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | DentalSoft | DentalSoft (La Plata / Rosario) | Argentina | Clínicas, consultorios y odontólogos AR | SaaS en nube | Comprobado: agenda centralizada, multi-sucursal, horarios por profesional. Vistas, sillones, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: reserva online 24/7, página web de la clínica, portal del paciente (ve y cancela). Reprogramación y lista de espera: No evidenciado | Comprobado: recordatorios por WhatsApp y email; campañas y recuperación de pacientes. Confirmación/cancelación desde el recordatorio: No evidenciado | Declarado (recordatorios y asistente que agenda por WhatsApp); API oficial: No evidenciado | Comprobado: ficha del paciente, odontograma interactivo inicial/evolutivo con PDF, ortodoncia, estudios 3D, consentimientos con firma, recetas digitales, órdenes a obras sociales | Comprobado: presupuestos con aprobación desde el turno, caja y cierre de caja, cuenta corriente, obras sociales y coberturas, liquidaciones (obra social y profesionales), inventario, reportes. Facturación electrónica ARCA, Mercado Pago, señas: No evidenciado | Comprobado: sincronización con Google Calendar. WhatsApp API, API pública, ARCA: No evidenciado | Demo sin tarjeta (comprobado). Precios no publicados; funcionalidades según plan |
| 2 | DentalCore | Od. A. Di Tullio / CTO I. Naveilhan (La Plata) | Argentina (opera en 8 países LatAm) | Consultorio unipersonal a clínicas de hasta 100 usuarios | SaaS web (Chrome/Edge); sin app nativa; links al paciente sin instalación | Comprobado: agenda visual multi-doctor con drag & drop, sala de espera, tareas automáticas; asistente de voz que avisa solapamientos (asistido, no regla dura documentada). Sillones, bloqueos, sobreturnos: No evidenciado | Parcial: el paciente confirma/cancela con un toque desde el link y la agenda se libera sola; videoconsulta con link por WhatsApp. Reserva abierta 24/7 y portal del paciente: No (portal declarado como «Próximamente») | Comprobado y detallado: confirmaciones/recordatorios 48 h y 24 h por WhatsApp (API oficial de Meta, plantillas aprobadas), post-operatorios, controles vencidos, cumpleaños, laboratorio listo, bandeja compartida. Lista de espera: No evidenciado | Comprobado: WhatsApp API oficial de Meta | Comprobado y extenso: odontograma + periodontograma, 15 módulos por especialidad, 17 motores CDSS con fuentes, recetas con chequeo de farmacia, 22 consentimientos con firma, derivaciones, órdenes de Rx y laboratorio, índice de salud oral. Receta electrónica legal: ReNaPDiS en trámite (no vigente) | Comprobado (AR): QR/link de Mercado Pago con registro en caja, factura electrónica ARCA (C/B con CUIT, CAE y QR) por WhatsApp/email, caja con arqueo, deudores, cobertura/copago, liquidación de obras sociales (OSDE, Swiss Medical, PAMI precargadas) | Comprobado: WhatsApp API oficial, Mercado Pago, ARCA (AR), HL7 FHIR R4/R5, CSV/FHIR para migración. Google Calendar, API pública general: No evidenciado | Un solo plan todo incluido: USD 50/mes (2 usuarios) + USD 10 por usuario adicional; videoconsulta USD 0,50. En AR se paga en pesos. Sin plan gratis ni prueba; reembolso 14 días. Promo fundadores −30 % 6 meses hasta 31/12 |
| 3 | Bilog | Bilog (empresa odontológica argentina) | Argentina | Consultorios, clínicas multi-profesional y obras sociales/gerenciadoras | Nube (App Web + App Mobile iOS/Android publicadas) | Comprobado: agenda diaria, turnos por profesional/consultorio, estados de turno, confirmaciones automáticas. Vista semanal, sillones, duración variable, bloqueos, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: agenda online (paciente reserva, cancela y consulta); alta por QR en recepción. Reprogramación y lista de espera: No evidenciado | Comprobado: recordatorios y confirmaciones automáticas. Canal, reglas de reintento, ausentes, campañas: No evidenciado | No evidenciado (los pacientes «llegan desde WhatsApp» como origen, sin integración documentada) | Comprobado: ficha del paciente, odontograma, tratamientos y evolución digital, historia clínica con adjuntos, recetas, asistente «iAngela» (con descargo clínico). Detalle FDI/versiones: No evidenciado | Comprobado: prestaciones, obras sociales, liquidaciones, presupuestos, pagos, reportes y KPI. Caja, facturación electrónica, Mercado Pago, señas: No evidenciado | No evidenciado (sin WhatsApp API, Google Calendar, API pública ni AFIP/ARCA en la fuente) | Solo «Solicitar demo»; precios no publicados. Cobro mensual con factura (tarjeta, transferencia o depósito), sin permanencia, configuración inicial sin costo |
| 4 | OdontoClinIA (ClinIA) | Emprinet | Argentina | Consultorios privados, clínicas PyME multi-silla, servicios municipales/hospitalarios (SUMAR+), cadenas multi-sucursal | Plataforma web por instancia con subdominio propio; turnero web + app de pacientes; nada que instalar | Comprobado: agenda por profesional, especialidad o sillón/consultorio. Vistas, duraciones, bloqueos, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: turnero web + app + reserva por WhatsApp con IA contra agenda real; confirmación, cancelación y reprogramación por WhatsApp. Lista de espera: No evidenciado | Comprobado: recordatorios/confirmaciones automáticos por WhatsApp y correo; IA que deriva a humano. Ausentes, recuperación, campañas, controles: No evidenciado | Comprobado: WhatsApp con IA que valida contra agenda real | Comprobado y detallado: odontograma FDI de 52 piezas por cara (5 caras), existente vs. indicado, versiones bloqueadas con historial por pieza y comparación, plan con CIE-10 + nomenclador, historia clínica con adjuntos y asistente IA, exportación PDF con matrícula | Comprobado: verificación de cobertura vía API PUCO, facturación a obras sociales/prepagas con factura electrónica ARCA, caja para particulares en ARS/USD/EUR con recibo PDF por WhatsApp y arqueo. Mercado Pago, señas: No evidenciado | Comprobado: PUCO, RENAPER (declarado disponible), ARCA, HL7 FHIR (recetas), WhatsApp con IA. Google Calendar, API pública: No evidenciado | Sin precio público; cotización por institución tras demo de 45 min. Usuarios, migración y servidores a $0 dentro del abono |
| 5 | FLAP (perfil Odontología) | Tu WebMaster | Argentina | Odontólogo independiente y clínica dental (incluye odonto-pediatría, ortodoncia, implantología) | SaaS web + PWA instalable + página de reservas mobile-friendly; check-in QR/tótem opcional | Comprobado: agenda multi-profesional con especialidades, box, duración por prestación, disponibilidad y bloqueos, estados visibles, autoasignación por carga entre odontólogos compatibles, analíticas de agenda, lista de espera con avisos. Anti-solapamiento como regla dura: afirmación sin documentación de regla | Comprobado: página de reservas 24/7 con turnero (prestación/profesional/fecha/hora) y demo pública; cancelación/reprogramación declaradas en flujo, autogestión por el paciente No evidenciada | Comprobado: avisos automáticos; email base incluido; WhatsApp vía packs por volumen; solicitud automática de reseña de Google post-atención. Recuperación de ausentes, campañas: No evidenciado | WhatsApp vía packs adicionales (API oficial como tal: No evidenciado) | Comprobado: historia clínica (antecedentes, anamnesis, evoluciones, documentos/fotos), odontograma digital FDI con historial y anulación sin borrado, ortodoncia. Consentimiento/receta formal: No evidenciado | Comprobado: señas y cobros con Mercado Pago vinculados a la reserva, tratamientos/presupuestos, finanzas/liquidaciones, inventario. Facturación electrónica, obras sociales: No evidenciado | Comprobado: Google Calendar y Meet, Mercado Pago, sitio web con SEO. API pública: No evidenciado | Plan Gratis comprobado (turnero, agenda y clientes hasta el límite mensual). Planes pagos en /precios; configuración inicial sin cargo |
| 6 | Livio | Livio (Gestión Dental Inteligente) | Argentina | Clínicas en crecimiento (facturación ARS 5–20 M/mes, segunda sucursal, caos de WhatsApp, cumplimiento HCE) | SaaS web (dashboard) + WhatsApp/web como front del paciente | Comprobado: agenda visual por profesional y sucursal; estados pendiente/confirmado/no-show/cancelado. Vistas, sillones, duraciones, bloqueos, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: chatbot omnicanal 24/7 que agenda solo (WhatsApp + web) con bloqueo de horario; inbox único; recordatorio 24 h antes. Cancelación/reprogramación por el paciente y lista de espera: No evidenciado | Comprobado: recordatorios WhatsApp/SMS/email; chatbot + pipeline de leads + dashboard (no-shows, leads, producción). Protocolos clínicos de control: No evidenciado | Comprobado: WhatsApp (chatbot e inbox) | Comprobado: HCE «en 3 clics» con odontograma interactivo, evolución, adjuntos, firma digital, trazabilidad y respaldo declarados; acceso del paciente «futuro» (hoy no disponible). Detalle FDI/versiones: No evidenciado | Comprobado: dashboard (facturación estimada, producción por profesional, ocupación, no-shows), facturación y reportes. Caja/cobros, Mercado Pago, señas, obras sociales, factura electrónica: No evidenciado | WhatsApp/chatbot comprobados. Google Calendar, API, ARCA: No evidenciado | Prueba gratis 30 días sin tarjeta con todo PRO (comprobado). Plan completo ARS $99.000/mes; Enterprise personalizado. Cancelación libre declarada |
| 7 | AgendaPro (vertical Odontología) | AgendaPro Inc. | Chile (origen); opera en Argentina con sitio y precios locales | Multi-vertical (salud, estética, peluquería, spa, veterinaria) con vertical dental; útil si la clínica mezcla salud + estética | SaaS web + apps «AgendaPro Business» (App Store/Google Play) | Comprobado: turnos configurables por tipo de práctica/profesional, multi-sede y multi-sillón, comisiones por dentista, reportes por profesional/sede. Bloqueos, duración, sobreturnos, anti-solapamiento como reglas duras: No evidenciado | Comprobado: reserva online 24/7 sin registro, link para RRSS, marketplace gratuito, cancelación/cambio con liberación automática, doble confirmación. Lista de espera: No evidenciado | Comprobado: recordatorios automáticos por WhatsApp (complemento pago en AR)/SMS/email; emailing/marketing; ficha/CRM. Recuperación de ausentes como flujo: No evidenciado | WhatsApp como complemento pago, no nativo incluido | Comprobado parcial: historia clínica odontológica editable, registro por profesional, adjunto de imágenes/estudios, fichas personalizables y consentimientos (desde Premium). Odontograma dedicado: No evidenciado | Comprobado: caja en tiempo real, registro automático por turno, seña al reservar, pago online/Mercado Pago con credenciales propias (comisión AgendaPro 2 % +IVA, 1 % +IVA en Pro, más lo de MP), inventario/órdenes de laboratorio, giftcards/presupuestos. Facturación electrónica ARCA, obras sociales: No evidenciado | Comprobado: Mercado Pago (AR), marketplace, emailing, Analytics/Meta Pixel, API (plan Pro), videoconferencia y asistente «Charly» (complementos). Google Calendar: No evidenciado | Precios AR publicados en pesos con IVA: Individual ARS $13.900/mes (1 profesional); Básico desde $33.900; Premium desde $44.900; Pro desde ~$249.900. Complementos (WhatsApp desde $7.900/50 mensajes, video, Charly). Prueba gratis; sin plan gratis permanente |
| 8 | Dentalink | Engenis SpA / HealthAtom | Chile (operación latinoamericana) | Consultas individuales y clínicas multi-profesional/multi-sucursal | SaaS en nube (+ app móvil referenciada) | Comprobado: vista global/semanal/diaria por sillón y profesional; tiempos por odontólogo; estados configurables con sala de espera; sobreturno en agenda paralela; reprogramación individual o masiva; tareas automáticas de citas (plan Titanium). Duración variable, bloqueos, anti-solapamiento explícito: No evidenciado | Comprobado: agendamiento online multi-canal/RRSS; confirmación y reprogramación por el paciente; pagos online. Lista de espera: No evidenciado | Comprobado: recordatorios por WhatsApp/email, tareas automáticas de control y de citas (Titanium), seguimiento de planes presupuestados. Campañas: módulo «fideliza» genérico sin detalle | WhatsApp automático como «próxima alternativa» en ayuda (no disponible a la fecha de la fuente) | Comprobado: historia clínica digital, odontograma + periodontograma, ortodoncia, estética facial, consentimientos, firma electrónica (adicional), imágenes/documentos, videos 3D, telemedicina (adicional), «Clinical Copilot»/IA (novedad 2026 según plan) | Comprobado: pagos presenciales/online, créditos y cuotas, gastos/inventario, comisiones y multicentro, informes. Facturación electrónica por país y obras sociales argentinas: No evidenciado (SII chileno sí) | Comprobado parcial: SII chileno y agendamiento integrable a web. API pública, ARCA, Google Calendar: No evidenciado | Planes Esencial / Pro / Titanium con matriz publicada; cotización obligatoria (precios por país/tamaño sin valores en la página CL). Telemedicina y firma como adicionales |
| 9 | Dentidesk | Dentidesk Chile SpA | Chile (operación latinoamericana) | Clínicas pequeñas y grandes; sindicatos; universidades | SaaS en nube + app móvil (Google Play y App Store) | Comprobado: agenda avanzada personalizable; horarios por profesional con intervalos (15/30/40 min), feriados que bloquean automáticamente, estados personalizables, motivos de consulta, reprogramación. Sillones, duración por prestación, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: link de agendamiento online integrable a la web; correos de confirmación (día previo) con confirmar/anular desde el email; correos de control/cumpleaños. Reserva 24/7, WhatsApp, reprogramación por paciente, lista de espera: No evidenciado (WhatsApp «próxima alternativa») | Comprobado (email): confirmación y recordatorio de controles/cumpleaños. WhatsApp/SMS automáticos, ausentes, recuperación, campañas: No evidenciado | No evidenciado (WhatsApp figura como lote futuro) | Comprobado: ficha con anamnesis/examen/imágenes/informes, odontograma + fichas de especialidades sin costo adicional, presupuestos por pieza/área/superficie, recetas/interconsultas/derivaciones/laboratorio/radiología, consentimientos y plantillas | Comprobado: convenios con descuento, prestaciones, egresos, stock, producción/recaudación/morosos, liquidación por profesional, encuesta post-atención. Mercado Pago, señas, obras sociales argentinas, ARCA: No evidenciado (SII chileno vía integraciones) | Comprobado: SII (CL) y agendamiento online. Google Calendar, API, ARCA: No evidenciado | Un solo plan con todo (usuarios administrativos ilimitados, imágenes sin costo). Prueba 15 días; precios por país/tamaño a cotizar (referencia secundaria: USD 50 inicial) |
| 10 | Doctocliq | Doctocliq (constitución no evidenciada; contactos Perú/México) | Latinoamérica (20+ países; adaptaciones PE, MX, EC, CO) | Profesionales independientes, clínicas y centros (dental, estética, fisio) | SaaS 100 % nube + apps nativas iOS/Android; requiere internet | Comprobado: día/semana/mes por sillón y profesional; motivos con duración; estados (pendiente/confirmada/cancelada/atendida/sala de espera); reprogramación por arrastre; citas recurrentes; importación de Google Calendar. Bloqueos, sobreturnos, anti-solapamiento: No evidenciado | Comprobado: agendamiento online 24/7 por link (WhatsApp/Instagram/Google); confirmación/cancelación desde el mensaje en tiempo real; pago anticipado. Lista de espera formal: No evidenciado (tareas de seguimiento a cancelados/ausentes) | Comprobado: recordatorios automáticos por WhatsApp (paquetes de mensajes, sin mensualidad) y email; seguimiento post-atención; tareas de reagendamiento; marketing y «Soyla IA» (complementos) | Comprobado: WhatsApp (Meta Business Partner declarado) | Comprobado: historia personalizable, odontograma + periodontograma, ortodoncia/estética, recetas/evolución, fotos/documentos, presupuestos con seguimiento de aceptación | Comprobado: caja, facturación electrónica según norma local (PE/MX/EC/CO; Argentina: No evidenciado), inventario/compras, laboratorio, reportes, comisiones. Mercado Pago, señas, ARCA, obras sociales argentinas: No evidenciado | Comprobado: WhatsApp (Meta Partner), Google Calendar (importación), Excel masivo, apps móviles. API pública, ARCA: No evidenciado | Plan gratuito permanente hasta 30 citas/mes sin tarjeta (comprobado) + 7 días en plan Avanzado al registrarse; WhatsApp por paquetes sin mensualidad; planes pagos al escalar |
| 11 | Curve Dental (Curve Hero + Curve GRO) | Curve Dental (CD Newco, LLC) | Estados Unidos / Canadá | Independientes, startups y grupos multi-clínica (EE. UU./Canadá) | SaaS 100 % nube por navegador; app móvil de gestión | Comprobado: agenda con proveedores, operatorias y tipos de cita configurables (duración, días/horarios, antelación mínima); multi-sede con columna de clínica. Sobreturnos y anti-solapamiento explícito: No evidenciado | Comprobado: self-scheduling online (requiere GRO) con caída en tiempo real en agenda y control por prestador/operatoria/tipo/obra social. Cancelación online por el paciente: No evidenciado | Comprobado: GRO incluido en la suscripción (recordatorios, recare, reseñas, mensajes grupales, tareas Smart Action List). Lista corta: Short Notice / Smart Fill con avisos de huecos (comprobado) | No evidenciado (canal SMS/correo 2-way) | Comprobado: charting, imagen, compliance, formularios digitales, videos educativos. IA de última generación: afirmación sin detalle (parcial). Presupuestos: No evidenciado | Comprobado: facturación/billing, pagos electrónicos desde el portal, reportes. Pagos/fiscalidad locales argentinos: No evidenciado | Comprobado parcial: GRO nativo, portal del paciente, reseñas. API pública, WhatsApp, Google Calendar, firma certificada: No evidenciado | Suscripción mensual «Hero» sin hardware; precio no publicado (cotización, USD/CAD). Trial y plan gratis: No evidenciado |
| 12 | Dentally | Dentally (parte de Henry Schein One) | Reino Unido | Independientes, nuevos consultorios, grupos multi-site, prácticas NHS | SaaS cloud por navegador; multi-dispositivo; funciona con baja conectividad | Comprobado: diario con zonas de agenda (p. ej. NHS vs. privado), listas de espera/waitlists, short-notice filler (≤5 días hábiles), duración y precio por tipo de cita online, multi-site con base única. Bloqueos y anti-solapamiento explícito: No evidenciado | Comprobado (Portal + Help Centre): reserva online para nuevos, existentes y recall con depósitos/pagos; cancelación y re-reserva online por el paciente; acceso sin web propia (enlace, QR, SMS/correo); login con OTP; reflejo en tiempo real | Comprobado: recordatorios y confirmaciones automatizadas, recalls inteligentes, campañas a inactivos, reportes de ausentes (FTA) | No evidenciado (canal SMS/correo) | Comprobado: charting, notas por voz con IA (cupo por plan), imagen Vision con IA, historia clínica que el paciente completa desde casa, planes enviados al portal para revisión/firma. Odontograma con ese nombre: No evidenciado; presupuestos: estimaciones de plan (parcial) | Comprobado: facturación, reportes en tiempo real (actividad, ingresos, uso de sillón), integración NHS (no trasladable a AR), depósitos y pagos online vía Portal. Procesadores argentinos: No evidenciado | Comprobado: marketplace de partners, NHS, postcode lookup. WhatsApp, Google Calendar: No evidenciado. API abierta solo en plan Pro (parcial) | Precios públicos en GBP sin IVA: Starter £265/mes, Essentials £380/mes, Pro £510/mes (escala por sillones/sedes). Trial general y plan gratis: No evidenciado |
| 13 | Tab32 | Tab32 | Estados Unidos | Startups e independientes (Alpine, 1–5 prestadores) y grupos/DSO (Summit) | SaaS 100 % cloud-native (Google Cloud); navegador, cualquier dispositivo | Comprobado: scheduling con gestión de sillones, drag-and-drop, ASAP list & waitlist, cross-location scheduling (Summit). Duración por tipo, bloqueos, anti-solapamiento explícito: No evidenciado | Comprobado: online booking desde la web con sincronización en tiempo real; AutoRemind incluido el primer año en Alpine (500 mensajes/mes). Cancelación/reprogramación online por el paciente: No evidenciado | Comprobado: AutoRemind (recordatorios, recall, confirmaciones), comunicación bidireccional, formularios digitales y kiosk check-in (add-on), reportes en tiempo real | No evidenciado (canal SMS/correo) | Comprobado: odontograma, perio, notas, planes de tratamiento, imagen integrada + IA radiológica (PiAI), dictado por voz, laboratorio, ortodoncia. Presupuesto con firma: parcialmente evidenciado (e-sign en formularios) | Comprobado: claims con adjuntos, elegibilidad, ERA/EOB, cuentas por cobrar, Stripe (text-to-pay, tarjetas guardadas), statements. Pagos locales argentinos: No evidenciado | Comprobado: Stripe, DentalXChange, sensores de imagen, Pearl AI, BigQuery/Looker (Summit), SSO Google/Azure, API abierta y MCP para agentes IA. WhatsApp, Google Calendar: No evidenciado | Precios públicos en USD: Alpine Start-Up $125/mes año 1 (hasta 3 prestadores) → $225 desde año 2; Established $225/mes; Summit a medida. Trial 14 días (con tarjeta). Plan gratis: No evidenciado |
| 14 | Dentrix Ascend | Henry Schein One | Estados Unidos | Consultorios individuales, multi-sede, grupos y DSO | SaaS 100 % nube por navegador; sin servidor; disponibilidad declarada 99,99 % | Comprobado: agenda (Schedule) con vistas centralizadas de disponibilidad; multi-profesional y multi-sillón (reserva online exige operatorias fijas por proveedor); duración configurable; plantillas con bloques y excepciones; sincronización que declara evitar dobles reservas online. Sobreturnos: No evidenciado | Comprobado: reserva online 24/7 desde la web, por correo/SMS y Reserve with Google; tipos de cita, prestadores y franjas controlados por el consultorio; confirmación, cancelación y reprogramación por el paciente (Patient Engage). Lista de espera formal: No evidenciado | Comprobado: Patient Engage Suite (recordatorios SMS/correo/voz, confirmaciones, recare/recall, encuestas, mensajería bidireccional). Cifras de resultado (−23 % ausentismo): afirmación del proveedor | No evidenciado (canal SMS/correo/voz, propio del mercado estadounidense) | Comprobado: historia clínica/charting (Quick Exam), odontograma y planificación, imagen con IA (Detect AI / VideaHealth), notas por voz con IA, formularios que escriben en la ficha, presupuestos/planes de tratamiento | Comprobado: elegibilidad aseguradora en tiempo real, claims, ERA, facturación y pagos online y en consultorio, reportes en tiempo real. Pagos locales argentinos: No evidenciado | Comprobado: Reserve with Google, formularios digitales, Patient Engage, IA (AWS, VideaHealth, Pearl en marcas hermanas), phone-AI. API pública general, WhatsApp, Google Calendar bidireccional: No evidenciado | Suscripción mensual por tamaño/n.º de prestadores; sin precio público (cotización, USD). Incluye hosting, actualizaciones y soporte; add-ons de engagement/analítica. Entorno de prueba durante la migración. Plan gratis: No evidenciado |
| 15 | Open Dental | Open Dental Software, Inc. | Estados Unidos | Consultorios de cualquier tamaño, grupos/DSO; bajo costo y alta personalización | Híbrida: auto-hospedada (servidor propio, Windows) + Open Dental Cloud (hosting del proveedor, solo EE. UU.) | Comprobado: agenda con operatorias configurables, clínicas/sedes, bloqueos (blockouts), listas ASAP y recall, confirmaciones por estado, duración variable, multi-profesional (hasta 3 prestadores en tarifa base). Anti-solapamiento como regla configurable: No evidenciado (los blockouts cumplen esa función parcial) | Comprobado: familia Web Sched (New Patient, Existing Patient, Recall, ASAP; servicios pagos); reserva directa o solicitud sujeta a confirmación; citas online marcadas con línea punteada; enlace por SMS/correo y web. Cancelación online autogestionada: parcialmente evidenciada | Comprobado: eReminders/eConfirmations (SMS/correo), agradecimientos, recall automáticos o manuales (vía eServices, bundle pago + texting por mensaje) | No evidenciado | Comprobado: tooth chart, perio, notas clínicas, imágenes, planes de tratamiento, prescripción electrónica (pago por prescriptor), formularios digitales con firma online y OCR de seguros | Comprobado: fee schedules, seguros, claims vía clearinghouse externo (costo por claim), estados de cuenta, caja, queries y reportes personalizados. Pagos locales argentinos: No evidenciado | Comprobado: API de Open Dental, texting, eClipboard, eRx, clearinghouses. WhatsApp, Google Calendar: No evidenciada. Firma digital certificada: No (firma en formularios, parcial) | Precios públicos en USD: licencia + soporte $199/mes/sede (luego $149/mes); fuera de EE. UU./Canadá $89/mes/sede; Cloud aparte ($250–$2.370/mes + migración $400); eServices $165/mes/sede + SMS. Versión de evaluación gratuita. Plan gratis permanente: No evidenciado |
| 16 | CareStack | CareStack | Estados Unidos | Startups, consultorios únicos, grupos multi-sede y DSO; «todo-incluido sin upsells» | SaaS cloud; app móvil (CS Mobile); kioscos de check-in | Comprobado: multi-specialty scheduling, vistas personalizadas, Appointment Finder, Short Call List, calendario de producción, control de permisos online por tipo de producción, multi-sede. Bloqueos, anti-solapamiento, sobreturnos discretos: No evidenciado | Comprobado: auto-reserva online 24/7 desde web o portal con filtros por prestador/tratamiento/sede; dos modos (reserva directa o solicitud sujeta a confirmación); URLs por sede o multi-sede; Reserve with Google. Cancelación/reprogramación online por el paciente: No evidenciado | Comprobado: recordatorios integrados, notificaciones, campañas masivas, agentes IA («Casey»: confirma por llamada/texto/correo y rellena cancelaciones; recobro y recall con IA; alcance real: afirmación comercial) | No evidenciado (SMS/correo/llamada IA) | Comprobado: charting y planes, perio (con voz por IA en plan superior), notas con plantillas (IA en plan superior), imagen nativa con IA (Overjet), laboratorio, ortodoncia/perio/cirugía, prescripción electrónica, formularios y portal | Comprobado: elegibilidad y verificación electrónica, claims centralizados, ERA, tarjetas y card-on-file, reportes/analítica, payroll, referidos, dashboard diario. Pagos locales argentinos: No evidenciado | Comprobado: Google Analytics + Reserve with Google, telefonía IA/VOIP, chat de equipo HIPAA. API pública, WhatsApp, Google Calendar, firma certificada: No evidenciado | Precios públicos en USD: Essentials desde $829/mes, Intelligence desde $1.299/mes (según sedes, sillones, prestadores; cotización final por demo). Demo gratuita; trial auto-servido y plan gratis: No evidenciado |
| 17 | Denticon | Planet DDS | Estados Unidos | Grupos multi-sede, DSO y enterprise (también prácticas individuales) | SaaS cloud por navegador; solo Windows (no Mac, declarado en FAQ) | Comprobado: scheduling avanzado multi-sede (agendar entre sedes), vistas personalizadas, morning huddle, RCM task manager, metas por prestador. Sillones, duración, bloqueos, anti-solape, sobreturnos discretos: No evidenciado | Comprobado: online scheduling + registro online + recordatorios por texto + pagos por SMS/correo; reserva 24/7 declarada. Cancelación/reprogramación online por el paciente y lista de espera: No evidenciado (agentes IA DentalOS que confirman/reagendan: afirmación comercial) | Comprobado parcial: recordatorios, formularios online, comunicaciones; perio por voz; RCM task automation. Recall/campañas como módulo discreto: No evidenciado | No evidenciado | Comprobado: planificación avanzada, imagen nativa (Apteryx XVWeb), ortodoncia, perio por voz, notas de progreso, multi-especialidad. Odontograma/presupuestos discretos: No evidenciado con ese detalle | Comprobado: elegibilidad, batch claims, posteo automático 835/EOB, pagos integrados con débito automático y planes, oficina central de facturación (CBO), reportes sin código. Pagos locales argentinos: No evidenciado | Comprobado: 50+ integraciones vía API. WhatsApp, Google Calendar, firma certificada: No evidenciado | Desde $795/mes (FAQ oficial; paquetes a medida; usuarios/prestadores adicionales sin costo en sedes activas; soporte incluido). Trial: No evidenciado (demo con expertos). Plan gratis: No evidenciado |
| 18 | EXACT | Software of Excellence (parte de Henry Schein One) | Reino Unido / Australia / Nueva Zelanda | Consultorios privados, mixtos (privado + NHS) y multi-site en UK/ANZ | Híbrida: instalada/local con componentes cloud (MyPractice Cloud, Patient Portal, Online Booking) | Comprobado: libro de citas con Utilisation Manager, Short Notice Lists (relleno de huecos), Workflow Manager (tareas de recepción), Multi Practice Cloud con reportes en tiempo real. Duración variable, sobreturnos, anti-solapamiento explícito: No evidenciado | Comprobado: Online Booking + Patient Portal (confirmaciones, formularios desde casa) + Clinipad en recepción. Cancelación/reprogramación online y lista de espera pública: No evidenciado (la lista es interna: short-notice) | Comprobado (punto fuerte): recordatorios automáticos, recalls automáticos, Care Manager (planes pendientes), Marketing Manager y Campaign+, Channel Track, Online Reputation Manager, UDA Manager predictivo. Métricas (88 % recalls, 0,7 % ausentes): cifras del proveedor | No evidenciado (canal SMS/correo) | Comprobado parcial: Examine Pro (imagen), Pearl AI en Rx, planes de tratamiento y seguimiento (Care Manager). Odontograma/anamnesis discretos: No evidenciado | Comprobado: reportes financieros y multi-site en tiempo real, gestión de deuda, UDA/contratos NHS (no trasladable). Caja/cobros online y procesadores argentinos: No evidenciado | Integraciones de terceros «end-to-end» sin catálogo público consultado (parcial). WhatsApp, Google Calendar, API pública, firma digital: No evidenciado | Suscripción con cotización personalizada; precio no publicado (GBP/AUD/NZD). Trial y plan gratis: No evidenciado. Sin presencia americana/latina |

---

## B. Matriz de puntuación ponderada (escala 0–5 por dimensión)

**Dimensiones y pesos:** Gestión de turnos y automatización 25 % (T) ·
Funcionalidad clínica 20 % (C) · Integraciones locales y WhatsApp 15 % (I) ·
Administración, cobros y facturación 15 % (A) · Experiencia del paciente 10 %
(P) · Seguridad, exportación y trazabilidad 10 % (S) · Precio y facilidad de
adopción 5 % ($) — Total ponderado sobre 5,00.

**Regla aplicada:** cada «No evidenciado» en una dimensión reduce la nota de
forma conservadora (ver notas ①–⑦ al pie). Las cifras comerciales no auditadas
(conteos de clientes, «−40 % no-shows», «líder en…») no suman puntaje.

| # | Sistema | T 25 % | C 20 % | I 15 % | A 15 % | P 10 % | S 10 % | $ 5 % | **Total** | Ranking |
|---|---|---|---|---|---|---|---|---|---|---|
| 4 | OdontoClinIA (AR) | 4 | 5 | 5 | 4 | 4 | 3 | 2 | **4,15** | **1** ② |
| 2 | DentalCore (AR) | 3 | 5 | 5 | 5 | 3 | 5 | 2 | **4,15** | **2** ② |
| 5 | FLAP Odonto (AR) | 4 | 3 | 3 | 3 | 5 | 2 | 5 | **3,45** | 3 |
| 10 | Doctocliq (LatAm) | 4 | 4 | 3 | 2 | 4 | 2 | 5 | **3,40** | 4 |
| 1 | DentalSoft (AR) | 4 | 4 | 3 | 3 | 4 | 1 | 3 | **3,35** | 5 |
| 16 | CareStack (EE. UU.) | 4 | 5 | 1 | 1 | 4 | 5 | 1 | **3,25** | 6 ③ |
| 8 | Dentalink (CL) | 4 | 4 | 2 | 3 | 4 | 1 | 2 | **3,15** | 7 |
| 7 | AgendaPro (CL→AR) | 4 | 2 | 3 | 3 | 5 | 1 | 4 | **3,10** | 8 |
| 12 | Dentally (UK) | 5 | 3 | 1 | 1 | 5 | 3 | 1 | **3,00** | 9 |
| 14 | Dentrix Ascend (EE. UU.) | 4 | 4 | 1 | 1 | 4 | 4 | 1 | **2,95** | 10 ③ |
| 13 | Tab32 (EE. UU.) | 4 | 4 | 1 | 1 | 3 | 4 | 3 | **2,95** | 11 ③ |
| 15 | Open Dental (EE. UU.) | 4 | 4 | 1 | 1 | 4 | 2 | 3 | **2,85** | 12 |
| 6 | Livio (AR) | 3 | 3 | 2 | 2 | 4 | 2 | 4 | **2,75** | 13 ④ |
| 11 | Curve (EE. UU./CA) | 4 | 3 | 1 | 1 | 4 | 3 | 1 | **2,65** | 14 ③ |
| 17 | Denticon (EE. UU.) | 3 | 3 | 2 | 1 | 3 | 5 | 1 | **2,65** | 15 ③ |
| 9 | Dentidesk (CL) | 3 | 4 | 1 | 2 | 3 | 1 | 3 | **2,55** | 16 |
| 3 | Bilog (AR) | 3 | 3 | 1 | 2 | 4 | 1 | 2 | **2,40** | 17 ① |
| 18 | EXACT (UK/AU/NZ) | 4 | 2 | 1 | 1 | 3 | 0 | 1 | **2,05** | 18 ⑤ |

**Notas al pie (motivo de las penalizaciones conservadoras):**

- ① **Bilog (17.º):** la home consultada tiene bajo detalle funcional
  verificable (sin precios, sin matriz de planes, sin documentación de
  agenda/clínica/seguridad); las cifras de adopción (+1.500 clínicas, +10 M
  pacientes) son afirmaciones del proveedor. Se penalizan I, A, S y $ con 1–2
  aunque el producto sea argentino y con trayectoria declarada.
- ② **Empate 4,15:** OdontoClinIA queda 1.ª por desempate en la dimensión de
  mayor peso (T = 4 frente a 3 de DentalCore: ClinIA sí tiene reserva y
  reprogramación autogestionada por WhatsApp; DentalCore declara su portal como
  «Próximamente»). DentalCore compensa con la mejor administración local
  evidenciada (ARCA + Mercado Pago + FHIR + auditoría).
- ③ **Sistemas internacionales (puestos 6, 10, 11, 12, 14, 15):** obtienen 1–2
  en I y A porque ninguno evidencia WhatsApp Business API, Mercado Pago, ARCA
  ni obra social argentina; su puntaje proviene de turnos, clínica y
  seguridad. No son comparables en precio (USD/GBP inalcanzables para el
  consultorio medio argentino) y se usan solo como referencia de UX y de
  mecanismos (ver sección D).
- ④ **Livio (13.º):** bien posicionado en canal (chatbot + WhatsApp) y precio
  en pesos con trial, pero sin administración financiera ni obra social
  evidenciadas y sin detalle técnico del odontograma; de ahí el 2–3 en C, I
  y A.
- ⑤ **EXACT (18.º, S = 0):** único sistema sin ninguna evidencia pública de
  seguridad/respaldo/control de acceso en las páginas consultadas; sumado a
  arquitectura híbrida local, precio opaco y nula presencia latina, queda
  último pese a su liderazgo en automatización de recalls.
- ⑥ **DentalSoft (5.º, S = 1):** el mapa funcional agenda + obra social más
  completo entre los argentinos, pero sin evidencia de seguridad, cifrado,
  auditoría o exportación, y sin precios públicos; por eso no entra al top 3
  pese a su relevancia.
- ⑦ **AgendaPro (8.º, C = 2) y Dentidesk (16.º, I = 1):** AgendaPro pierde en
  clínica por ser generalista sin odontograma dedicado evidenciado; Dentidesk
  pierde en integración local por ser email-céntrico con WhatsApp declarado
  como futuro y sin facturación AR.

---

## C. Análisis competitivo

### C.1. Funcionalidades estándar del mercado (las tiene casi todos; la v1 debe cubrir el núcleo)

1. **Agenda por profesional** con vistas día/semana y estados de turno
   (pendiente, confirmado, cancelado, presente/ausente, sala de espera). La
   agenda multi-profesional y multi-sillón/box es universal.
2. **Reserva online 24/7** con control del consultorio sobre qué se ofrece
   (prestador, prestación, franja). Es estándar en 16 de 18 sistemas; las
   excepciones son DentalCore (portal «Próximamente») y matices de
   autogestión.
3. **Confirmación y cancelación por el paciente** desde el mensaje, el email o
   el portal, con liberación automática del horario. Estándar; la
   **reprogramación autogestionada** es menos común (solo ClinIA, Dentalink,
   Dentidesk, Doctocliq y Dentally la evidencian con claridad).
4. **Recordatorios automáticos** (canal según mercado: SMS/correo en
   EE. UU./UK, WhatsApp/correo en LatAm/AR). Todos los sistemas los tienen en
   alguna forma.
5. **Odontograma + historia clínica + presupuestos/planes de tratamiento** como
   tríada clínica mínima. Solo AgendaPro (ficha sin odontograma dedicado) y
   EXACT (odontograma no evidenciado) se apartan.
6. **Ficha del paciente con historial** (turnos, tratamientos, pagos) y
   **reportes básicos** de actividad.

### C.2. Funcionalidades diferenciadoras reales (evidenciadas, no eslóganes)

- **Motor de ocupación y recupero:** short-notice / ASAP lists con avisos de
  huecos (Curve, Tab32, Open Dental, Dentally, EXACT) y reprogramación masiva
  (Dentalink). Es el mecanismo probado contra el ausentismo.
- **Doble modo de reserva** — directa vs. solicitud sujeta a confirmación —
  con marcado visual del origen online (CareStack, Open Dental). Calza
  exactamente con la regla del proyecto (recepción confirma/anula).
- **Disponibilidad derivada de la plantilla del profesional,** no cargada turno
  por turno (Dentrix Ascend, Open Dental, Curve). Mitiga el riesgo
  «disponibilidad desactualizada» del discovery.
- **Convivencia de coberturas en una agenda:** zonas NHS/privado (Dentally),
  sobreturno paralelo (Dentalink), órdenes a obras sociales con seguimiento de
  etapa (DentalSoft), PUCO + nomenclador + CIE-10 (ClinIA). Modelos imitables
  para obra social vs. particular.
- **Cobro pegado a la reserva:** seña y pago online vinculados al turno con
  Mercado Pago (FLAP, AgendaPro en AR; DentalCore con QR/link) y factura
  electrónica ARCA enviada por WhatsApp/email (DentalCore, ClinIA).
- **Trazabilidad y portabilidad de datos:** audit trail + permisos granulares
  (Denticon), auditoría de accesos con usuario/IP/dispositivo y exportación
  completa incluso post-baja (DentalCore), data warehouse abierto (Tab32
  Summit).
- **Soporte clínico con fuentes:** 17 motores CDSS basados en reglas/literatura
  con decisión y firma del profesional (DentalCore); odontograma versionado por
  pieza con comparación (ClinIA).
- **Adquisición y reputación:** marketplace de visibilidad, solicitud
  automática de reseña de Google post-atención y check-in QR (FLAP, AgendaPro);
  asistente de voz/IA que agenda contra la agenda real (DentalCore, ClinIA,
  Livio).

### C.3. Vacíos frecuentes del mercado argentino (oportunidades)

1. **Ningún sistema publica la regla anti-solapamiento por odontólogo como
   invariante verificable de servidor.** El proyecto la exige (checklist §7):
   es diferencial implementable desde el día 1.
2. **WhatsApp casi nunca está incluido:** AgendaPro y FLAP lo cobran aparte,
   Doctocliq por paquetes, DentalCore con plantillas Meta, Dentalink/Dentidesk
   como «futuro». Un recordatorio post-MVP simple y transparente en costo es
   ventaja.
3. **Precios opacos en pesos:** solo Livio, FLAP (plan gratis + /precios) y
   AgendaPro (matriz AR) publican algo; Bilog, DentalSoft y ClinIA exigen
   demo/cotización. La transparencia (precio en ARS, trial sin tarjeta) es
   diferencial de adopción.
4. **Reprogramación autogestionada y lista de espera** son escasas en AR (solo
   ClinIA reprograma por WhatsApp; solo FLAP avisa huecos compatibles).
   Oportunidad de v2, no de v1.
5. **Matriz de estados simple con transiciones por rol estricta**
   (solicitado/confirmado/anulado/ausente/presente): todos los relevados tienen
   catálogos más extensos y difusos. Mantener la simplicidad es
   posicionamiento.
6. **Obra social + facturación + cobro local coexistiendo** solo se evidencia
   en DentalCore (ARCA + Mercado Pago + liquidación OS) y parcialmente en
   ClinIA (PUCO + ARCA, sin Mercado Pago) y DentalSoft (órdenes y liquidación,
   sin FE/MP). El resto omite al menos una pata.
7. **Exportación y auditoría** son casi inexistentes en AR salvo DentalCore; la
   portabilidad de datos es argumento de confianza.

### C.4. Oportunidades de innovación para un nuevo sistema

1. **Turnos como núcleo, no como módulo:** invertir la prioridad del mercado
   (todos son «clínica + agenda») y hacer de la agenda impecable —
   disponibilidad por plantilla, anti-solape de servidor, doble modo
   directa/solicitud — la propuesta de valor.
2. **Operativa de ausentismo criolla:** short-notice list por WhatsApp
   post-MVP (el equivalente argentino al SMS estadounidense), con solicitud de
   reseña de Google post-atención (mecánica ya validada por FLAP).
3. **Transparencia radical:** precio en pesos publicado, plan gratis o trial sin
   tarjeta (mecánica validada por FLAP, Livio, Doctocliq) y política de
   exportación de datos desde el día 1 (nadie la ofrece en AR salvo
   DentalCore).
4. **Escalera obra social → facturación → cobro:** entrar por agenda + estados
   (v1), sumar señas con Mercado Pago (v2), y recién después PUCO/ARCA (etapas
   posteriores), siguiendo el orden de complejidad real que muestra la
   evidencia.
5. **Zonas de agenda obra social/particular** (idea trasladable de Dentally) y
   **pacientes familiares con email compartido** (odontopediatría, validado por
   FLAP) como diferenciales de bajo costo.

---

## D. Recomendación final

### D.1. Cinco competidores prioritarios para analizar con demo

1. **OdontoClinIA (ClinIA)** — https://www.clinia.com.ar/odontologia — Qué
   mirar: reserva y reprogramación por WhatsApp con IA contra agenda real;
   odontograma versionado; PUCO + ARCA. Por qué: mejor ajuste funcional al
   proyecto (turnos + obra social argentina).
2. **DentalSoft** — https://dentalsoft.com.ar/funcionalidades — Qué mirar:
   portal del paciente, página web que recibe turnos, órdenes a obras sociales
   con liquidación. Por qué: mapa agenda + obra social más completo en AR.
3. **FLAP (perfil Odontología)** — https://flap.com.ar/odontologos — Qué mirar:
   página de reservas 24/7, autoasignación por carga, lista de espera con
   avisos, señas con Mercado Pago, plan gratis. Por qué: referencia de
   adopción y de mecánicas v2 (lista de espera, reseñas Google).
4. **DentalCore** — https://dentalcore.app/ — Qué mirar: recordatorios
   WhatsApp API 48/24 h, cobro QR/link de Mercado Pago, factura ARCA por
   WhatsApp, auditoría y exportación FHIR. Por qué: vara de administración
   local + seguridad + portabilidad.
5. **AgendaPro (vertical dental AR)** —
   https://agendapro.com/ar/dental/software-odontologico — Qué mirar: reserva
   sin registro, marketplace, seña al reservar, comisiones, matriz de precios
   AR. Por qué: máquina comercial y modelo de precios en pesos con
   complementos.

*Alternos si hay tiempo: Bilog (cobertura consultorio → clínica → obra social)
y Livio (chatbot + precio único en ARS con trial).*

### D.2. Tres productos de referencia para UX (no son competencia directa en AR)

1. **Dentally (UK)** — https://www.dentally.com/en-gb/ — Portal del paciente
   (reserva + cancelación + re-reserva + formularios + pagos + firma + OTP) y
   zonas de agenda NHS/privado trasladables a obra social/particular.
2. **CareStack (EE. UU.)** — https://carestack.com/ — Doble modo reserva
   directa / solicitud a confirmar con marcado visual del origen online; el
   patrón exacto para «recepción confirma, paciente solicita».
3. **Tab32 (EE. UU.)** — https://tab32.com/ — ASAP list & waitlist +
   comunicación bidireccional + precio público transparente con comparador de
   costo total; el patrón para la v2 de recupero de ausentes.

### D.3. MVP sugerido (coherente con el checklist: v1 acotada, sin integraciones obligatorias, recordatorio post-MVP)

**Imprescindibles (v1 — lo que pide el discovery, endurecido por la
evidencia):**

- Solicitud de turno online por el paciente con login (correo o N.º de
  socio/afiliado + contraseña).
- Disponibilidad derivada de la plantilla del odontólogo
  (días/horarios/duración por prestación), no carga manual turno por turno.
- Agenda del día para recepción (todos los odontólogos) y por odontólogo
  (solo sus turnos).
- Máquina de estados mínima con transiciones por rol estricta: solicitado →
  confirmado / anulado (recepción); ausente avisado por el paciente; presente
  / ausente marcado por el odontólogo sobre sus turnos.
- **Regla anti-solapamiento por odontólogo como invariante de servidor**
  (ningún competidor la publica verificable: diferencial día 1).
- Anticipación mínima configurable para cancelación/anulación.
- Modo de reserva «solicitud sujeta a confirmación» con marcado visual del
  origen online (patrón CareStack/Open Dental).

**Diferenciadores v1 (bajo costo, alto valor):**

- Reserva directa inmediata solo en huecos simples próximos + solicitud a
  confirmar para el resto.
- Confirmación/cancelación por el paciente desde enlace sin instalar nada
  (patrón DentalCore/FLAP).
- Transparencia: precio en pesos visible si se monetiza el piloto, o trial sin
  tarjeta si se valida adopción.

**Etapas posteriores (en este orden, por complejidad real evidenciada):**

1. **Post-MVP inmediato:** recordatorios (canal a definir; WhatsApp como
   equivalente al SMS estadounidense) + reprogramación autogestionada + lista
   de espera / short-notice con avisos.
2. **v2 comercial:** señas y cobros con Mercado Pago vinculados a la reserva
   (patrón FLAP/AgendaPro).
3. **v3 administrativa:** obras sociales (órdenes, cobertura, liquidación;
   patrón DentalSoft), verificación PUCO y factura electrónica ARCA (patrón
   ClinIA/DentalCore).
4. **Fundación de confianza (transversal cuando se toque datos clínicos):**
   roles/permisos granulares + audit trail (patrón Denticon/DentalCore),
   exportación completa (FHIR/CSV) y alineación con Ley 25.326 / Ley 27.706.

**Lo que explícitamente NO entra en v1:** odontograma, historia clínica,
CDSS/IA diagnóstica, marketing multicanal, multi-sede, CBO, integraciones
aseguradoras/NHS, firma certificada. Todo ello existe en el mercado pero es
costo y complejidad fuera del alcance académico.

---

## Verificación de fuentes y uso del protocolo Ajustar

Todas las fuentes oficiales fueron consultadas el **2026-10-09**. Se aplicó el protocolo de inspección para corregir invenciones del agente durante el relevamiento. A continuación, las 5 fuentes comprobadas personalmente y corregidas:

1. **DentalCore (AR)**
   - **URL:** `https://dentalcore.app/funcionalidades/portal-paciente`
   - **Qué afirmaba el informe de la IA:** El agente listó que DentalCore contaba con un "Portal del paciente autogestionado para reserva 24/7".
   - **Qué se encontró y corrigió:** Al verificar la web oficial, la sección del portal indica claramente "Próximamente". Se usó *Ajustar* para obligar al agente a marcar la reserva abierta 24/7 y el portal del paciente como "No" (Próximamente), y modificar la calificación en la tabla comparativa.

2. **FLAP Odontología (AR)**
   - **URL:** `https://flap.com.ar/odontologos/funcionalidades/agenda-online`
   - **Qué afirmaba el informe de la IA:** El agente documentó que FLAP tenía "WhatsApp nativo incluido en todos los planes".
   - **Qué se encontró y corrigió:** Revisando la página de precios, los avisos por WhatsApp se venden como packs por volumen adicionales, no están incluidos de base. Se ajustó el informe para reflejar que es un complemento pago.

3. **Livio (AR)**
   - **URL:** `https://www.liviodental.com/#pricing`
   - **Qué afirmaba el informe de la IA:** El agente indicó que el sistema contaba con "liquidación a obras sociales y facturación electrónica ARCA".
   - **Qué se encontró y corrigió:** En el detalle de funcionalidades (#features) no hay mención alguna a facturación electrónica ARCA ni a obras sociales (se enfocan en dashboard y leads). Se usó *Ajustar* para pasar ambas características a "No evidenciado".

4. **Dentrix Ascend (EE. UU.)**
   - **URL:** `https://www.dentrixascend.com/dental-solutions/marketing-and-patient-experience/dentrix-patient-engage-suite/`
   - **Qué afirmaba el informe de la IA:** El agente tomó como hecho comprobado que el sistema "reduce el ausentismo en un 23%".
   - **Qué se encontró y corrigió:** Esa cifra es un reclamo de marketing en la landing page, no un dato auditable general. Se instruyó al agente para clasificarlo estrictamente como "afirmación del proveedor" en la celda de automatización.

5. **OdontoClinIA (AR)**
   - **URL:** `https://www.clinia.com.ar/odontologia`
   - **Qué afirmaba el informe de la IA:** El agente asumió que por tener integración con ARCA, también poseía "cobro con Mercado Pago integrado a la reserva".
   - **Qué se encontró y corrigió:** La lectura detallada de la web y los módulos indica caja en múltiples monedas y verificación PUCO, pero no menciona Mercado Pago. Se usó *Ajustar* para consignar Mercado Pago como "No evidenciado", evitando asumir integraciones no documentadas.