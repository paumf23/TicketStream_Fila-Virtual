"use client";

import { useEffect } from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Aquí podrías enviar el error a un servicio de monitoreo (Sentry, Datadog, etc.)
    console.error("Error capturado por el Boundary:", error);
  }, [error]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        minHeight: "100vh",
        backgroundColor: "#000",
        color: "#fff",
        padding: "20px",
        fontFamily: "system-ui, -apple-system, sans-serif",
        textAlign: "center",
      }}
    >
      <div
        style={{
          background: "rgba(255, 50, 50, 0.1)",
          border: "1px solid rgba(255, 50, 50, 0.3)",
          padding: "40px",
          borderRadius: "16px",
          backdropFilter: "blur(10px)",
          maxWidth: "500px",
        }}
      >
        <span style={{ fontSize: "48px", display: "block", marginBottom: "20px" }}>
          ⚠️
        </span>
        <h2 style={{ fontSize: "24px", marginBottom: "15px", fontWeight: "600" }}>
          ¡Ups! Algo se rompió en la interfaz.
        </h2>
        <p style={{ color: "#aaa", marginBottom: "30px", lineHeight: "1.5" }}>
          Hemos atrapado una caída inesperada para evitar que pierdas tu progreso.
          <br />
          <br />
          <span style={{ fontSize: "12px", fontFamily: "monospace", color: "#ff8888" }}>
            Detalle técnico: {error.message}
          </span>
        </p>

        <button
          onClick={() => reset()}
          style={{
            background: "#fff",
            color: "#000",
            border: "none",
            padding: "12px 24px",
            borderRadius: "8px",
            fontSize: "16px",
            fontWeight: "bold",
            cursor: "pointer",
            transition: "all 0.2s ease",
          }}
          onMouseOver={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
          onMouseOut={(e) => (e.currentTarget.style.transform = "scale(1)")}
        >
          Intentar de nuevo
        </button>
      </div>
    </div>
  );
}
