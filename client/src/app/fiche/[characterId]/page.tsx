import { SheetScreen } from "@/features/sheet/components/SheetScreen";

/** Fenêtre détachée de la fiche d'un personnage (écrans 05a, 05b, 05c). */
export default async function SheetPage(props: {
  readonly params: Promise<{ characterId: string }>;
}) {
  const { characterId } = await props.params;
  return <SheetScreen characterId={characterId} />;
}
