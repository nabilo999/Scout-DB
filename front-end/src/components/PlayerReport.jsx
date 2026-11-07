import { useState } from "react";
import PlayerCard from "./PlayerCard";
import OverviewPanel from "./OverviewPanel";
import PageControls from "./PageControls";
import Attributes from "./Attributes";
import Projections from "./Projections";
export default function PlayerReport({ player, onBack }) {
  const [overviewPage, setOverviewPage] = useState(0);
  const [detailsPage, setDetailsPage] = useState(0);
  return (
    <main className="report-screen">
      <div className="report-frame">
        <div className="report-inner">
          <section className="report-left">
            <h1>Player Report</h1>
            <PlayerCard player={player} />
            <div className="overview-content" key={overviewPage}>
              <OverviewPanel player={player} page={overviewPage} />
            </div>
            <PageControls
              pages={[
                "Attribute distribution",
                "Season snapshot",
                "Development",
              ]}
              selected={overviewPage}
              onChange={setOverviewPage}
              label="overview page"
            />
          </section>
          <section className="report-right">
            <header className="details-header">
              <h2>ATTRIBUTES</h2>
              <PageControls
                pages={["Player attributes", "Projections and similar players"]}
                selected={detailsPage}
                onChange={setDetailsPage}
                label="details page"
              />
            </header>
            <div className="details-content" key={detailsPage}>
              {detailsPage === 0 ? (
                <Attributes groups={player.attributes} />
              ) : (
                <Projections player={player} />
              )}
            </div>
          </section>
        </div>
      </div>
      <footer className="report-footer">
        <button onClick={onBack}>← New search</button>
      </footer>
    </main>
  );
}
