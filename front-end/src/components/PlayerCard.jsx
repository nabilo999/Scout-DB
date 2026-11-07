import { PlayerPortrait } from "./Artwork";
import ClubBadge from "./ClubBadge";
export default function PlayerCard({ player }) {
  return (
    <section
      className="player-card-shell"
      aria-label="Player identity"
      style={{
        "--club-color": player.clubColor || "var(--red)",
        "--club-text-color": player.clubTextColor || "#fff",
      }}
    >
      <div className="player-card">
        <div className="player-name">
          <h2>{player.name}</h2>
        </div>
        <div className="player-details">
          <div className="portrait-space">
            <PlayerPortrait />
          </div>
          <div className="identity-stats">
            <div className="club-name">
              <ClubBadge
                key={player.clubBadgeUrl || player.club}
                name={player.club}
                url={player.clubBadgeUrl}
              />
              <span>{player.club}</span>
            </div>
            <div className="headline-stats">
              {[
                ["PCTL", player.percentile],
                ["POS", player.position],
                ["AGE", player.age],
              ].map(([label, value]) => (
                <div key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                </div>
              ))}
            </div>
            <dl className="status-stats">
              <div>
                <dt>VALUE</dt>
                <dd>{player.value}</dd>
              </div>
              <div>
                <dt>FITNESS</dt>
                <dd className="fit">{player.fitness}</dd>
              </div>
              <div>
                <dt>DEVELOPMENT</dt>
                <dd className="improving">{player.development}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </section>
  );
}
