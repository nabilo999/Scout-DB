import { useEffect, useMemo, useState } from "react";

const labels = {
  minutes: "Minutes",
  goalsPer90: "Goals / 90",
  non_penalty_goals_per90: "Non-penalty goals / 90",
  xgPer90: "xG / 90",
  xAPer90: "xA / 90",
  assistsPer90: "Assists / 90",
  shotsPer90: "Shots / 90",
  key_passes_Per90: "Key passes / 90",
  buildup_involvement: "Build-up / 90",
  attacking_involvement: "Attacking involvement",
  shot_quality: "Shot quality",
  finishing_expected: "Finishing vs expected",
  share_team_attack: "Share of team attack",
  share_team_buildup: "Share of team build-up",
  chance_quality: "Chance quality",
  distance: "KNN distance",
};

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") {
    return Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2);
  }
  return value;
}

function followingSeason(season) {
  const start = Number(String(season).slice(0, 4));
  return `${start + 1}-${String((start + 2) % 100).padStart(2, "0")}`;
}

function changeFrom(current, projected) {
  if (typeof current !== "number" || typeof projected !== "number" || current <= 0) return null;
  return ((projected - current) / current) * 100;
}

function App() {
  const [name, setName] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [report, setReport] = useState(null);
  const [graphVersion, setGraphVersion] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const query = name.trim();
    if (!query) {
      setSuggestions([]);
      return undefined;
    }

    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(`/api/players?q=${encodeURIComponent(query)}`);
        if (response.ok) setSuggestions(await response.json());
      } catch {
        setSuggestions([]);
      }
    }, 180);

    return () => window.clearTimeout(timer);
  }, [name]);

  const matchFields = useMemo(() => {
    if (!report?.matches?.length) return [];
    const preferred = [
      "goalsPer90",
      "non_penalty_goals_per90",
      "xgPer90",
      "xAPer90",
      "assistsPer90",
      "shotsPer90",
      "key_passes_Per90",
      "buildup_involvement",
      "attacking_involvement",
      "distance",
    ];
    return preferred.filter((field) =>
      report.matches.some((row) => row[field] !== null && row[field] !== undefined),
    );
  }, [report]);

  async function getReport(event) {
    event.preventDefault();
    if (!name.trim()) return;

    setLoading(true);
    setError("");
    setReport(null);
    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ player_name: name.trim() }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Could not create the report.");
      setReport(payload);
      setGraphVersion(Date.now());
      setSuggestions([]);
    } catch (requestError) {
      setError(requestError.message || "The local Python app could not be reached.");
    } finally {
      setLoading(false);
    }
  }

  const prediction = report?.prediction
    ? Object.entries(report.prediction).filter(([, value]) => value !== null)
    : [];
  const currentStats = report?.current_stats || {};

  return (
    <main className="page-shell">
      <section className="search-card" aria-label="Player search">
        <form onSubmit={getReport}>
          <label htmlFor="player-name">Player name</label>
          <div className="search-row">
            <div className="autocomplete">
              <input
                id="player-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                onFocus={() => name.trim() && setSuggestions(suggestions)}
                placeholder="Start typing a player name"
                autoComplete="off"
              />
              {suggestions.length > 0 && (
                <ul className="suggestions" role="listbox">
                  {suggestions.map((suggestion) => (
                    <li key={suggestion}>
                      <button
                        type="button"
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => {
                          setName(suggestion);
                          setSuggestions([]);
                        }}
                      >
                        {suggestion}
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <button className="report-button" type="submit" disabled={loading || !name.trim()}>
              {loading ? "Building report…" : "Get Report"}
              {!loading && <span aria-hidden="true">↗</span>}
            </button>
          </div>
        </form>
        {error && <p className="error-message" role="alert">{error}</p>}
      </section>

      {report && (
        <section className="report-section" aria-live="polite">
          <div className="report-heading">
            <div>
              <h2>{report.player}</h2>
            </div>
            <div className="player-meta">
              <span>{report.position}</span>
              <span>{report.season} profile</span>
            </div>
          </div>

          <section className="panel">
            <div className="panel-heading">
              <div>
                <h3>Top five similar players</h3>
              </div>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Player</th><th>Season</th><th>Club</th><th>Minutes</th>
                    {matchFields.map((field) => <th key={field}>{labels[field] || field}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {report.matches.map((row, index) => (
                    <tr key={`${row.player}-${row.season}`}>
                      <td><span className="rank">0{index + 1}</span>{row.player}</td>
                      <td>{row.season}</td>
                      <td>{row.team}</td>
                      <td>{formatValue(row.minutes)}</td>
                      {matchFields.map((field) => <td key={field}>{formatValue(row[field])}</td>)}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          <section className="panel projection-panel">
            <div className="panel-heading">
              <div>
                <h3>Current season · {report.season}</h3>
              </div>
            </div>
            {Object.keys(currentStats).length ? (
              <div className="prediction-grid current-grid">
                {Object.entries(currentStats).map(([field, value]) => (
                  <div className="prediction-item" key={field}>
                    <span>{labels[field] || field}</span>
                    <strong>{formatValue(value)}</strong>
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-note">Current season stats are unavailable.</p>
            )}
          </section>

          <section className="panel projection-panel">
            <div className="panel-heading">
              <div>
                <h3>Next season outlook · {followingSeason(report.season)}</h3>
              </div>
            </div>
            {prediction.length ? (
              <div className="prediction-grid">
                {prediction.map(([field, value]) => (
                  <div className="prediction-item" key={field}>
                    <span>{labels[field] || field}</span>
                    <strong>{formatValue(value)}</strong>
                    {(() => {
                      const change = changeFrom(currentStats[field], value);
                      return change === null ? null : (
                        <small className={`change-badge ${change > 0 ? "up" : change < 0 ? "down" : "flat"}`}>
                          {change > 0 ? "↑" : change < 0 ? "↓" : "→"} {Math.abs(change).toFixed(1)}%
                        </small>
                      );
                    })()}
                  </div>
                ))}
              </div>
            ) : (
              <p className="empty-note">No comparable players had an observed next-season row.</p>
            )}
          </section>

          <section className="panel graph-panel">
            <div className="panel-heading">
              <div>
                <h3>How close are the comparisons?</h3>
              </div>
            </div>
            <img
              className="similarity-graph"
              src={`/api/graph?version=${graphVersion}`}
              alt={`Ranked similarity distances for ${report.player}`}
            />
          </section>
        </section>
      )}

    </main>
  );
}

export default App;
