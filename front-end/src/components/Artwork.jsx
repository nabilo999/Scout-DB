export function ScoutLogo() {
  return (
    <div className="scout-logo" aria-label="ScoutDB">
      <span className="logo-scout">SCOUT</span><span className="logo-db">DB</span>
    </div>
  );
}

// One local, reusable silhouette for every player placeholder.
function PersonIcon({ className, label }) {
  return (
    <svg
      className={className}
      viewBox="0 0 100 100"
      role="img"
      aria-label={label}
    >
      <circle cx="50" cy="32" r="18" fill="currentColor" />
      <path d="M15 91v-9c0-18 15-29 35-29s35 11 35 29v9Z" fill="currentColor" />
    </svg>
  );
}

export function PlayerPortrait() {
  return <PersonIcon className="player-portrait" label="Player silhouette" />;
}

export function SimilarPortrait({ name }) {
  return (
    <PersonIcon className="similar-portrait" label={name + " silhouette"} />
  );
}
