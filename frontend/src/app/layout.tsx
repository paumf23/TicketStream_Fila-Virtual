import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/common/Header/Header";
import Footer from "@/components/common/Footer/Footer";

// Metadata: define el título y descripción de la pestaña del navegador
export const metadata: Metadata = {
  title: "TicketStream — Plataforma de Entradas",
  description:
    "Gestión inteligente de filas virtuales para eventos masivos.",
};

// Layout raíz: envuelve TODAS las páginas.
// "children" es la página actual que se renderiza dentro del layout.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body style={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
        <Header />
        <main style={{ flex: 1, padding: "32px" }}>{children}</main>
        <Footer />
      </body>
    </html>
  );
}
