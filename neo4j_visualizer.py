from neo4j_manager import Neo4jManager, driver
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

class CypherRequest(BaseModel):
    query: str
app = FastAPI()

origins = [
    "https://wesselritskes.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cypher_filter = ["create", "merge", "set", "delete", "detach", "remove", "foreach", "load", "call"]

def _to_cy_edges(edges):
    cy_edges = []

    for src, dst, rel in edges:
        cy_edges.append({
            "data": {
                "id": f"{src}-{dst}-{rel}",
                "source": src,
                "target": dst,
                "relationship": rel
            }
        })

    return cy_edges

@app.get("/api/overview")
def overview():
    with driver.session() as session:
        manager = Neo4jManager(session)

        nodes, edges = manager.overview()

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

@app.get("/api/inspect/{asn}")
def inspect(asn: int):
    with driver.session() as session:
        manager = Neo4jManager(session)

        nodes, edges = manager.inspect(asn)

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

@app.post("/api/visualize")
def visualize_query(request: CypherRequest):
    query_lower = request.query.lower()

    # Check to not allow people to change data
    for word in cypher_filter:
        if re.search(rf"\b{word}\b", query_lower):
            raise HTTPException(
                status_code=400,
                detail = f"Query niet toegestaan: het gebruik van '{word.upper()}' is verboden."
            )

    with driver.session() as session:
        manager = Neo4jManager(session)

        nodes, edges = manager.visualize(request.query)

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

