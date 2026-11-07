// Illustrative data only. Map future API results to this structure.
export const demoPlayer = {
  name: "Julian Draxler",
  club: "Wanderers",
  // Future team API fields; no remote badge is loaded in this prototype.
  clubBadgeUrl: null,
  clubColor: "#ed1526",
  clubTextColor: "#ffffff",
  percentile: 86,
  position: "LM",
  age: 25,
  value: "£27,500,000",
  fitness: "Fit",
  development: "Improving",
  snapshot: [
    ["Appearances", "32", "Minutes", "2,483"],
    ["Goals", "8", "Assists", "11"],
    ["Key Passes", "67", "Chances Created", "78"],
    ["Shots on Target", "25", "Shots", "32"],
    ["Passes Completed", "1,842", "Pass Accuracy", "89%"],
  ],
  distribution: [80, 94, 68, 35, 69, 82],
  history: [
    { season: "19–20", rating: 78 },
    { season: "21–22", rating: 83 },
    { season: "22–23", rating: 86 },
  ],
  attributes: [
    {
      title: "Physical",
      rows: [
        ["Acceleration", 79, "Sprint Speed", 78],
        ["Agility", 85, "Balance", 76],
        ["Jumping", 64, "Stamina", 69],
        ["Strength", 62, "Reactions", 80],
      ],
    },
    {
      title: "Mental",
      rows: [
        ["Aggression", 49, "Interceptions", 38],
        ["Attack Position", 76, "Vision", 76],
      ],
    },
    {
      title: "Technical",
      rows: [
        ["Ball Control", 96, "Crossing", 86],
        ["Dribbling", 95, "Finishing", 83],
        ["FK Acc.", 78, "Heading Acc.", 58],
        ["Long Passing", 86, "Short Passing", 91],
        ["Marking", 34, "Shot Power", 91],
        ["Long Shots", 93, "Stand Tackle", 45],
        ["Sliding Tackle", 34, "Volleys", 87],
        ["Curve", 95, "Penalties", 70],
      ],
    },
    {
      title: "Goalkeeping",
      rows: [
        ["GK Diving", 11, "GK Handling", 13],
        ["GK Kicking", 5, "GK Reflexes", 8],
        ["GK Positioning", 13, null, null],
      ],
    },
  ],
  projections: [
    ["Projected Appearances", "34"],
    ["Projected Minutes", "2,621"],
    ["Projected Goals", "10"],
    ["Projected Assists", "14"],
    ["Projected Key Passes", "76"],
    ["Projected Chances Created", "86"],
    ["Projected Shots", "40"],
    ["Projected Percentile Rank", "88th"],
  ],
  similar: [
    {
      name: "Kai Havertz",
      club: "ARS",
      season: "22–23",
      score: "92%",
      color: "#c82028",
    },
    {
      name: "Christopher Nkunku",
      club: "CHE",
      season: "17–18",
      score: "89%",
      color: "#17469e",
    },
    {
      name: "James Maddison",
      club: "TOT",
      season: "20–21",
      score: "88%",
      color: "#182443",
    },
    {
      name: "Florian Wirtz",
      club: "B04",
      season: "23–24",
      score: "87%",
      color: "#bc242b",
    },
    {
      name: "Dani Olmo",
      club: "RBL",
      season: "18–19",
      score: "85%",
      color: "#d62740",
    },
  ],
};
