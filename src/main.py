import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from src.routes.redmine_request import router as redmine_request_router


app = FastAPI()

app.include_router(redmine_request_router, prefix="/api")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
def read_root():
    return "Redmine API"


if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="debug")
