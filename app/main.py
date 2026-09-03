from fastapi import FastAPI
from app.api.repository import router as repository_router
from app.api.graphs import router as graphs_router
from app.api.understanding import router as understanding_router



app = FastAPI()

app.include_router(repository_router)
app.include_router(graphs_router)
app.include_router(understanding_router)

@app.get("/")
def root():
    return {"message": "Hello World"}
 


