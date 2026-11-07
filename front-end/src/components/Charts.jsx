export function DistributionChart({ values }) {
  const labels = [
    "Offence",
    "Technique",
    "Physical",
    "Defense",
    "Stamina",
    "Speed",
  ];
  function points(data) {
    return data
      .map((value, index) => {
        const angle = ((index * 60 - 90) * Math.PI) / 180;
        return (
          250 + Math.cos(angle) * value + "," + (126 + Math.sin(angle) * value)
        );
      })
      .join(" ");
  }
  return (
    <svg
      className="distribution-chart"
      viewBox="0 0 500 250"
      role="img"
      aria-label="Attribute distribution across six categories"
    >
      <polygon
        points={points([92, 92, 92, 92, 92, 92])}
        fill="#39464a"
        stroke="#26343b"
        strokeWidth="8"
      />
      <polygon
        points={points([86, 86, 86, 86, 86, 86])}
        fill="none"
        stroke="#c5ac65"
        strokeWidth="5"
      />
      <polygon
        points={points(values.map((value) => value * 0.76))}
        fill="#ffffff12"
        stroke="#eceff0"
        strokeWidth="3"
      />
      {labels.map((label, index) => {
        const angle = ((index * 60 - 90) * Math.PI) / 180;
        return (
          <text
            key={label}
            x={250 + Math.cos(angle) * 150}
            y={131 + Math.sin(angle) * 112}
            textAnchor="middle"
          >
            {label}
          </text>
        );
      })}
    </svg>
  );
}
export function DevelopmentChart({ history }) {
  const first = history[0];
  const last = history[history.length - 1];
  const growth = last.rating - first.rating;
  const seasons = Number(last.season.slice(0, 2)) - Number(first.season.slice(0, 2));
  const average = seasons > 0 ? (growth / seasons).toFixed(1) : "0.0";
  const positions = history.map((item, index) => ({
    x: 110 + index * 155,
    y: 168 - (item.rating - 70) * 5.7,
    ...item,
  }));
  const points = positions.map((item) => item.x + "," + item.y).join(" ");
  return (
    <>
      <svg
        className="development-chart"
        viewBox="0 0 500 200"
        role="img"
        aria-label={"Overall performance: " + history.map(item => item.rating).join(" → ")}
      >
        <text x="260" y="19" textAnchor="middle" className="chart-subtitle">
          Overall Rating / Performance (by season)
        </text>
        {[70, 75, 80, 85, 90].map((value) => (
          <g key={value}>
            <line
              x1="45"
              x2="480"
              y1={168 - (value - 70) * 5.7}
              y2={168 - (value - 70) * 5.7}
              stroke="#ccc"
            />
            <text x="36" y={173 - (value - 70) * 5.7} textAnchor="end">
              {value}
            </text>
          </g>
        ))}
        <path d="M45 54 V168 H480" fill="none" stroke="#222" />
        <polygon points={"110,168 " + points + " 420,168"} fill="#d9e1d9" />
        <polyline
          points={points}
          fill="none"
          stroke="#2c3c44"
          strokeWidth="3"
        />
        {positions.map((item) => (
          <g key={item.season}>
            <circle
              cx={item.x}
              cy={item.y}
              r="4.5"
              fill="#fff"
              stroke="#2c3c44"
              strokeWidth="2.5"
            />
            <text
              x={item.x}
              y={item.y - 10}
              textAnchor="middle"
              fontWeight="bold"
            >
              {item.rating}
            </text>
            <text x={item.x} y="189" textAnchor="middle">
              {item.season}
            </text>
          </g>
        ))}
      </svg>
      <div className="growth-summary">
        <div>
          <strong>{growth >= 0 ? "+" : ""}{growth}</strong>
          <span>
            Growth
            <br />
            ({first.season} → {last.season})
          </span>
        </div>
        <div>
          <strong>{growth >= 0 ? "+" : ""}{average} / season</strong>
          <span>Average Increase</span>
        </div>
        <div>
          <strong>{growth > 0 ? "⬈ Improving" : growth < 0 ? "↘ Declining" : "→ Stable"}</strong>
          <span>Development Trend</span>
        </div>
      </div>
    </>
  );
}
