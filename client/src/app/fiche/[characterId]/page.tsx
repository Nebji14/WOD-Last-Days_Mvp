import { SheetScreen } from "@/features/sheet/components/SheetScreen";
import { EDIT_MODE_PARAM, EDIT_MODE_VALUE } from "@/shared/windows/detached";

/**
 * Fenêtre détachée de la fiche d'un personnage (écrans 05a, 05b, 05c).
 * Le paramètre `mode=modification` l'ouvre en mode modification (04a-I3).
 */
export default async function SheetPage(props: {
  readonly params: Promise<{ characterId: string }>;
  readonly searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { characterId } = await props.params;
  const query = await props.searchParams;
  return (
    <SheetScreen
      characterId={characterId}
      initialEditing={query[EDIT_MODE_PARAM] === EDIT_MODE_VALUE}
    />
  );
}
