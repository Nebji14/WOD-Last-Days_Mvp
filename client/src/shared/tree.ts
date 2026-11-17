/**
 * Arborescences : dossiers d'images (04b) et catégories de PNJ (04c, C07).
 *
 * Fonctions pures : le serveur reste seul garant de l'absence de cycle, le
 * client la reflète pour l'ergonomie.
 */

export interface TreeNode {
  readonly id: string;
  readonly name: string;
  readonly parentId: string | null;
}

/** Comparaison de noms sans tenir compte de la casse ni des accents. */
export function byName(left: { name: string }, right: { name: string }): number {
  return left.name.localeCompare(right.name, "fr", { sensitivity: "base" });
}

/** Enfants directs d'un nœud (`null` : racine), par nom. */
export function childrenOf<T extends TreeNode>(nodes: readonly T[], parentId: string | null): T[] {
  return nodes.filter((node) => node.parentId === parentId).sort(byName);
}

/** Chemin d'un nœud, de la racine jusqu'à lui ([Fil d'Ariane]). */
export function nodePath<T extends TreeNode>(nodes: readonly T[], nodeId: string | null): T[] {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  const path: T[] = [];
  let current = nodeId === null ? undefined : byId.get(nodeId);
  while (current !== undefined && !path.includes(current)) {
    path.unshift(current);
    current = current.parentId === null ? undefined : byId.get(current.parentId);
  }
  return path;
}

/** Indique si `candidateId` est `nodeId` lui-même ou l'un de ses descendants (04b-I10, C07). */
export function isWithin(
  nodes: readonly TreeNode[],
  nodeId: string,
  candidateId: string | null,
): boolean {
  return nodePath(nodes, candidateId).some((node) => node.id === nodeId);
}

/** Le nœud et tous ses descendants (Q04c-4 : une catégorie montre aussi ses sous-catégories). */
export function subtreeIds(nodes: readonly TreeNode[], nodeId: string): Set<string> {
  const ids = new Set([nodeId]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const node of nodes) {
      if (node.parentId !== null && ids.has(node.parentId) && !ids.has(node.id)) {
        ids.add(node.id);
        grew = true;
      }
    }
  }
  return ids;
}
