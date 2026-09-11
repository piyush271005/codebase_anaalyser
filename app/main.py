from fastapi import FastAPI
from app.api.repository import router as repository_router
from app.api.graphs import router as graphs_router
from app.api.understanding import router as understanding_router
from app.api.search import router as search_router
from app.api.retrieval import router as retrieval_router
from app.api.answer import router as answer_router
from dotenv import load_dotenv
load_dotenv()



from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="AI Codebase Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router)
app.include_router(graphs_router)
app.include_router(understanding_router)
app.include_router(search_router)
app.include_router(retrieval_router)
app.include_router(answer_router)

@app.get("/")
def root():
    return {"message": "Hello World"}
 


