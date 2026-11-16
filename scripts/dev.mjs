/**
 * Lancement local du projet : serveur FastAPI (port 8000) et client Next.js
 * (port 3000) dans un seul terminal.
 *
 * Réservé au développement. En production, le client est servi par Vercel et
 * le serveur par Render, chacun avec sa propre commande.
 *
 * L'arrêt de l'un des deux processus, ou Ctrl+C, arrête l'autre.
 */
import { spawn, spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const isWindows = process.platform === "win32";

const serverDir = join(root, "server");
const clientDir = join(root, "client");
const python = join(serverDir, ".venv", isWindows ? "Scripts/python.exe" : "bin/python");
const nextBin = join(clientDir, "node_modules", "next", "dist", "bin", "next");

const prerequisites = [
  [python, "environnement Python absent : créer server/.venv puis installer requirements-dev.txt"],
  [nextBin, "dépendances du client absentes : lancer « npm install » dans client/"],
];
for (const [path, hint] of prerequisites) {
  if (!existsSync(path)) {
    console.error(`Lancement impossible, ${hint}.`);
    process.exit(1);
  }
}

const children = [
  spawn(python, ["-m", "uvicorn", "app.main:create_app", "--factory", "--reload"], {
    cwd: serverDir,
    stdio: "inherit",
  }),
  spawn(process.execPath, [nextBin, "dev"], { cwd: clientDir, stdio: "inherit" }),
];

let stopping = false;

/** Arrête un processus et ses descendants (rechargement à chaud, compilateur). */
function terminate(child) {
  if (child.pid === undefined || child.exitCode !== null) {
    return;
  }
  if (isWindows) {
    spawnSync("taskkill", ["/pid", String(child.pid), "/T", "/F"], { stdio: "ignore" });
  } else {
    child.kill("SIGTERM");
  }
}

function stopAll(exitCode) {
  if (stopping) {
    return;
  }
  stopping = true;
  children.forEach(terminate);
  process.exit(exitCode);
}

for (const child of children) {
  child.on("exit", (code) => stopAll(code ?? 0));
  child.on("error", (error) => {
    console.error(`Processus non démarré : ${error.message}`);
    stopAll(1);
  });
}
process.on("SIGINT", () => stopAll(0));
process.on("SIGTERM", () => stopAll(0));
