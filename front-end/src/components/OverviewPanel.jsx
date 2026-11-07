import Panel from "./Panel";
import { DistributionChart, DevelopmentChart } from "./Charts";
export default function OverviewPanel({ player, page }) {
  if (page === 0)
    return (
      <Panel title="Attribute Distribution">
        <DistributionChart values={player.distribution} />
      </Panel>
    );
  if (page === 1)
    return (
      <Panel title="Season Snapshot">
        <table className="snapshot-table">
          <tbody>
            {player.snapshot.map((row) => (
              <tr key={row[0]}>
                <th scope="row">{row[0]}</th>
                <td>{row[1]}</td>
                <th scope="row">{row[2]}</th>
                <td>{row[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    );
  return (
    <Panel title="Development">
      <DevelopmentChart history={player.history} />
    </Panel>
  );
}
