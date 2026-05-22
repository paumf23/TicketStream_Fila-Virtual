# ═══════════════════════════════════════════════════════════════════════════════
# mock_data.py — Constantes y datos de prueba para la simulación
# ═══════════════════════════════════════════════════════════════════════════════

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
