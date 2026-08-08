from fastapi import FastAPI
from app.api.repository import router as repository_router



app = FastAPI()

app.include_router(repository_router)

@app.get("/")
def root():
    return {"message": "Hello World"}
 


