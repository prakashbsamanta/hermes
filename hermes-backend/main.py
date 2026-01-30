from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Ensure backend path is in sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from api.routes import router

app = FastAPI(title="Hermes Backtest API", version="0.1.0")

# CORS Configuration
# Allow frontend (React) to access this API
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173", # Vite default
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/")
def read_root():
    return {"status": "Hermes API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
