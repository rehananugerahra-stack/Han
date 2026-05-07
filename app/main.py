from fastapi import FastAPI

from app.database import engine, Base
from app.routers import venues, creators, bookings, events, promotions, market_research, competitors, pricing_intel

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Venue Manager",
    description=(
        "API for content creators to discover and book venues for their productions. "
        "Includes event day management, promotional campaigns, and market research "
        "to drive restaurant foot traffic and expand revenue."
    ),
    version="3.0.0",
)

app.include_router(venues.router)
app.include_router(creators.router)
app.include_router(bookings.router)
app.include_router(events.router)
app.include_router(promotions.router)
app.include_router(market_research.router)
app.include_router(competitors.router)
app.include_router(pricing_intel.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "Venue Manager"}
