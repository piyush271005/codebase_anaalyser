from pydantic import BaseModel


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    file_path: str | None = None
    line: int | None = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    line: int | None = None


class Graph(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphRequest(BaseModel):
    repo_url: str


class GraphResponse(BaseModel):
    function_call_graph: Graph
    dependency_graph: Graph
