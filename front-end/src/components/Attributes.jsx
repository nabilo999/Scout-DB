function Rating({ value }) {
  let color = "red";
  if (value >= 90) color = "dark-green";
  else if (value >= 80) color = "green";
  else if (value >= 70) color = "yellow";
  else if (value >= 50) color = "orange";
  return <span className={"rating rating-" + color}>{value}</span>;
}
export default function Attributes({ groups }) {
  return (
    <div className="attributes">
      {groups.map((group) => (
        <section className="attribute-group" key={group.title}>
          <h3>{group.title}:</h3>
          {group.rows.map((row) => (
            <div className="attribute-row" key={row[0]}>
              <div>
                <span>{row[0]}</span>
                <Rating value={row[1]} />
              </div>
              {row[2] && (
                <div>
                  <span>{row[2]}</span>
                  <Rating value={row[3]} />
                </div>
              )}
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
