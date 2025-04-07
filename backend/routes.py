from fastapi import APIRouter
from . import crud
router = APIRouter()

@router.get("/track")
def get_track():
    return crud.get_track()