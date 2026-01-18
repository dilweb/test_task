from fastapi import FastAPI
import uvicorn

from src.restfulapi.activities import activities
from src.restfulapi.buildings import buildings
from src.restfulapi.organizations import organizations


app = FastAPI(title="RESTful API test task.txt")

app.include_router(buildings.router)
app.include_router(activities.router)
app.include_router(organizations.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)