# ai_backend/services/dimension.py - UPDATE

import json

with open("ai_backend/data/furniture_data.json", "r") as f:
    FURNITURE_DATA = json.load(f)

def calculate_room_area(length: float, width: float) -> float:
    """Square feet ber koro"""
    return length * width

def get_furniture_dimensions(room_type: str, furniture_type: str, subtype: str):
    """Furniture er size khuje ber koro"""
    return FURNITURE_DATA.get(room_type, {}).get(furniture_type, {}).get(subtype)

def check_furniture_fit(room, furnitures) -> tuple[bool, str]:
    """
    Check koro furniture room e fit hobe kina
    """
    room_area = room.length * room.width  # square feet
    
    # Furniture total area calculate (inches to feet convert)
    total_furniture_area = 0
    for furniture in furnitures:
        # Width * Depth inches theke square feet e convert
        furn_area = (furniture.width * furniture.depth) / 144  # 144 = 12*12
        total_furniture_area += furn_area
    
    # Rule: Furniture 60% er beshi nite pare na
    max_allowed = room_area * 0.60
    
    if total_furniture_area > max_allowed:
        return False, "Please deselect one item because the dimension is bigger."
    
    # Check circulation space (min 3 feet pathway dorkar)
    if total_furniture_area > room_area * 0.50:
        return True, "Fits tightly. Consider removing one item for better movement."
    
    return True, f"All furniture fits comfortably. Using {(total_furniture_area/room_area)*100:.1f}% of floor space."

def check_collision(furnitures: list) -> bool:
    """
    Advanced: Check koro furniture overlap hocche kina
    Eita implement korte complex - pore korbe
    """
    # TODO: Add 2D collision detection
    return True