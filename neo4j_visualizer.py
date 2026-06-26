from neo4j_manager import Neo4jManager, driver, PUBLIC_AS, PRIVATE_AS, ROUTER
from fastapi import FastAPI, HTTPException, Response, Cookie, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from auth_manager import *
import re

local = False

class CypherRequest(BaseModel):
    query: str

class InspectRequest(BaseModel):
    type: str
    id: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CredentialRequest(BaseModel):
    username: str
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

def require_session(session: str | None = Cookie(default=None)):
    if session is None or not authenticate_session(session):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )


@app.get("/api/overview")
def overview(_ = Depends(require_session)):

    with driver.session() as session:
        manager = Neo4jManager(session)

        nodes, edges = manager.overview()

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

@app.post("/api/inspect")
def inspect(request: InspectRequest, _ = Depends(require_session)):
    rq_type = request.type
    rq_id = request.id

    with driver.session() as session:
        manager = Neo4jManager(session)

        if rq_type == PUBLIC_AS:
            nodes, edges = manager.inspect_public_as(int(rq_id))
        elif rq_type == PRIVATE_AS:
            nodes, edges = manager.inspect_private_as(rq_id)
        elif rq_type == ROUTER:
            nodes, edges = manager.inspect_router(rq_id)
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown request type: {rq_type}"
            )

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

@app.post("/api/visualize")
def visualize_query(request: CypherRequest, _ = Depends(require_session)):
    query_lower = request.query.lower()

    # Check to not allow people to change data
    for word in cypher_filter:
        if re.search(rf"\b{word}\b", query_lower):
            raise HTTPException(
                status_code=400,
                detail = f"Query not allowed: the use of '{word.upper()}' is forbidden."
            )

    with driver.session() as session:
        manager = Neo4jManager(session)

        nodes, edges = manager.visualize(request.query)

        return {
            "nodes": list(nodes.values()),
            "edges": _to_cy_edges(edges)
        }

@app.post("/auth/login")
def login(request: LoginRequest, response: Response):
    if not authenticate_user(request.username, request.password):
        raise HTTPException(status_code=401,
                            detail="Incorrect username or password")

    token = gen_session()

    response.set_cookie(
        key="session",
        value=token,
        httponly=True,
        secure=not local,
        samesite="lax",
        max_age=60 * 60 * 24
    )

    return {"success": True}


@app.post("auth/logout")
def logout(response: Response, session: str | None = Cookie(default=None)):
    del_session(session)

    response.delete_cookie(
        key="session",
        httponly=True,
        secure=not local,
        samesite="lax"
    )

    return {"success": True}


@app.post("/auth/generate-credentials")
def generate_credentials(request: CredentialRequest, authorization: str = Header()):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)

    admin_key = authorization[7:]

    password = gen_credentials(request.username, admin_key)

    return {"password": password}

@app.post("/auth/delete-credentials")
def delete_credentials(request: CredentialRequest, authorization: str = Header()):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)

    admin_key = authorization[7:]

    del_credentials(request.username, admin_key)


if local:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")