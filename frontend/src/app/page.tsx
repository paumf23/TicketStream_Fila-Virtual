import { getActiveEvents } from "@/lib/api";
import HomeClient from "@/components/HomeClient/HomeClient";
import styles from "./page.module.css";

export const dynamic = "force-dynamic";

export default async function HomePage({ 
  searchParams 
}: { 
  searchParams: Promise<{ category?: string }> 
}) {
  const { category } = await searchParams;

  try {
    const data = await getActiveEvents(category);
    
    return (
      <div className={styles.container}>
        <HomeClient 
          initialEvents={data.events} 
          category={category} 
        />

        {/* Footer de Métodos de Pago */}
        {!category && (
          <section className={styles.paymentSection}>
            <div className={styles.paymentCard}>
              <div className={styles.paymentHeader}>
                <span className={styles.paymentIcon}>💳</span>
                <h2 className={styles.paymentTitle}>Métodos de Pago</h2>
              </div>
              <p className={styles.paymentText}>
                Si tenés alguna duda con el pago o querés cancelar tu compra, por favor contactá primero a nuestro equipo de <strong>AYUDA</strong>.
                Evitá iniciar un desconocimiento en tu Banco o Tarjeta: este tipo de gestiones puede generar bloqueos automáticos por actividad sospechosa y afectar futuras compras. Estamos para ayudarte y resolver cualquier inconveniente rápidamente.
              </p>
              <div className={styles.paymentLogos}>
                <img src="/images/payments/visa.png" alt="Visa" className={styles.brandLogo} />
                <img src="/images/payments/Modo.png" alt="MODO" className={styles.brandLogo} />
                <img src="/images/payments/Amex.png" alt="AMEX" className={styles.brandLogo} />
                <img src="/images/payments/mastercard.png" alt="Mastercard" className={styles.brandLogo} />
                <img src="/images/payments/mercadopago.png" alt="Mercado Pago" className={styles.brandLogo} />
              </div>
            </div>
          </section>
        )}
      </div>
    );
  } catch (error) {
    console.error("Error loading events:", error);
    return (
      <div className={styles.container}>
        <div style={{ textAlign: "center", padding: "100px 20px" }}>
          <h1 className={styles.title}>Error</h1>
          <p className={styles.error}>
            No se pudieron cargar los eventos. Verificá que el backend esté corriendo.
          </p>
        </div>
      </div>
    );
  }
}
