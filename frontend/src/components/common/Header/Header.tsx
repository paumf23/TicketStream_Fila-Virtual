import Link from "next/link";
import styles from "./Header.module.css";

export default function Header() {
  return (
    <header className={styles.header}>
      <Link href="/" className={styles.logo}>
        <div className={styles.logoIcon}>
          <svg width="32" height="32" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="10" width="32" height="20" rx="4" stroke="url(#tech-grad-header)" strokeWidth="3" />
            <circle cx="20" cy="20" r="4" fill="url(#tech-grad-header)" />
            <path d="M4 20H12" stroke="url(#tech-grad-header)" strokeWidth="3" strokeLinecap="round" />
            <path d="M28 20H36" stroke="url(#tech-grad-header)" strokeWidth="3" strokeLinecap="round" />
            <path d="M10 32C15 32 20 28 30 28" stroke="url(#tech-grad-header)" strokeWidth="2" strokeLinecap="round" opacity="0.4" />
            <defs>
              <linearGradient id="tech-grad-header" x1="4" y1="10" x2="36" y2="30" gradientUnits="userSpaceOnUse">
                <stop stopColor="#0F4CFF" />
                <stop offset="1" stopColor="#00E0FF" />
              </linearGradient>
            </defs>
          </svg>
        </div>
        <span className={styles.logoText}>TicketStream</span>
      </Link>
      
      <nav className={styles.nav}>
        <Link href="/nosotros" className={styles.navLink}>
          Nosotros
        </Link>
        <Link href="/" className={styles.navLink}>
          Eventos
        </Link>
        
        {/* Menú Desplegable de Categorías */}
        <div className={styles.dropdown}>
          <div className={styles.dropdownTrigger}>
            Filtrar por Categoría <span>▾</span>
          </div>
          <div className={styles.dropdownContent}>
            <Link href="/" className={styles.dropdownItem}>Todos</Link>
            <Link href="/?category=Música" className={styles.dropdownItem}>Música</Link>
            <Link href="/?category=Teatro" className={styles.dropdownItem}>Teatro</Link>
            <Link href="/?category=Deportes" className={styles.dropdownItem}>Deportes</Link>
            <Link href="/?category=Especiales" className={styles.dropdownItem}>Especiales</Link>
          </div>
        </div>
      </nav>
    </header>
  );
}
