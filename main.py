from fastapi import FastAPI
from dotenv import load_dotenv
from ai_backend.api import room, furniture, generation

load_dotenv()

app = FastAPI(title="Room Designer API")

app.include_router(room.router, prefix="/room", tags=["room"])
app.include_router(furniture.router, prefix="/furniture", tags=["furniture"])
app.include_router(generation.router, prefix="/generation", tags=["generation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
