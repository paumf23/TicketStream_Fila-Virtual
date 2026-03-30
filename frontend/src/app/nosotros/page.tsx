import Link from "next/link";
import styles from "./page.module.css";

export default function NosotrosPage() {
  return (
    <div className={styles.container}>
      <header className={styles.hero}>
        <div className={styles.logoWrapper}>
          <svg width="60" height="60" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="10" width="32" height="20" rx="4" stroke="url(#tech-grad-big)" strokeWidth="3" />
            <circle cx="20" cy="20" r="4" fill="url(#tech-grad-big)" />
            <path d="M4 20H12" stroke="url(#tech-grad-big)" strokeWidth="3" strokeLinecap="round" />
            <path d="M28 20H36" stroke="url(#tech-grad-big)" strokeWidth="3" strokeLinecap="round" />
            <path d="M10 32C15 32 20 28 30 28" stroke="url(#tech-grad-big)" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
            <defs>
              <linearGradient id="tech-grad-big" x1="4" y1="10" x2="36" y2="30" gradientUnits="userSpaceOnUse">
                <stop stopColor="#0F4CFF" />
                <stop offset="1" stopColor="#00E0FF" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 className={styles.title}>Sobre TicketStream</h1>
      </header>

      <div className={styles.content}>
        <p>
          En <strong>TicketStream</strong>, transformamos la manera en que el mundo experimenta los eventos en vivo. 
          Nuestra plataforma utiliza algoritmos avanzados de procesamiento en tiempo real para gestionar 
          filas virtuales con transparencia absoluta. No solo vendemos entradas; garantizamos que cada 
          proceso de compra sea seguro, ordenado y eficiente, permitiendo que miles de usuarios accedan 
          a sus espectáculos favoritos sin fricciones ni comprometer la seguridad de sus datos.
        </p>
        <p>
          Internamente, nuestro software utiliza una arquitectura de alta disponibilidad que gestiona el 
          flujo de usuarios mediante bases de datos en memoria y colas de mensajes distribuidas. Esto nos 
          permite evitar "race conditions" (condiciones de carrera) y asegurar que cada ticket sea asignado 
          de forma única y justa según el estricto orden de llegada, garantizando integridad total incluso 
          bajo picos masivos de demanda. ¡Te invitamos a ser parte de la próxima gran experiencia con TicketStream!
        </p>
      </div>

      <div className={styles.buttonWrapper}>
        <Link href="/" className={styles.backButton}>
          ← Volver a Eventos
        </Link>
      </div>

    </div>
  );
}
