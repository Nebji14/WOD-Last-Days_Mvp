/** Méthodes de connexion du compte, lues une fois à l'ouverture du profil. */
import { useEffect, useState } from "react";

import { fetchLoginMethods, type LoginMethods } from "@/features/auth/api";

/**
 * Retourne les méthodes de connexion, `null` pendant la lecture ou si elle a
 * échoué : le profil reste alors utilisable, sans état affiché pour les méthodes.
 */
export function useLoginMethods(): LoginMethods | null {
  const [methods, setMethods] = useState<LoginMethods | null>(null);

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
  }, []);

  return methods;
}
