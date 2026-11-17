/** Libellés français du profil du joueur (écran 09). */
export const frProfile = {
  profile: {
    windowTitle: "PROFIL",
    subtitle: "Ton compte et tes personnages",
    subtitleGm: "Ton compte",
    close: "FERMER",
    loading: "Ouverture du profil…",
    status: {
      player: "En ligne · joueur",
      gm: "En ligne · Maître du jeu",
    },
    account: {
      title: "MON COMPTE",
      displayName: "Nom affiché",
      username: "Nom d'utilisateur",
      state: "État du compte",
      active: "Actif",
    },
    methods: {
      title: "MÉTHODES DE CONNEXION",
      password: "Identifiant + mot de passe",
      google: "Google",
      enabled: "active",
      notLinked: "non rattaché",
    },
    editInfo: "MODIFIER MES INFORMATIONS",
    editInfoLater: "Modification du compte et des méthodes de connexion : après le MVP (US-004).",
    characters: {
      title: "MES PERSONNAGES · {count}",
      create: "+  CRÉER UN PERSONNAGE",
      empty: "Tu n'as encore aucun personnage. Crée ton chasseur pour rejoindre la table.",
      atTable: "À LA TABLE",
      play: "JOUER CE PERSONNAGE",
      open: "OUVRIR LA FICHE",
      delete: "SUPPRIMER",
      deleteLabel: "Supprimer {name}",
      deleteTitle: "SUPPRIMER LE PERSONNAGE",
      deleteQuestion:
        "Supprimer définitivement « {name} » ? Sa fiche, ses formes et ses notes seront effacées. Cette action est irréversible.",
      deleteHint: "Supprimer un personnage demande toujours une confirmation (US-010).",
      mainForm: "principale",
      oneForm: "1 forme : {names}",
      manyForms: "{count} formes : {names}",
    },
  },
} as const;
