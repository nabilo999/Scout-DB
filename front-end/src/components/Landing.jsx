import { useState } from "react";
import { ScoutLogo } from "./Artwork";
export default function Landing({ onScout }) {
  const [query, setQuery] = useState("");
  function submit(event) {
    event.preventDefault();
    if (query.trim()) onScout(query.trim());
  }
  return (
    <main className="landing">
      <div className="corner corner-top" aria-hidden="true">
        <i />
        <b />
        <span />
      </div>
      <div className="corner corner-bottom" aria-hidden="true">
        <i />
        <b />
        <span />
      </div>
      <section className="search-content" aria-label="Scout a player">
        <ScoutLogo />
        <form className="search-frame" onSubmit={submit}>
          <div className="search-inner">
            <label className="sr-only" htmlFor="player-search">
              Who are you looking for?
            </label>
            <input
              id="player-search"
              placeholder="What are you looking for?"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              autoComplete="off"
              required
            />
            <button type="submit" disabled={!query.trim()}>
              Scout <span aria-hidden="true">▸</span>
            </button>
          </div>
        </form>
      </section>
    </main>
  );
}
