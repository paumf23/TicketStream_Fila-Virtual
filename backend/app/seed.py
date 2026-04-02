

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

PAYMENT_METHODS = ["card", "wallet"]
PAYMENT_PROVIDERS = {
    "card": ["visa", "mastercard", "amex"],
    "wallet": ["mercadopago", "modo"]
}

EXIT_REASONS = ["purchased", "expired", "abandoned", "disconnected"]


# ─── Eventos de ejemplo ──────────────────────────────────────────────────────

SEED_EVENTS = [
    {
        "name": "Turismo Carretera: Gran Premio RUS Agro — Rafaela",
        "description": "El Autódromo de Rafaela, el 'Templo de la Velocidad', recibe al Turismo Carretera para una de las fechas más esperadas del calendario. Viví la adrenalina de los motores a más de 250 km/h en el óvalo más rápido de Sudamérica. Sentí el rugir de los Ford, Chevrolet, Dodge y Torino mientras los mejores pilotos del país se baten a duelo en las chicanas. Una experiencia única para los amantes de los fierros, con un ambiente de fiesta en las tribunas y toda la pasión del automovilismo nacional. ¡No te pierdas el Gran Premio RUS Agro en la mítica Rafaela!",
        "image_url": "http://localhost:3000/images/events/tc_rafaela.png",
        "total_capacity": 45000,
        "price": 35000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Deportes",
        "rating": 9.4,
        "rating_label": "VELOCIDAD PURA",
        "event_date": "2026-06-19"
    },
    {
        "name": "Superclásico: River Plate vs Boca Juniors",
        "description": "El evento deportivo más intenso de la región se juega en el Estadio Monumental. Mucho más que un partido de fútbol, el Superclásico es una batalla de orgullo, pasión y herencia. Viví la adrenalina de las tribunas colmadas, el color de los recibimientos y el duelo táctico entre los dos gigantes del fútbol argentino por el Torneo Liga Profesional 2026. Asegurá tu lugar en la historia y presenciá un encuentro que paraliza al país y atrae la mirada de todo el mundo. ¡Sentí el rugir del Monumental en cada jugada!",
        "image_url": "http://localhost:3000/images/events/river_boca.png",
        "total_capacity": 72000,
        "price": 70000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Deportes",
        "rating": 9.5,
        "rating_label": "PASIÓN PURA"
    },
    {
        "name": "Lollapalooza Argentina 2026",
        "description": "El festival más importante de Argentina regresa al Hipódromo de San Isidro para tres jornadas inolvidables. Con más de 100 artistas distribuidos en múltiples escenarios, Kidzapalooza, una propuesta gastronómica de primer nivel y espacios de arte inmersivo, el Lolla es mucho más que música; es un estilo de vida. Vení a disfrutar de tus bandas favoritas bajo el sol y a descubrir los nuevos talentos que están marcando tendencia en todo el mundo. ¡Tres días de pura vibra festivalera te esperan!",
        "image_url": "http://localhost:3000/images/events/lollapalooza.jpeg",
        "total_capacity": 5000,
        "price": 110000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Música",
        "rating": 9.2,
        "rating_label": "FESTIVAL DEL AÑO"
    },
    {
        "name": "Experiencia Queen - Greatest Hits",
        "description": "EXPERIENCIA QUEEN llega con su espectacular Greatest Hits Tour 2026. El show promete llevar al público a revivir los grandes éxitos de Queen en una única noche, transportándolos a los icónicos conciertos de la banda de manera fiel y deslumbrante.\n\nEste espectáculo, que recrea a la perfección tanto la música como la escenografía de los conciertos de Queen, representan con notable exactitud a cada uno de los miembros originales del grupo. Con vestuarios auténticos y el uso de instrumentos originales, el espectáculo ofrece una experiencia única para los fanáticos de todas las edades.\n\nEl repertorio incluye himnos inolvidables como “Bohemian Rhapsody”, “Love of My Life”, “Somebody to Love”, “Radio Ga Ga”, “I Want to Break Free” y “We Are the Champions”, entre otros, haciendo de cada función una verdadera fiesta de emociones. EXPERIENCIA QUEEN se convierte en una opción ideal para disfrutar en familia de la música de una de las bandas más legendarias de todos los tiempos.",
        "image_url": "http://localhost:3000/images/events/queen.png",
        "total_capacity": 5000,
        "price": 95000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Música",
        "rating": 9.7,
        "rating_label": "TRIBUTO LEGENDARIO"
    },
    {
        "name": "No me acuerdo las cosas",
        "description": "Olvidarse todo, envejecer y otros síntomas de la edad. Una obra teatral que explora la memoria y los vínculos familiares con humor y melancolía. Protagonizada por un elenco estelar, esta pieza invita a reflexionar sobre lo que elegimos recordar y lo que el tiempo intenta borrar.\n\nUna comedia dramática de Julieta Otero con dirección de Dalia Gutmann que ha conquistado a la crítica y al público por su honestidad y calidez. Perfecta para quienes buscan una historia profunda que hable sobre la vida cotidiana con una sonrisa.",
        "image_url": "http://localhost:3000/images/events/no_me_acuerdo.jpg",
        "total_capacity": 300,
        "price": 48000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Teatro",
        "rating": 8.9,
        "rating_label": "CONMOVEDORA"
    },
    {
        "name": "Comic Con Argentina 2026",
        "description": "La convención de cultura pop más grande del continente regresa más grande que nunca. Comic Con Argentina 2026 te trae paneles exclusivos con invitados internacionales del cine y la televisión, stands de cómics únicos, coleccionables de edición limitada, un área de gaming masiva y el mejor concurso de cosplay de la región. Sumergite en un paraíso para los fanáticos donde cada rincón ofrece una nueva sorpresa sobre tus universos favoritos de Marvel, DC, Star Wars, Anime y mucho más. ¡Viví tu pasión al máximo!",
        "image_url": "http://localhost:3000/images/events/comic_con.png",
        "event_date": "2026-12-05",
        "total_capacity": 15000,
        "price": 105000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Especiales",
        "rating": 9.0,
        "rating_label": "EL PARAÍSO GEEK"
    },
    {
        "name": "Cirque du Soleil: Kurios",
        "description": "Adéntrate en el 'Gabinete de Curiosidades' de un inventor ambicioso que desafía las leyes del tiempo y el espacio. Kurios es una de las producciones más aclamadas del Cirque du Soleil, donde lo invisible cobra vida y la realidad se reinventa a través de acrobacias imposibles, música envolvente y un despliegue visual steampunk asombroso. Una experiencia inmersiva que te transportará a un mundo donde todo es posible si te atreves a mirar más allá. ¡Bienvenido al universo Kurios!",
        "image_url": "http://localhost:3000/images/events/cirque_kurios.jpg",
        "total_capacity": 45000,
        "price": 100000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Especiales",
        "rating": 9.8,
        "rating_label": "MAGIA TOTAL"
    },
    {
        "name": "Por el placer de volver a verla",
        "description": "Por el placer de volver a verla sigue a un prestigioso autor y director teatral (Miguel Ángel Solá) que decide emprender un viaje emocional hacia su pasado para encontrar respuestas esenciales sobre su vida. Como un \"arqueólogo de la memoria\", el protagonista se despoja de lo superficial frente al público para reconstruir su historia personal y artística a través del reencuentro con la figura de una mujer única e irrepetible (Mercedes Funes), quien guarda las claves de su identidad.",
        "image_url": "http://localhost:3000/images/events/placer_volver.png",
        "total_capacity": 500,
        "price": 52000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Teatro",
        "rating": 10.0,
        "rating_label": "EXCELENTE"
    },
    {
        "name": "El Lago de los Cisnes",
        "description": "La inmortal obra maestra de Tchaikovsky, El Lago de los Cisnes, cobra una nueva y vibrante vida de la mano de una compañía de ballet de primer nivel. Esta puesta en escena transforma el drama clásico de amor y tragedia en un espectáculo donde la elegancia, la técnica y la expresión corporal alcanzan su máximo esplendor.\n\nA través de una coreografía fiel al lenguaje del ballet clásico, un elenco de bailarines de élite reinterpreta esta historia legendaria con gracia y precisión. El resultado es una puesta en escena emocionante que mantiene la esencia del clásico original mientras deslumbra con vestuarios exquisitos, una iluminación envolvente y la magia atemporal de la danza.",
        "image_url": "http://localhost:3000/images/events/lago_cisnes.jpeg",
        "total_capacity": 1200,
        "price": 50000.00,
        "currency": "ARS",
        "status": "active",
        "category": "Teatro",
        "rating": 9.8,
        "rating_label": "IMPERDIBLE"
    }
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
        print("🧹 Limpiando base de datos...")
        from sqlalchemy import text
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        await db.execute(text("TRUNCATE TABLE payments;"))
        await db.execute(text("TRUNCATE TABLE tickets;"))
        await db.execute(text("TRUNCATE TABLE queue_history;"))
        await db.execute(text("TRUNCATE TABLE buyers;"))
        await db.execute(text("TRUNCATE TABLE events;"))
        await db.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
        await db.commit()

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
                event_date=event_data.get("event_date") or (now + timedelta(days=30 + i * 15)),
                sale_start=now - timedelta(days=7),
                sale_end=now + timedelta(days=25 + i * 15),
                status=event_data.get("status", "active"),
                category=event_data.get("category"),
                rating=event_data.get("rating"),
                rating_label=event_data.get("rating_label"),
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

                method = random.choice(PAYMENT_METHODS)
                provider = random.choice(PAYMENT_PROVIDERS[method])

                payment = Payment(
                    id=str(uuid4()),
                    ticket_id=ticket.id,
                    amount=float(event.price),
                    payment_method=method,
                    payment_provider=provider,
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
