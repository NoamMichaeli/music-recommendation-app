import random

from fastapi import APIRouter, HTTPException
from . import postgres_crud
from .models import User, Track, CSVUploadRequest, UserTrackRequest
from .password_util import hash_password, verify_password
from typing import List
from .algo import update_user_mean_vector

router = APIRouter()


# endpoint related to the basic webapp
@router.get("/track")
def get_track():
    return postgres_crud.get_track()


@router.post("/register")
def register(user: User):
    hashed_password = hash_password(user.password)
    dbuser = postgres_crud.create_user(user.username, hashed_password)
    if not dbuser:
        raise HTTPException(status_code=400, detail="Username already exists")

    return {'user_id': dbuser['user_id'],
            'user_name': dbuser['user_name']}


@router.post("/login")
def login(user: User):
    dbuser = postgres_crud.authenticate_user(user.username)
    if not dbuser or not verify_password(user.password, dbuser['hashed_password']):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    return {'user_id': dbuser['user_id'],
            'user_name': dbuser['user_name'],
            'is_admin': dbuser['is_admin']}


@router.get("/verify_user")
def verify_user(user_id: int, user_name: str):
    result = postgres_crud.user_exists(user_id, user_name)
    if not result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")
    return {"is_admin": result['is_admin']}


@router.get("/like")
def get_likes(user_id: int, user_name: str):
    dict_result = postgres_crud.user_exists(user_id, user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")
    return postgres_crud.get_likes(user_id)


@router.get("/dislike")
def get_dislikes(user_id: int, user_name: str):
    dict_result = postgres_crud.user_exists(user_id, user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")
    return postgres_crud.get_dislikes(user_id)


@router.get("/recommendation", response_model=List[Track])
def get_recommendations(user_id: int, user_name: str, is_from_button: bool, is_user_ignored_recommendations: bool):
    dict_result = postgres_crud.user_exists(user_id, user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")
    tracks = postgres_crud.get_random_10_tracks()
    # Add missing keys
    types = ["user_history", "similar_users"]
    for i, item in enumerate(tracks):
        item["relevance_percentage"] = random.randint(80, 99)  # or any logic you want
        item["recommendation_type"] = types[i % len(types)]  # alternate types

    return tracks


@router.post("/like/csv")
def upload_csv(request: CSVUploadRequest):
    dict_result = postgres_crud.user_exists(request.user_id, request.user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")

    affected_rows = postgres_crud.upload_csv(request.user_id, request.track_ids)
    if affected_rows == 0:
        return {"status": "200", "message": "All liked tracks already exist", "affected_rows": affected_rows}
    else:
        update_user_mean_vector(request.user_id)
        return {"status": "200", "message": "Likes were added successfully", "affected_rows": affected_rows}


@router.post("/like")
def add_like_route(request: UserTrackRequest):
    dict_result = postgres_crud.user_exists(request.user_id, request.user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")
    success, message, affected_rows = postgres_crud.add_like(request.user_id, request.track_id)
    if success:
        update_user_mean_vector(request.user_id)
    return {"status": "200", "message": message, "affected_rows": affected_rows}


@router.post("/dislike")
def add_dislike(request: UserTrackRequest):
    dict_result = postgres_crud.user_exists(request.user_id, request.user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")

    postgres_crud.add_dislike(request.user_id, request.track_id)
    # stats_postgres_crud.user_disliked_recommended_track_report(request.user_id, request.track_id, request.recommendation_type)
    return {"status": "200"}


@router.delete("/like")
def remove_like(request: UserTrackRequest):
    dict_result = postgres_crud.user_exists(request.user_id, request.user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")

    postgres_crud.remove_like(request.user_id, request.track_id)
    update_user_mean_vector(request.user_id)
    return {"status": "200"}


@router.delete("/dislike")
def remove_dislike(request: UserTrackRequest):
    dict_result = postgres_crud.user_exists(request.user_id, request.user_name)
    if not dict_result.get("is_user_exists", False):
        raise HTTPException(status_code=404, detail="User not found")

    postgres_crud.remove_dislike(request.user_id, request.track_id)
    return {"status": "200"}