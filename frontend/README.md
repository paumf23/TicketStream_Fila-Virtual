# ⚛️ TicketStream — Frontend

Interfaz de usuario del sistema de fila virtual **TicketStream**, construida con **Next.js 16**, **React 19** y **TypeScript**. Consume la API REST del backend y se conecta por WebSocket para recibir actualizaciones en tiempo real.

---

## 🛠️ Tech Stack

| Tecnología | Versión | Rol |
|---|---|---|
| **Next.js** | 16.2 | Framework React con App Router y SSR |
| **React** | 19.2 | Librería de UI — componentes y hooks |
| **TypeScript** | 5.x | Tipado estático en todo el proyecto |
| **CSS Modules** | — | Estilos encapsulados por componente (sin librerías externas) |

> El frontend **no usa librerías de UI externas** (como Tailwind, Material UI, etc.). Todos los estilos están escritos manualmente con CSS Modules, lo que permite control total sobre el diseño y evita dependencias innecesarias.

---

## 📁 Estructura del Proyecto

```
frontend/
├── public/                         # Archivos estáticos (favicon, imágenes)
├── src/
│   ├── app/                        # App Router — Páginas (Next.js)
│   │   ├── layout.tsx              # Layout raíz (Header + Footer global)
│   │   ├── page.tsx                # Home — Landing page con eventos activos
│   │   ├── globals.css             # Variables CSS globales y reset de estilos
│   │   ├── page.module.css         # Estilos de la landing page
│   │   ├── evento/[eventId]/       # Detalle del evento
│   │   ├── cola/[eventId]/         # Sala de espera (fila virtual en tiempo real)
│   │   ├── compra/[eventId]/       # Formulario de compra (cuando llega el turno)
│   │   ├── ticket/[ticketId]/      # Confirmación del ticket comprado
│   │   └── nosotros/              # Página informativa
│   │
│   ├── components/                 # Componentes reutilizables
│   │   ├── common/                 # Componentes globales
│   │   │   ├── Header/             # Navbar
│   │   │   ├── Footer/             # Footer
│   │   │   ├── Button/             # Botón reutilizable
│   │   │   ├── Loader/             # Spinner de carga
│   │   │   └── ConfettiCanvas/     # Animación de confeti (confirmación de compra)
│   │   ├── EventCard/              # Tarjeta de evento en la landing page
│   │   ├── EventHero/              # Hero section del detalle del evento
│   │   ├── EventInfoCards/         # Tarjetas informativas (fecha, precio, capacidad)
│   │   ├── EnterQueueForm/         # Formulario para unirse a la fila
│   │   ├── QueueStatus/            # Visualización de la posición en la fila
│   │   ├── LiveStats/              # Estadísticas en tiempo real del evento
│   │   ├── TurnNotification/       # Notificación cuando llega el turno
│   │   ├── PurchaseForm/           # Formulario de datos del comprador y pago
│   │   ├── TicketConfirmation/     # Vista de ticket comprado exitosamente
│   │   ├── ParticleTunnel/         # Animación de loading con partículas
│   │   ├── HomeClient/             # Lógica client-side de la landing page
│   │   ├── SimulationHUD/          # Panel de control de la simulación estándar
│   │   └── SimulationDrawer/       # Drawer lateral para simulación avanzada
│   │
│   ├── lib/                        # Servicios y utilidades
│   │   ├── api.ts                  # Cliente HTTP — todas las llamadas al backend
│   │   ├── websocket.ts            # Hook useWebSocket — conexión en tiempo real
│   │   └── utils.ts                # Funciones utilitarias (formateo, helpers)
│   │
│   └── types/
│       └── index.ts                # Definición centralizada de tipos TypeScript
│
├── package.json                    # Dependencias y scripts
├── tsconfig.json                   # Configuración TypeScript
└── next.config.ts                  # Configuración Next.js
```

---

## 🔄 Flujo de Usuario

El frontend implementa un flujo lineal que guía al usuario desde la selección del evento hasta la obtención del ticket:

```
Landing Page → Detalle del Evento → Sala de Espera → Compra → Ticket Confirmado
     /           /evento/[id]        /cola/[id]      /compra/[id]   /ticket/[id]
```

| # | Página | Ruta | Descripción |
|---|---|---|---|
| 1 | **Home** | `/` | Landing page con listado de eventos activos filtrable por categoría |
| 2 | **Detalle del evento** | `/evento/[eventId]` | Información del evento, estadísticas y botón para entrar a la fila |
| 3 | **Sala de espera** | `/cola/[eventId]` | Fila virtual con posición en tiempo real, estadísticas en vivo y simulación |
| 4 | **Formulario de compra** | `/compra/[eventId]` | Datos del comprador y método de pago (solo accesible cuando llega el turno) |
| 5 | **Confirmación** | `/ticket/[ticketId]` | Ticket confirmado con código único y animación de confeti |
| 6 | **Nosotros** | `/nosotros` | Información sobre el proyecto |

---

## 🔌 Comunicación con el Backend

### Cliente HTTP (`lib/api.ts`)

Todas las llamadas HTTP al backend están centralizadas en `api.ts`. Cada función corresponde a un endpoint del backend FastAPI:

| Función | Endpoint | Uso |
|---|---|---|
| `getActiveEvents()` | `GET /api/events/active` | Landing page — cargar eventos |
| `getEvent(id)` | `GET /api/events/{id}` | Detalle del evento |
| `getEventStats(id)` | `GET /api/events/{id}/stats` | Estadísticas del evento |
| `enterQueue(data)` | `POST /api/queue/enter` | Unirse a la fila |
| `getQueuePosition(userId, eventId)` | `GET /api/queue/position` | Consultar posición |
| `purchaseTicket(data)` | `POST /api/tickets/purchase` | Comprar ticket |
| `getTicketDetail(id)` | `GET /api/tickets/{id}` | Ver ticket comprado |
| `simulateLoad(eventId, n)` | `POST /api/simulate/load` | Simulación estándar |
| `advancedSimulate(data)` | `POST /api/simulate/advanced` | Simulación avanzada |

La URL base del backend se configura con la variable de entorno `NEXT_PUBLIC_API_URL` (por defecto: `http://localhost:8000`).

### WebSocket (`lib/websocket.ts`)

El hook `useWebSocket(eventId)` gestiona la conexión en tiempo real con el backend:

- Se conecta a `ws://localhost:8000/ws/{eventId}` cuando el usuario entra a la sala de espera.
- Recibe mensajes del worker (posición actualizada, notificación de turno, estadísticas en vivo).
- Si la conexión se cae, **reconecta automáticamente** después de 3 segundos.
- Se desconecta limpiamente cuando el usuario navega a otra página.

La URL base del WebSocket se configura con `NEXT_PUBLIC_WS_URL` (por defecto: `ws://localhost:8000`).

---

## 🧩 Componentes Principales

| Componente | Función | Página |
|---|---|---|
| `EventCard` | Tarjeta de evento con imagen, nombre, precio y fecha | Home |
| `EventHero` | Hero section con imagen de fondo y datos principales | Detalle del evento |
| `EventInfoCards` | Tarjetas informativas: fecha, precio, capacidad | Detalle del evento |
| `EnterQueueForm` | Formulario para ingresar nombre y unirse a la fila | Detalle del evento |
| `QueueStatus` | Barra de progreso con posición actual en la fila | Sala de espera |
| `LiveStats` | Métricas en vivo del evento (usuarios en fila, tickets vendidos, etc.) | Sala de espera |
| `TurnNotification` | Notificación y redirección cuando llega el turno del usuario | Sala de espera |
| `PurchaseForm` | Formulario de datos personales y selección de pago | Compra |
| `TicketConfirmation` | Vista del ticket confirmado con código único | Confirmación |
| `ParticleTunnel` | Animación de partículas durante la carga de la sala de espera | Sala de espera |
| `SimulationHUD` | Panel de control para la simulación estándar | Sala de espera |
| `SimulationDrawer` | Drawer lateral con parámetros configurables para simulación avanzada | Sala de espera |

### Simulación desde la interfaz

La sala de espera (`/cola/[eventId]`) incluye dos modos de simulación:

- **SimulationHUD** — Permite iniciar una simulación rápida con un botón. Inyecta usuarios ficticios en la fila con configuración por defecto.
- **SimulationDrawer** — Drawer lateral que se abre desde el HUD y permite al usuario configurar una simulación avanzada con los siguientes parámetros: población total (hasta 10.000 usuarios), velocidad de procesamiento (usuarios/minuto), tasa de abandono (0-100%), capacidad del evento, y la posición del usuario real dentro de la fila simulada.

Los componentes llaman a `simulateLoad()` y `advancedSimulate()` respectivamente desde `lib/api.ts`, y el procesamiento corre en el Worker del backend.

---

## 🚀 Levantar el Frontend

### Requisitos

- [Node.js 18+](https://nodejs.org/)
- Backend corriendo (ver README principal del proyecto)

### Instalación y ejecución

```bash
cd frontend
npm install
npm run dev
```

La aplicación estará disponible en **http://localhost:3000**.

### Scripts disponibles

| Script | Comando | Descripción |
|---|---|---|
| `dev` | `npm run dev` | Servidor de desarrollo con hot-reload |
| `build` | `npm run build` | Compilar para producción |
| `start` | `npm run start` | Servir el build de producción |
| `lint` | `npm run lint` | Ejecutar ESLint para verificar calidad de código |

### Variables de entorno del frontend

| Variable | Descripción | Valor por defecto |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | URL base del backend (HTTP) | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | URL base del backend (WebSocket) | `ws://localhost:8000` |

> Estas variables solo necesitan cambiarse si el backend corre en un host o puerto diferente.

---

<p align="center">
  Parte del proyecto <strong>TicketStream</strong> — Sistema de fila virtual en tiempo real
</p>
