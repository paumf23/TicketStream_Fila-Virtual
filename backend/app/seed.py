

import asyncio
import random
import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from app.database import AsyncSessionLocal, Base, engine
from app.models.buyer import Buyer
from app.models.event import Event
from app.models.payment import Payment
from app.models.queue_history import QueueHistory
from app.models.ticket import Ticket

FIRST_NAMES = [
    "Martín", "Lucía", "Santiago", "Valentina", "Mateo",
    "Sofía", "Benjamín", "Catalina", "Joaquín", "Emilia",
    "Tomás", "Isabella", "Agustín", "Camila", "Felipe",
    "Julieta", "Nicolás", "Florencia", "Thiago", "Renata",
    "Facundo", "Milagros", "Lautaro", "Candela", "Bautista",
    "Pilar", "Ignacio", "Rocío", "Manuel", "Abril",
    "Franco", "Martina", "Gonzalo", "Delfina", "Ramiro",
    "Morena", "Máximo", "Alma", "Salvador", "Luna",
    "Dante", "Bianca", "Bruno", "Jazmín", "Elías",
    "Mía", "Simón", "Olivia", "Ciro", "Emma",
]

LAST_NAMES = [
    "González", "Rodríguez", "Martínez", "López", "García",
    "Pérez", "Fernández", "Díaz", "Romero", "Alvarez",
    "Torres", "Ruiz", "Ramírez", "Flores", "Herrera",
    "Medina", "Castro", "Vargas", "Morales", "Gutiérrez",
    "Sánchez", "Ortiz", "Silva", "Molina", "Acosta",
    "Rojas", "Cabrera", "Núñez", "Peralta", "Figueroa",
    "Giménez", "Suárez", "Aguirre", "Domínguez", "Ríos",
    "Navarro", "Paz", "Córdoba", "Lucero", "Miranda",
    "Bustos", "Vera", "Sosa", "Luna", "Ledesma",
    "Ponce", "Campos", "Cáceres", "Ojeda", "Villalba",
]

EMAIL_DOMAINS = [
    "gmail.com", "hotmail.com", "yahoo.com.ar",
    "outlook.com", "live.com.ar",
]

PAYMENT_METHODS = ["credit_card", "debit_card", "mercado_pago"]

EXIT_REASONS = ["purchased", "expired", "abandoned", "disconnected"]


# ─── Eventos de ejemplo ──────────────────────────────────────────────────────

SEED_EVENTS = [
    {
        "name": "Lollapalooza Argentina 2026",
        "description": "Festival de música internacional con artistas de todo el mundo. 3 días de shows en vivo.",
        "image_url": "https://images.unsplash.com/photo-1459749411175-04bf5292ceea?w=800",
        "total_capacity": 5000,
        "price": 45000.00,
        "currency": "ARS",
    },
    {
        "name": "River Plate vs Boca Juniors - Superclásico",
        "description": "El superclásico del fútbol argentino en el Monumental. Torneo Liga Profesional 2026.",
        "image_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=800",
        "total_capacity": 72000,
        "price": 25000.00,
        "currency": "ARS",
    },
    {
        "name": "Coldplay - Music of the Spheres Tour",
        "description": "La banda británica vuelve a Buenos Aires con su gira mundial. Estadio River Plate.",
        "image_url": "https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=800",
        "total_capacity": 65000,
        "price": 55000.00,
        "currency": "ARS",
    },
    {
        "name": "Comic Con Argentina 2026",
        "description": "Convención de comics, anime, gaming y cultura pop. Paneles, cosplay y stands.",
        "image_url": "https://images.unsplash.com/photo-1608889175123-8ee362201f81?w=800",
        "total_capacity": 15000,
        "price": 12000.00,
        "currency": "ARS",
    },
]


def _generate_dni() -> str:
    return str(random.randint(20000000, 45000000))


def _generate_email(first_name: str, last_name: str) -> str:
    domain = random.choice(EMAIL_DOMAINS)
    num = random.randint(1, 999)
    name = first_name.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    surname = last_name.lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
    return f"{name}.{surname}{num}@{domain}"


def _generate_ticket_code() -> str:
    return f"VQ-{secrets.token_hex(6).upper()}"


def _generate_payment_reference() -> str:
    return f"PAY-{secrets.token_hex(8).upper()}"


async def seed_database():
    """Carga datos iniciales en la base de datos."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Verificar si ya hay datos
        from sqlalchemy import func, select
        result = await db.execute(select(func.count()).select_from(Event))
        count = result.scalar()
        if count > 0:
            print("⚠️  La base de datos ya tiene datos. Seed cancelado.")
            return

        print("🌱 Sembrando datos iniciales...")

        now = datetime.utcnow()
        events = []

        # ─── Crear eventos ────────────────────────────────────────────
        for i, event_data in enumerate(SEED_EVENTS):
            event = Event(
                id=str(uuid4()),
                name=event_data["name"],
                description=event_data["description"],
                image_url=event_data["image_url"],
                total_capacity=event_data["total_capacity"],
                remaining_capacity=event_data["total_capacity"],
                price=event_data["price"],
                currency=event_data["currency"],
                event_date=now + timedelta(days=30 + i * 15),
                sale_start=now - timedelta(days=7),
                sale_end=now + timedelta(days=25 + i * 15),
                status="active",
            )
            db.add(event)
            events.append(event)

        await db.flush()
        print(f"   ✅ {len(events)} eventos creados")

        # ─── Crear compradores, tickets, pagos y queue_history ────────
        total_buyers = 0
        total_tickets = 0
        total_payments = 0
        total_queue_records = 0

        for event in events:
            num_purchases = min(50, event.total_capacity // 100)
            num_queue_total = num_purchases + random.randint(20, 60)

            for _ in range(num_purchases):
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)

                buyer = Buyer(
                    id=str(uuid4()),
                    first_name=first_name,
                    last_name=last_name,
                    dni=_generate_dni(),
                    email=_generate_email(first_name, last_name),
                )
                db.add(buyer)
                await db.flush()

                ticket = Ticket(
                    id=str(uuid4()),
                    buyer_id=buyer.id,
                    event_id=event.id,
                    ticket_code=_generate_ticket_code(),
                    price_paid=float(event.price),
                    status="confirmed",
                )
                db.add(ticket)
                await db.flush()

                payment = Payment(
                    id=str(uuid4()),
                    ticket_id=ticket.id,
                    amount=float(event.price),
                    payment_method=random.choice(PAYMENT_METHODS),
                    status="completed",
                    payment_reference=_generate_payment_reference(),
                )
                db.add(payment)


                entered = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
                wait_seconds = random.randint(30, 600)
                queue_record = QueueHistory(
                    user_id=str(uuid4()),
                    event_id=event.id,
                    initial_position=random.randint(1, 500),
                    entered_at=entered,
                    allowed_at=entered + timedelta(seconds=wait_seconds),
                    exited_at=entered + timedelta(seconds=wait_seconds + random.randint(10, 120)),
                    exit_reason="purchased",
                    wait_time_seconds=wait_seconds,
                )
                db.add(queue_record)

                total_buyers += 1
                total_tickets += 1
                total_payments += 1
                total_queue_records += 1


            event.remaining_capacity -= num_purchases


            non_purchase_count = num_queue_total - num_purchases
            for _ in range(non_purchase_count):
                exit_reason = random.choice(["expired", "abandoned", "disconnected"])
                entered = now - timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
                wait_seconds = random.randint(10, 900)

                queue_record = QueueHistory(
                    user_id=f"sim-{uuid4().hex[:12]}",
                    event_id=event.id,
                    initial_position=random.randint(1, 1000),
                    entered_at=entered,
                    allowed_at=entered + timedelta(seconds=wait_seconds) if exit_reason != "disconnected" else None,
                    exited_at=entered + timedelta(seconds=wait_seconds + random.randint(5, 300)),
                    exit_reason=exit_reason,
                    wait_time_seconds=wait_seconds,
                )
                db.add(queue_record)
                total_queue_records += 1

        await db.commit()

        print(f"   ✅ {total_buyers} compradores creados")
        print(f"   ✅ {total_tickets} tickets vendidos")
        print(f"   ✅ {total_payments} pagos registrados")
        print(f"   ✅ {total_queue_records} registros de cola creados")
        print("🎉 Seed completado exitosamente!")


if __name__ == "__main__":
    asyncio.run(seed_database())
