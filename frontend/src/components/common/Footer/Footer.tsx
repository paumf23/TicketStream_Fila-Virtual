import Link from "next/link";
import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.container}>
        <div className={styles.grid}>
          {/* Columna 1: Logo e Info */}
          <div className={styles.col}>
            <div className={styles.logo}>
              <div className={styles.logoIcon}>
                <svg width="28" height="28" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="4" y="10" width="32" height="20" rx="4" stroke="url(#tech-grad-footer)" strokeWidth="3" />
                  <circle cx="20" cy="20" r="4" fill="url(#tech-grad-footer)" />
                  <path d="M4 20H12" stroke="url(#tech-grad-footer)" strokeWidth="3" strokeLinecap="round" />
                  <path d="M28 20H36" stroke="url(#tech-grad-footer)" strokeWidth="3" strokeLinecap="round" />
                  <path d="M10 32C15 32 20 28 30 28" stroke="url(#tech-grad-footer)" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
                  <defs>
                    <linearGradient id="tech-grad-footer" x1="4" y1="10" x2="36" y2="30" gradientUnits="userSpaceOnUse">
                      <stop stopColor="#0F4CFF" />
                      <stop offset="1" stopColor="#00E0FF" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
              <span className={styles.logoText}>TicketStream</span>
            </div>

            <p className={styles.description}>
              La plataforma líder en gestión de filas virtuales para los eventos más grandes del país.
            </p>
          </div>

          {/* Columna 2: Categorías */}
          <div className={styles.col}>
            <h4 className={styles.colTitle}>Categorías</h4>
            <ul className={styles.links}>
              <li><Link href="/">Todos</Link></li>
              <li><Link href="/?category=Música">Música</Link></li>
              <li><Link href="/?category=Teatro">Teatro</Link></li>
              <li><Link href="/?category=Deportes">Deportes</Link></li>
              <li><Link href="/?category=Especiales">Especiales</Link></li>
            </ul>
          </div>


          {/* Columna 3: Información */}
          <div className={styles.col}>
            <h4 className={styles.colTitle}>Información</h4>
            <ul className={styles.links}>
              <li><Link href="/">Términos y Condiciones</Link></li>
              <li><Link href="/">Políticas de Privacidad</Link></li>
              <li><Link href="/">Defensa del Consumidor</Link></li>
              <li><Link href="/">Puntos de Venta</Link></li>
            </ul>
            <div className={styles.arrepentimiento}>
              <Link href="/" className={styles.arrepentimientoLink}>
                ↩ Desistir de la compra
              </Link>
              <p className={styles.arrepentimientoDesc}>
                Derecho de revocación (Art. 34, Ley 24.240)
              </p>
            </div>
          </div>

          {/* Columna 4: Badges */}
          <div className={styles.col}>
            <div className={styles.badges}>
              <div className={styles.badgePlaceholder}>
                <div className={styles.qrCode}>
                   {/* Simulación de Data Fiscal QR */}
                   <div className={styles.qrInner}></div>
                </div>
                <span className={styles.badgeLabel}>DATA FISCAL</span>
              </div>
              <div className={styles.badgePlaceholder}>
                <span className={styles.secureIcon}>🔒</span>
                <span className={styles.badgeLabel}>SECURE SSL</span>
              </div>
            </div>
          </div>
        </div>

        <div className={styles.bottomBar}>
          <p>© {new Date().getFullYear()} TicketStream. Todos los derechos reservados.</p>
          <div className={styles.socialLinks}>
            <span>IG</span>
            <span>TW</span>
            <span>FB</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
