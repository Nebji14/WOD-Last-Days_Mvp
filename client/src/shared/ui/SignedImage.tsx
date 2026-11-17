/**
 * Image lue par un lien signé du stockage privé (US-031).
 *
 * Le lien change à chaque relecture et expire : il ne passe pas par
 * l'optimiseur d'images de Next, d'où un élément `<img>` simple. La CSP
 * n'autorise que le domaine du stockage (`img-src`).
 */

interface SignedImageProps {
  readonly url: string | null;
  /** Texte de remplacement ; vide pour une image décorative déjà nommée à côté. */
  readonly alt: string;
  readonly className?: string;
}

export function SignedImage({ url, alt, className = "" }: SignedImageProps) {
  if (url === null) {
    return <span aria-hidden="true" className={`bg-field block ${className}`} />;
  }
  return (
    // eslint-disable-next-line @next/next/no-img-element -- lien signé externe, voir l'en-tête
    <img src={url} alt={alt} draggable={false} className={className} />
  );
}
