from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from . import routes

app = FastAPI()

# Include the router
app.include_router(routes.router)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="./frontend"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("./frontend/login/index.html")

@app.get("/basic-webapp")
async def read_root():
    return FileResponse("./frontend/basic_webapp/index.html")


