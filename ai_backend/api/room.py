# ai_backend/api/room.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from ai_backend.models import RoomDimensions, FurnitureSelection
from ai_backend.services.dimension import calculate_room_area, check_furniture_fit

router = APIRouter()

class RoomRequest(BaseModel):
    length: float
    width: float
    height: float  # Optional for volume, but area is length * width

class FitCheckRequest(BaseModel):
    room: RoomDimensions
    furnitures: list[FurnitureSelection]

@router.post("/dimensions")
def set_room_dimensions(room: RoomRequest):
    area = calculate_room_area(room.length, room.width)
    return {"square_feet": area, "message": "Room dimensions set."}

@router.post("/fit-check")
def check_fit(request: FitCheckRequest):
    fits, message = check_furniture_fit(request.room, request.furnitures)
    if not fits:
        raise HTTPException(status_code=400, detail=message)
    return {"fits": fits, "message": message}