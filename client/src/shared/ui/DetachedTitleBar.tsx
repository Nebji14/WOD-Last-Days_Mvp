/**
 * Barre de titre des fenêtres détachées (profil, outils du MJ) : titre,
 * sous-titre et bouton qui ferme la fenêtre.
 */

interface DetachedTitleBarProps {
  readonly title: string;
  readonly subtitle: string;
  readonly closeLabel: string;
}

export function DetachedTitleBar({ title, subtitle, closeLabel }: DetachedTitleBarProps) {
  return (
    <header className="border-line bg-panel flex h-[60px] shrink-0 items-center justify-between gap-4 border-b px-4 sm:px-8">
      <div>
        <h1 className="font-display text-ink-bright text-[20px] font-bold tracking-[4px]">
          {title}
        </h1>
        <p className="text-ink-muted text-sm italic">{subtitle}</p>
      </div>
      <button
        type="button"
        onClick={() => window.close()}
        className="border-line-strong font-display text-ink flex h-[34px] cursor-pointer items-center gap-2.5 rounded-xs border px-3.5 text-[11px] font-bold tracking-[2.5px] hover:brightness-125"
      >
        {closeLabel}
        <span aria-hidden="true">✕</span>
      </button>
    </header>
  );
}
