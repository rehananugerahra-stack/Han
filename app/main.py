from fastapi import FastAPI

from app.database import engine, Base
from app.routers import venues, creators, bookings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Venue Manager",
    description="API for content creators to discover and book venues for their productions.",
    version="1.0.0",
)

app.include_router(venues.router)
app.include_router(creators.router)
app.include_router(bookings.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "Venue Manager"}
