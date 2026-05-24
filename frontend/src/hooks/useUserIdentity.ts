import { useState, useEffect } from "react";

export function useUserIdentity(isSimMode: boolean, urlUserId: string | null) {
  const [userId, setUserId] = useState<string | null>(null);
  const [userName, setUserName] = useState<string>("");

  useEffect(() => {
    if (isSimMode && urlUserId) {
      setUserId(urlUserId);
      setUserName("User Simulador");
    } else {
      const storedId = localStorage.getItem("vq_user_id");
      const storedFirst = localStorage.getItem("vq_first_name") || "";
      const storedLast = localStorage.getItem("vq_last_name") || "";
      setUserId(storedId);
      setUserName(`${storedFirst} ${storedLast}`.trim());
    }
  }, [isSimMode, urlUserId]);

  return { userId, userName };
}
