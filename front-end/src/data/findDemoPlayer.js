import { demoPlayer } from "./demoPlayer.js";
import { moussaDembele } from "./moussaDembele.js";
import { willHughes } from "./willHughes.js";

function normalizeName(name) {
  return name.normalize("NFD").replace(/[\u0300-\u036f]/g, "")
    .trim().toLowerCase().replace(/\s+/g, " ");
}

export function findDemoPlayer(query) {
  const name = normalizeName(query);
  if (name === "moussa dembele") return moussaDembele;
  if (name === "will hughes") return willHughes;
  return demoPlayer;
}
