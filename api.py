"""Small local API that lets the React page call the Python scouting model."""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from nearest_neighbors import DATA_DIR, find_similar_players


app = FastAPI(title="ScoutIQ Local Report")
GRAPH_PATH = Path(__file__).parent / "player_similarity.png"

names = pd.concat(
    [
        pd.read_csv(DATA_DIR / "players_attack.csv", usecols=["player"])["player"],
        pd.read_csv(DATA_DIR / "players_midfield.csv", usecols=["player"])["player"],
    ]
)
PLAYER_NAMES = sorted(names.dropna().astype(str).drop_duplicates().tolist(), key=str.casefold)


class ReportRequest(BaseModel):
    player_name: str


@app.get("/api/players")
def search_players(q: str = Query(default="", max_length=80)):
    query = q.strip().casefold()
    if not query:
        return []
    return [name for name in PLAYER_NAMES if name.casefold().startswith(query)][:12]


@app.post("/api/report")
def create_report(request: ReportRequest):
    try:
        return find_similar_players(
            request.player_name,
            show_graph=False,
            return_report=True,
        )
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error


@app.get("/api/graph")
def get_graph():
    if not GRAPH_PATH.exists():
        raise HTTPException(status_code=404, detail="Generate a report to create the graph.")
    return FileResponse(GRAPH_PATH, media_type="image/png", headers={"Cache-Control": "no-store"})
