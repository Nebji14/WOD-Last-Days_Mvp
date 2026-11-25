/** Grande photo du profil, avec son bouton ; les initiales quand elle n'est pas modifiable. */
import type { Account } from "@/features/auth/api";
import { PortraitPicker } from "@/features/characters/components/PortraitPicker";
import type { PortraitFiles } from "@/features/characters/portrait";
import { initials } from "@/features/table/seatLayout";
import { labels } from "@/shared/i18n";

export interface ProfilePictureSource {
  readonly portrait: string | null;
  /** Nom du personnage joué, ou du MJ. */
  readonly name: string;
  readonly busy: boolean;
  readonly onSave: (files: PortraitFiles) => void;
  readonly onRemove: () => void;
}

interface ProfilePictureProps {
  readonly account: Account;
  readonly source: ProfilePictureSource | null;
}

export function ProfilePicture({ account, source }: ProfilePictureProps) {
  if (source !== null) {
    return (
      <PortraitPicker
        {...source}
        className="ring-gold size-28 text-4xl shadow-[0_0_24px_rgb(201_176_106/0.2)] ring-2"
      />
    );
  }
  return (
    <span
      aria-hidden="true"
      className="border-gold bg-field font-display text-gold flex size-28 items-center justify-center rounded-full border-2 text-5xl font-bold shadow-[0_0_24px_rgb(201_176_106/0.2)]"
    >
      {account.role === "gm" ? labels.table.gm.initials : initials(account.displayName).slice(0, 1)}
    </span>
  );
}
