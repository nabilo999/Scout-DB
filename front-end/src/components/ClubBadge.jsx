import { useState } from "react";

// The same badge slot works with a future API URL or the local placeholder.
export default function ClubBadge({ name, url }) {
  const [failed, setFailed] = useState(false);
  return (
    <span className="club-badge">
      {url && !failed ? (
        <img src={url} alt={name + " badge"} onError={() => setFailed(true)} />
      ) : (
        <svg
          viewBox="0 0 32 36"
          role="img"
          aria-label={name + " badge placeholder"}
        >
          <path
            d="M3 3h26v17c0 7-8 12-13 14C11 32 3 27 3 20Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <text
            x="16"
            y="23"
            textAnchor="middle"
            fill="currentColor"
            fontSize="16"
            fontWeight="bold"
          >
            {name.charAt(0)}
          </text>
        </svg>
      )}
    </span>
  );
}
