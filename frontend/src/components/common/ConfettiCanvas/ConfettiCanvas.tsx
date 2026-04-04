"use client";

import React, { useEffect, useRef, useCallback } from "react";

interface ConfettiPiece {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  rotation: number;
  rotationSpeed: number;
  color: string;
  opacity: number;
  gravity: number;
}

const CONFETTI_COLORS = [
  "#00B894", // --color-success
  "#00D9A3", // lighter variant
  "#009B7D", // darker variant
  "#55EFC4", // bright variant
  "#00CEC9", // secondary accent
];

export default function ConfettiCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const piecesRef = useRef<ConfettiPiece[]>([]);
  const animRef = useRef<number>(0);
  const burstCountRef = useRef(0);

  const createCornerBurst = useCallback(
    (originX: number, originY: number, targetX: number, targetY: number) => {
      const newPieces: ConfettiPiece[] = [];
      const baseAngle = Math.atan2(targetY - originY, targetX - originX);

      for (let i = 0; i < 60; i++) {
        const angle = baseAngle + (Math.random() - 0.5) * (Math.PI / 2);
        const speed = 6 + Math.random() * 10;
        newPieces.push({
          x: originX + (Math.random() - 0.5) * 40,
          y: originY + (Math.random() - 0.5) * 20,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          size: 8 + Math.random() * 6,
          rotation: Math.random() * 360,
          rotationSpeed: (Math.random() - 0.5) * 15,
          color:
            CONFETTI_COLORS[Math.floor(Math.random() * CONFETTI_COLORS.length)],
          opacity: 1,
          gravity: 0.08 + Math.random() * 0.06,
        });
      }
      piecesRef.current.push(...newPieces);
    },
    []
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", handleResize);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const leftX = 0;
    const rightX = canvas.width;
    const bottomY = canvas.height;

    function fireBurst() {
      createCornerBurst(leftX, bottomY, centerX, centerY);
      createCornerBurst(rightX, bottomY, centerX, centerY);
    }

    fireBurst();
    burstCountRef.current = 1;

    const burstInterval = setInterval(() => {
      burstCountRef.current += 1;
      fireBurst();
      if (burstCountRef.current >= 3) {
        clearInterval(burstInterval);
      }
    }, 1500);

    function animate() {
      const ctx = canvas!.getContext("2d");
      if (!ctx) return;

      ctx.clearRect(0, 0, canvas!.width, canvas!.height);

      const pieces = piecesRef.current;
      for (let i = pieces.length - 1; i >= 0; i--) {
        const p = pieces[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vy += p.gravity;
        p.vx *= 0.985;
        p.rotation += p.rotationSpeed;
        p.opacity -= 0.004;

        if (
          p.opacity <= 0 ||
          p.y > canvas!.height + 30 ||
          p.x < -30 ||
          p.x > canvas!.width + 30
        ) {
          pieces.splice(i, 1);
          continue;
        }

        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.globalAlpha = p.opacity;
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 3, p.size, p.size * 0.6);
        ctx.restore();
      }

      animRef.current = requestAnimationFrame(animate);
    }

    animRef.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animRef.current);
      clearInterval(burstInterval);
      window.removeEventListener("resize", handleResize);
    };
  }, [createCornerBurst]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        pointerEvents: "none",
        zIndex: 100,
      }}
    />
  );
}
