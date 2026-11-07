# ScoutDB front-end prototype

Scaffolded using create-vite with the React template. No backend, authentication, or model calls.

## Run

`npm install` then `npm run dev`. Production build: `npm run build`.

## Structure

- src/App.jsx: search, 1.5-second loading, report flow.
- src/data/demoPlayer.js: illustrative data and future integration boundary.
- src/components: reusable player card, panels, pagination, charts, attributes and projections.
- src/App.css: visual styles, responsive layout and reduced-motion handling.
- src/components/Artwork.jsx: native text wordmark and reusable SVG person silhouettes; no screenshot artwork is rendered.

Search Moussa Dembélé (or Moussa Dembele) and Will Hughes for their demo reports. Capitalization, accents, and extra spaces are ignored; all other entries fall back to Julian Draxler. Three left pages and two right pages navigate independently, wrapping at either end. On small screens the report stacks vertically. Text, charts, tables and controls are real UI; similar-player crests are placeholders. Matte surfaces share CSS palette variables. Fixed layout slots keep navigation and report dimensions stable across every panel combination. Development summaries are derived from each demo history. Replace these and map real data into demoPlayer's structure when integrating the backend.

Team styling: demoPlayer.clubBadgeUrl supplies the future badge image; clubColor and clubTextColor control the name banner. ClubBadge shows a shield placeholder when a badge is missing or fails to load. No team API is called.

The two added examples use fictional demo-season values and club associations for UI testing, not current statistics. Their complete fixtures live in src/data/moussaDembele.js and src/data/willHughes.js; name matching is in src/data/findDemoPlayer.js.
