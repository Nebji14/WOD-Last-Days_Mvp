/** Méthodes de connexion du compte, relues après chaque changement. */
import { useCallback, useEffect, useState } from "react";

import { fetchLoginMethods, type LoginMethods } from "@/features/auth/api";

export interface LoginMethodsState {
  /**
   * `null` pendant la lecture ou si elle a échoué : le profil reste alors
   * utilisable, sans état affiché pour les méthodes.
   */
  readonly methods: LoginMethods | null;
  readonly refresh: () => void;
}

export function useLoginMethods(): LoginMethodsState {
  const [methods, setMethods] = useState<LoginMethods | null>(null);
  const [version, setVersion] = useState(0);

  useEffect(() => {
    let active = true;
    fetchLoginMethods().then(
      (value) => {
        if (active) {
          setMethods(value);
        }
      },
      (error: unknown) => {
        console.warn("Méthodes de connexion indisponibles", error);
      },
    );
    return () => {
      active = false;
    };
  }, [version]);

  const refresh = useCallback(() => setVersion((current) => current + 1), []);
  return { methods, refresh };
}
