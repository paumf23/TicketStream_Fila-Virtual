import { useState, useEffect } from "react";

export function useTurnTimer(isMyTurn: boolean, initialTTL: number = 0) {
  const [turnTTL, setTurnTTL] = useState<number>(initialTTL);

  useEffect(() => {
    if (initialTTL > 0) {
      setTurnTTL(initialTTL);
    }
  }, [initialTTL]);

  useEffect(() => {
    if (!isMyTurn || turnTTL <= 0) return;
    const interval = setInterval(() => {
      setTurnTTL((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [isMyTurn, turnTTL]);

  return { turnTTL, setTurnTTL };
}
