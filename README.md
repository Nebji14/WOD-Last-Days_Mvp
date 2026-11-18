# WOD · Last Days

Application web d’aide à la gestion d’une campagne de **Hunter: The Vigil**, dans l’univers du Monde des Ténèbres. Elle réunit les feuilles de personnage, les outils du maître du jeu et les échanges autour de la table dans une interface en français sur ordinateur.

## État du projet

**Au 18 novembre 2026, le MVP est développé**, selon le suivi du chef de projet. Le dépôt contient le client, l’API, les migrations de base de données et des tests automatisés. La prochaine étape du cycle du MVP est la recette avec le développeur, le MJ et les joueurs, puis la correction des remontées et la validation de la version livrée.

La présence du code et des tests ne constitue pas, à elle seule, une recette complète : ce README ne certifie ni le passage de tous les tests, ni la conformité de chaque US, ni les performances en conditions réelles. La validation du MVP intervient lorsque les tests prévus sont réussis et qu’aucune anomalie connue issue de ces tests ne reste à corriger.

| Élément | État de référence |
| --- | --- |
| MVP | Développement réalisé, à soumettre à la recette complète |
| Cahier des charges | V0.12, datée du 13 novembre 2026 ; disponible sur le Drive du projet |
| User stories | Les 22 US du MVP et les US-004/US-005 de V1 sont rédigées ; les autres descriptions de V1 restent à poursuivre |
| Règles métier | RM-001 à RM-024 dans les documents de spécification |
| Modèle de données | MCD et MLD DBML de conception ; adaptations physiques dans les migrations du serveur |
| Évolutions | V1 à découper en versions et en blocs fonctionnels cohérents après le MVP |

La version documentaire **V0.12** et les versions des paquets applicatifs sont indépendantes. Les documents de conception gardent leur historique ; l’état actuel du développement est résumé ici.

## Objectif et périmètre

Le projet accompagne une campagne unique, avec un seul compte MJ. Il est dimensionné pour six joueurs et un MJ dans l’usage habituel, avec une cible de **dix utilisateurs simultanés, MJ compris**.

Les trois axes du produit sont :

- gérer et consulter les feuilles des personnages ;
- fournir au MJ les outils de gestion des joueurs, des PNJ et de la partie ;
- partager les informations et interactions utiles pendant la séance.

L’interface vise les navigateurs d’ordinateur **Chrome et Opera GX**, dans leurs versions stables récentes. L’adaptation aux smartphones et aux tablettes n’est pas prévue dans le périmètre défini.

## Fonctionnalités présentes dans le code

Les modules du dépôt couvrent notamment :

- **Comptes et accès** : inscription, connexion, déconnexion, connexion Google et accès dédié au MJ ;
- **Personnages** : création guidée des PJ, consultation et modification des feuilles, ressources, éléments de feuille et suivi de l’expérience ;
- **Outils MJ** : consultation des joueurs et de leur présence, accès aux feuilles, création et gestion de PNJ complets ou simplifiés, catégories et sous-catégories ;
- **Table et chat** : espace de partie partagé, échanges publics, modification et suppression de messages selon les droits, synchronisation en temps réel ;
- **Images** : bibliothèque du MJ, dossiers d’images et présentation à la table ;
- **Jets de dés** : préparation des jets, diffusion des résultats et relances, avec rendu visuel côté client.

Cette liste décrit les modules observés dans le dépôt. Le référentiel des US définit les critères d’acceptation ; leur validation se fait pendant la recette, et non par cette seule liste.

Les notes autonomes et leur partage, les échanges privés et les rapports de partie font également partie du périmètre documentaire d’évolution. Leur présence dans un MCD ou dans une US ne signifie pas qu’ils sont livrés dans ce MVP. Les développements peuvent aussi intégrer des adaptations postérieures aux documents de conception, par exemple les dossiers d’images ou les paramètres de jets.

## Documentation

**[Ouvrir le dossier Drive du projet](https://drive.google.com/drive/folders/1ZkD0z8W0AA7EC6qMvGnHzyDdI83XnDZX?usp=sharing)**

Le dossier regroupe le cahier des charges, le référentiel des user stories, le MCD et son dictionnaire des données, ainsi que le MLD éditable au format DBML.

| Document | Usage |
| --- | --- |
| [Cahier des charges — V0.12](https://docs.google.com/document/d/1AH2gP3IygUOD2KcT1ADQ7fg1l6sIUSFhlNWSO37huNg/edit) | Vision, périmètre MVP/V1, règles, droits, exigences non fonctionnelles et démarche de livraison |
| [Référentiel des user stories](https://docs.google.com/document/d/1QBpV-EYNmRDmWdZY5g-PIC8MGvQbWj4h10rlfp0ROtI/edit) | Parcours, critères d’acceptation et références aux règles métier |
| [MCD et dictionnaire des données](https://docs.google.com/document/d/1uR9vOImJY_YXE6JWTl2L20HsbynD-bCE/edit) | Six vues conceptuelles, attributs, associations et cardinalités |
| [MLD — DBML](https://drive.google.com/file/d/1PBJQAL8nnlKtMfJuwdRBQkkjpTaMubY5/view) | Base de conception relationnelle éditable |

Les documents de conception précèdent certaines adaptations de l’implémentation et couvrent aussi des évolutions prévues après le MVP. Ils restent les références de cadrage ; le schéma physique mis en œuvre est porté par les migrations du serveur. Leur version documentaire est indépendante de l’état de développement annoncé ci-dessus.

## Architecture

| Composant | Technologies et rôle |
| --- | --- |
| `client/` | Next.js 16, React 19, TypeScript, Tailwind CSS et Zustand ; interface et proxy HTTP `/api/*` |
| `server/` | Python 3.12+, FastAPI, Pydantic, asyncpg ; API, contrôles métier et temps réel WebSocket |
| Supabase | PostgreSQL, authentification et stockage privé des images |
| Visualisation des dés | Three.js, React Three Fiber et cannon-es |
| Tests client | Vitest et Testing Library |
| Tests serveur | pytest, avec contrôles statiques Ruff et mypy |

Les versions exactes sont fixées dans les fichiers de dépendances du dépôt. Les appels HTTP du navigateur passent par le proxy Next.js vers FastAPI. L’adresse de connexion WebSocket est configurée séparément. L’API porte les contrôles d’accès ; les clés secrètes Supabase restent côté serveur.

Le schéma à installer est défini par les fichiers SQL de **[`server/supabase/migrations/`](server/supabase/migrations/)**. Le DBML est une référence de conception, pas un script à importer directement à la place de ces migrations.

## Installation locale

### Prérequis

- Git, Node.js et npm compatibles avec les dépendances du client ;
- **Python 3.12 ou supérieur**, avec `venv` et `pip` ;
- un projet Supabase avec ses paramètres d’authentification, de base de données et de stockage.

### 1. Récupérer le dépôt et installer les dépendances

```bash
git clone https://github.com/Nebji14/WOD-Last-Days_Mvp.git
cd WOD-Last-Days_Mvp
npm ci --prefix client
python -m venv server/.venv
```

Installer ensuite les dépendances Python depuis la racine :

```bash
# Linux / macOS
server/.venv/bin/python -m pip install -r server/requirements-dev.txt
```

```powershell
# Windows PowerShell
.\server\.venv\Scripts\python.exe -m pip install -r server/requirements-dev.txt
```

La racine fournit seulement la commande de lancement ; le client et le serveur conservent chacun leurs dépendances.

### 2. Configurer les environnements

Copier [`server/.env.example`](server/.env.example) en `server/.env` et [`client/.env.example`](client/.env.example) en `client/.env.local`, puis renseigner les valeurs.

| Fichier | Variables principales |
| --- | --- |
| `server/.env` | `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `DATABASE_URL`, `ALLOWED_ORIGINS`, `PUBLIC_APP_URL`, `GM_ACCESS_PATH`, `SESSION_IDLE_SECONDS`, `ENVIRONMENT` |
| `client/.env.local` | `API_URL`, `NEXT_PUBLIC_REALTIME_URL`, `GM_ACCESS_PATH` |

En local, les exemples utilisent le client sur `http://localhost:3000`, l’API sur `http://localhost:8000` et le WebSocket sur `ws://localhost:8000`. `GM_ACCESS_PATH` doit être identique côté client et serveur. `SESSION_IDLE_SECONDS=7200` correspond au réglage indicatif de deux heures d’inactivité.

Ne pas versionner les fichiers `.env` remplis, les identifiants réels, les clés privées ou les sauvegardes de données des joueurs. La clé `SUPABASE_SECRET_KEY` et la chaîne `DATABASE_URL` ne doivent pas être exposées dans les variables publiques du client.

### 3. Préparer Supabase

Sur un projet de développement dédié, appliquer **dans l’ordre** les migrations `0001` à `0007` de [`server/supabase/migrations/`](server/supabase/migrations/), avec l’outil d’administration choisi par le développeur. Le serveur ne les exécute pas automatiquement au démarrage.

La migration des images configure notamment le bucket privé `images`. Les migrations adaptent le MLD aux choix d’implémentation : identité et méthodes de connexion confiées à Supabase Auth, représentation des feuilles, bibliothèques, PNJ et jets.

Pour la connexion Google, configurer le fournisseur dans Supabase et autoriser l’URL de retour `<PUBLIC_APP_URL>/api/auth/google/callback`, conformément à l’exemple d’environnement. Les paramètres des fournisseurs, de confirmation d’inscription et d’envoi des e-mails doivent être vérifiés par le développeur pour l’environnement choisi.

### 4. Initialiser le compte MJ

Depuis `server/`, avec l’environnement Python activé :

```bash
python -m scripts.create_gm
```

Le script demande l’identifiant, l’adresse de récupération et le mot de passe. Cette initialisation est prévue pour le compte MJ unique ; elle ne doit pas être relancée comme une création systématique au démarrage.

### 5. Démarrer l’application

Depuis la racine :

```bash
npm run dev
```

Le lanceur démarre FastAPI et Next.js dans le même terminal. `Ctrl+C` arrête les deux processus.

| Adresse | Usage |
| --- | --- |
| `http://localhost:3000` | Application |
| `http://localhost:3000/<GM_ACCESS_PATH>/connexion` | Accès MJ configuré |
| `http://localhost:8000/api/health` | Vérification de réponse de l’API |
| `http://localhost:8000/api/docs` | Documentation interactive de l’API en développement |

En lancement séparé : `npm run dev` depuis `client/` et `python -m uvicorn app.main:create_app --factory --reload` depuis `server/`, avec son environnement Python activé.

## Vérifications et recette

Commandes existantes côté client, depuis la racine :

```bash
npm --prefix client run lint
npm --prefix client run typecheck
npm --prefix client test
npm --prefix client run build
```

Côté serveur, depuis `server/` avec l’environnement Python activé :

```bash
python -m pytest
python -m ruff check .
python -m mypy app
```

Les fixtures des tests API utilisent des doublures pour les comptes, la base, le stockage et certains services externes. Ces tests ne remplacent donc pas une vérification de l’intégration Supabase réelle ni les essais avec les utilisateurs.

La recette du MVP doit notamment vérifier les parcours joueur et MJ, les droits, les calculs et saisies des feuilles, les PNJ, le chat et les images, ainsi que la continuité après coupure de connexion. Les exigences du cahier des charges comprennent une cible de dix utilisateurs simultanés et une propagation des actions enregistrées en une seconde maximum en conditions normales, après démarrage du service. Ces seuils sont des objectifs à mesurer, pas des résultats attestés par ce README.

## Déploiement et exploitation

Le projet prévoit **Vercel pour le client**, **Render pour le serveur**, et **Supabase pour les données, l’authentification et les images**. Le dépôt indique l’adresse [hunter-last-days.vercel.app](https://hunter-last-days.vercel.app/) pour l’application. La configuration et la validation de l’environnement déployé restent suivies par le développeur.

- Client : construire avec `npm run build`, puis utiliser `npm run start` pour un serveur Next.js hors hébergement géré.
- API : lancer la factory `app.main:create_app` avec Uvicorn ; le port, l’interface d’écoute et les options de production dépendent de l’hébergeur. Exemple : `python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port <PORT>` depuis `server/`.
- En production, utiliser HTTPS/WSS, renseigner les origines et URL publiques, et activer `ENVIRONMENT=production` côté serveur.
- Le temps réel et certains états de table sont gérés en mémoire du processus serveur ; la multiplication des workers ou instances nécessite une étude du partage de ces états.
- Le choix du dispositif de sauvegarde appartient au développeur. La tolérance documentaire est une perte maximale de sept jours de données après incident, avec restauration avant la séance suivante.
- Les maintenances planifiées pouvant interrompre le service se font hors des séances prévues, sauf intervention urgente.

## Suite du projet et contributions

Le MVP suit le cycle **spécification → développement → tests et corrections → validation et livraison**. Après validation, les US de V1 alimentent un backlog organisé par le développeur, avec des livraisons régulières de blocs fonctionnels cohérents. Aucun rythme de sprint chiffré n’est imposé.

Pour signaler une anomalie, fournir les étapes de reproduction, le résultat attendu, le résultat observé, le navigateur et, si possible, l’US concernée. Les changements de règles ou de périmètre doivent être rapprochés des documents de conception avant d’être considérés comme validés.

La conception fonctionnelle et le suivi sont portés par Axel Sénéchal ; le dépôt est maintenu par [Nebji14](https://github.com/Nebji14). Les contributions documentaires et techniques sont suivies par les commits et les pull requests du dépôt.
