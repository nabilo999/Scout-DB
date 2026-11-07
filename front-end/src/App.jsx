import { useEffect, useState } from "react";
import Landing from "./components/Landing";
import PlayerReport from "./components/PlayerReport";
import { demoPlayer } from "./data/demoPlayer";
import { findDemoPlayer } from "./data/findDemoPlayer";
import "./App.css";
export default function App() {
  const [screen, setScreen] = useState("search");
  const [player, setPlayer] = useState(demoPlayer);
  function scoutPlayer(query) {
    setPlayer(findDemoPlayer(query));
    setScreen("loading");
  }
  useEffect(() => {
    if (screen !== "loading") return;
    const timer = setTimeout(() => setScreen("report"), 1500);
    return () => clearTimeout(timer);
  }, [screen]);
  if (screen === "search")
    return <Landing onScout={scoutPlayer} />;
  if (screen === "loading")
    return (
      <main
        className="loading-screen"
        role="status"
        aria-label="Preparing player report"
      >
        <span className="spinner" />
      </main>
    );
  return (
    <PlayerReport player={player} onBack={() => setScreen("search")} />
  );
}
