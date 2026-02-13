# C4 Nivel 1: Diagrama de Contexto del Sistema

## Descripción

Este diagrama muestra el sistema Virtual Queue desde el nivel más alto, identificando los usuarios y sistemas externos con los que interactúa.

## Diagrama

```mermaid
C4Context
    title Sistema Virtual Queue - Contexto

    Person(user, "Usuario", "Persona que quiere comprar entradas para un evento")
    Person(admin, "Administrador", "Gestiona eventos y monitorea el sistema")

    System(virtualQueue, "Virtual Queue System", "Sistema de cola virtual que gestiona la venta ordenada de tickets para eventos masivos")

    System_Ext(paymentGateway, "Pasarela de Pago", "Procesa pagos de tarjetas (simulado)")
    System_Ext(emailService, "Servicio de Email", "Envía confirmaciones de compra (futuro)")

    Rel(user, virtualQueue, "Entra a cola, espera turno, compra ticket", "HTTPS/WebSocket")
    Rel(admin, virtualQueue, "Crea eventos, ve métricas", "HTTPS")
    Rel(virtualQueue, paymentGateway, "Procesa pagos", "HTTPS/API")
    Rel(virtualQueue, emailService, "Envía confirmaciones", "SMTP")
```

## Actores

| Actor | Descripción | Interacción |
|-------|-------------|-------------|
| **Usuario** | Persona que desea comprar entradas | Entra a la cola, ve su posición en tiempo real, compra cuando es su turno |
| **Administrador** | Operador del sistema | Crea eventos, define capacidad, monitorea ventas |

## Sistemas Externos

| Sistema | Propósito | Estado |
|---------|-----------|--------|
| **Pasarela de Pago** | Procesar transacciones | Simulado en MVP |
| **Servicio de Email** | Enviar confirmaciones | Futuro |
