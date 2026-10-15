# Main FastAPI application module
from fastapi import FastAPI

app = FastAPI(__name__)

# Import and include the appointment request router
from app.core.routes import include_routers
include_routers(app)