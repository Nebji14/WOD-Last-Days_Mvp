import type { SearchParams } from "@/features/auth/googleReturn";
import { ProfileScreen } from "@/features/profile/components/ProfileScreen";
import { parseGoogleResult } from "@/features/profile/googleResult";

/** Fenêtre détachée du profil ; Google y ramène aussi après un rattachement. */
export default async function ProfilePage({
  searchParams,
}: {
  readonly searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  return <ProfileScreen googleResult={parseGoogleResult(params.google)} />;
}
