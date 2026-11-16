/**
 * Libellés français de l'interface.
 *
 * Aucun texte n'est écrit en dur dans les composants : ils passent tous par ce
 * fichier, ce qui prépare la traduction anglaise (CDC 6.1).
 */
export const fr = {
  app: {
    title: "Hunter · Last Days",
    description: "Table de jeu de la campagne Last Days.",
    game: "HUNTER",
    campaign: "LAST DAYS",
  },
  errors: {
    validation_error: "Certaines informations saisies sont invalides.",
    invalid_credentials: "Identifiant ou mot de passe incorrect.",
    not_authenticated: "Ta session a expiré. Reconnecte-toi.",
    forbidden: "Tu n'as pas le droit de faire cette action.",
    forbidden_origin: "Requête refusée.",
    wrong_portal_gm: "Je sais que ça te manque… mais retourne à tes responsabilités.",
    wrong_portal_player:
      "Tu n'es pas sur la bonne page, petit joueur. Cette porte-ci est réservée au maître du jeu.",
    username_taken: "Ce nom de chasseur est déjà pris.",
    username_invalid:
      "Le nom doit contenir de 3 à 24 caractères : lettres sans accent, chiffres, point, tiret.",
    password_mismatch: "Les deux mots de passe sont différents.",
    password_too_weak: "Le mot de passe ne respecte pas les règles de sécurité.",
    rate_limited: "Trop de tentatives. Patiente quelques minutes avant de réessayer.",
    not_found: "Élément introuvable.",
    service_unavailable: "Le service est momentanément indisponible. Réessaie dans un instant.",
    internal_error: "Une erreur est survenue. Réessaie dans un instant.",
    network_error: "Connexion perdue. Vérifie ta connexion, puis réessaie.",
  },
  passwordRules: {
    min_length: "Au moins 10 caractères.",
    max_length: "Pas plus de 72 caractères.",
    letter: "Au moins une lettre.",
    digit: "Au moins un chiffre.",
  },
} as const;
