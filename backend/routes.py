from fastapi import APIRouter, HTTPException
from . import crud
from .models import User
from .password_util import hash_password, verify_password
router = APIRouter()

# endpoint related to the basic webapp
@router.get("/track")
def get_track():
    return crud.get_track()

@router.post("/register")
def register(user: User):
    hashed_password = hash_password(user.password)
    dbuser = crud.create_user(user.username, hashed_password)
    if not dbuser:
        raise HTTPException(status_code=400, detail="Username already exists")

    return {'user_id': dbuser['user_id'],
            'user_name': dbuser['user_name']}


@router.post("/login")
def login(user: User):
    dbuser = crud.authenticate_user(user.username)
    if not dbuser or not verify_password(user.password, dbuser['hashed_password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {'user_id': dbuser['user_id'],
            'user_name': dbuser['user_name'],
            'is_admin': dbuser['is_admin']}


@router.get("/verify_user")
def verify_user(user_id: int, user_name: str):
    result = crud.user_exists(user_id, user_name)
    if not result or not result['is_user_exists']:
        raise HTTPException(status_code=404, detail="User not found")
    return {"is_admin": result['is_admin']}