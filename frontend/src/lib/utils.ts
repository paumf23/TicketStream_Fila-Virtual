/**
 * Formatea un precio numérico a moneda local (es-AR).
 */
export function formatPrice(price: number, currency: string): string {
  return new Intl.NumberFormat("es-AR", {
    style: "currency",
    currency,
    minimumFractionDigits: 0,
  }).format(price);
}

/**
 * Formatea una fecha ISO a un formato legible (es-AR).
 */
export function formatDate(dateStr: string): string {
  const utcDateStr = dateStr.endsWith("Z") ? dateStr : `${dateStr}Z`;
  return new Date(utcDateStr).toLocaleDateString("es-AR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
