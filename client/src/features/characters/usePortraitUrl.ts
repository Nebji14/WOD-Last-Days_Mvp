"use client";

/**
 * Adresse locale d'un portrait, chargé une seule fois par fenêtre.
 *
 * L'image passe par l'API, qui vérifie les droits et renouvelle la session au
 * besoin ; un simple `<img src>` échouerait dès que la session expire.
 */
import { useEffect, useState } from "react";

import { fetchBlob } from "@/shared/api/client";

const loaded = new Map<string, Promise<string>>();

function load(name: string): Promise<string> {
  const known = loaded.get(name);
  if (known !== undefined) {
    return known;
  }
  const pending = fetchBlob(`/api/portraits/${name}`).then((blob) => URL.createObjectURL(blob));
  loaded.set(name, pending);
  // Un échec n'est pas retenu : le prochain affichage réessaie.
  pending.catch(() => loaded.delete(name));
  return pending;
}

/** Retourne l'adresse à afficher, `null` sans portrait, pendant le chargement ou s'il a échoué. */
export function usePortraitUrl(name: string | null): string | null {
  const [image, setImage] = useState<{ name: string; url: string } | null>(null);

  useEffect(() => {
    if (name === null) {
      return;
    }
    let active = true;
    load(name).then(
      (url) => {
        if (active) {
          setImage({ name, url });
        }
      },
      (error: unknown) => {
        console.warn("Portrait indisponible", error);
      },
    );
    return () => {
      active = false;
    };
  }, [name]);

  return image !== null && image.name === name ? image.url : null;
}
