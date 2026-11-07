import Panel from "./Panel";
import { SimilarPortrait } from "./Artwork";
export default function Projections({ player }) {
  return (
    <div className="projection-panels">
      <Panel title="Projected Next Season">
        <table className="projection-table">
          <tbody>
            {player.projections.map(([label, value]) => (
              <tr key={label}>
                <th scope="row">{label}</th>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      <Panel title="5 Similar Players">
        <table className="similar-table">
          <tbody>
            {player.similar.map((item, index) => (
              <tr key={item.name}>
                <td>{index + 1}</td>
                <td>
                  <SimilarPortrait name={item.name} />
                </td>
                <th scope="row">{item.name}</th>
                <td>
                  <span
                    className="mini-crest"
                    style={{ background: item.color }}
                  >
                    {item.club.charAt(0)}
                  </span>{" "}
                  {item.club}
                </td>
                <td>
                  <span className="season-badge">{item.season}</span>
                </td>
                <td>{item.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}
