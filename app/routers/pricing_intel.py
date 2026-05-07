"""
Competitive Pricing Intelligence
----------------------------------
Analyses competitor menu prices vs. your own to surface:
  - Market average price per category
  - Where you are priced above / below / on-par with the market
  - Specific recommendations to stay competitive without a race to the bottom
"""
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Competitor, CompetitorMenuItem, MenuCategory

router = APIRouter(prefix="/pricing", tags=["pricing intelligence"])


# ── helpers ───────────────────────────────────────────────────────────────────

def _avg(values: List[float]) -> float:
    return round(sum(values) / len(values), 2) if values else 0.0


def _position(our_price: float, market_avg: float) -> str:
    diff_pct = (our_price - market_avg) / market_avg * 100 if market_avg else 0
    if diff_pct > 10:
        return "above_market"
    if diff_pct < -10:
        return "below_market"
    return "competitive"


def _recommendation(our_price: float, market_avg: float, market_min: float, market_max: float, item: str) -> str:
    diff_pct = (our_price - market_avg) / market_avg * 100 if market_avg else 0
    if diff_pct > 20:
        suggested = round(market_avg * 1.05, 2)
        return (
            f"'{item}' is priced {diff_pct:.0f}% above market average (${market_avg}). "
            f"Risk of losing price-sensitive customers. Consider lowering to ${suggested} "
            f"to stay premium but competitive."
        )
    if diff_pct < -15:
        suggested = round(market_avg * 0.95, 2)
        return (
            f"'{item}' is priced {abs(diff_pct):.0f}% below market average (${market_avg}). "
            f"You are leaving money on the table. Raise to ${suggested} — "
            f"still cheaper than most competitors while improving your margin."
        )
    return (
        f"'{item}' is competitively priced at ${our_price} vs. market avg ${market_avg} "
        f"(range ${market_min}–${market_max}). No immediate action needed."
    )


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/overview", summary="Full market pricing overview by category")
def pricing_overview(
    max_distance: Optional[int] = Query(None, description="Only include competitors within this distance (metres)"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    q = db.query(CompetitorMenuItem).join(Competitor)
    if max_distance is not None:
        q = q.filter(Competitor.distance_meters <= max_distance)
    items = q.all()

    if not items:
        return {
            "message": "No competitor menu data yet.",
            "next_step": "Add competitors via POST /competitors/ then log their menu items via POST /competitors/{id}/menu",
        }

    # Group by category
    by_cat: Dict[str, List[float]] = defaultdict(list)
    for item in items:
        by_cat[item.category.value].append(item.price)

    category_stats = {}
    for cat, prices in by_cat.items():
        category_stats[cat] = {
            "item_count": len(prices),
            "market_min": round(min(prices), 2),
            "market_max": round(max(prices), 2),
            "market_avg": _avg(prices),
            "market_median": round(sorted(prices)[len(prices) // 2], 2),
        }

    total_competitors = db.query(Competitor).count()
    if max_distance:
        total_competitors = db.query(Competitor).filter(Competitor.distance_meters <= max_distance).count()

    return {
        "competitors_analysed": total_competitors,
        "total_menu_items_tracked": len(items),
        "pricing_by_category": category_stats,
        "insight": (
            "Use this data to benchmark your menu. Items priced more than 10% above market "
            "average in high-competition categories (beverage, lunch) risk churn. "
            "Items priced below market in premium categories (dinner, alcohol) signal under-monetisation."
        ),
    }


@router.get("/compare", summary="Compare your prices against competitors item by item")
def compare_prices(
    category: Optional[MenuCategory] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    q = db.query(CompetitorMenuItem).filter(CompetitorMenuItem.our_item_price.isnot(None))
    if category:
        q = q.filter(CompetitorMenuItem.category == category)
    items = q.all()

    if not items:
        return {
            "message": "No comparison data yet.",
            "next_step": (
                "When adding competitor menu items, fill in 'our_item_name' and 'our_item_price' "
                "to enable direct item-by-item comparisons."
            ),
        }

    # Group by our item name
    grouped: Dict[str, Dict] = defaultdict(lambda: {
        "our_price": None, "competitor_prices": [], "our_item_name": None, "category": None
    })

    for item in items:
        key = item.our_item_name
        grouped[key]["our_price"] = item.our_item_price
        grouped[key]["our_item_name"] = item.our_item_name
        grouped[key]["category"] = item.category.value
        grouped[key]["competitor_prices"].append({
            "competitor": item.competitor.name,
            "their_item": item.name,
            "their_price": item.price,
        })

    comparisons = []
    for key, data in grouped.items():
        competitor_prices = [cp["their_price"] for cp in data["competitor_prices"]]
        market_avg = _avg(competitor_prices)
        market_min = round(min(competitor_prices), 2)
        market_max = round(max(competitor_prices), 2)
        our_price = data["our_price"]
        position = _position(our_price, market_avg)

        comparisons.append({
            "our_item": key,
            "category": data["category"],
            "our_price": our_price,
            "market_avg": market_avg,
            "market_min": market_min,
            "market_max": market_max,
            "position": position,
            "price_difference_pct": round((our_price - market_avg) / market_avg * 100, 1) if market_avg else 0,
            "recommendation": _recommendation(our_price, market_avg, market_min, market_max, key),
            "competitor_breakdown": data["competitor_prices"],
        })

    # Sort: show problem items first
    order = {"above_market": 0, "below_market": 1, "competitive": 2}
    comparisons.sort(key=lambda x: order[x["position"]])

    above = [c for c in comparisons if c["position"] == "above_market"]
    below = [c for c in comparisons if c["position"] == "below_market"]
    competitive = [c for c in comparisons if c["position"] == "competitive"]

    return {
        "items_compared": len(comparisons),
        "summary": {
            "above_market": len(above),
            "competitive": len(competitive),
            "below_market": len(below),
        },
        "pricing_health_score": _health_score(len(above), len(below), len(competitive)),
        "comparisons": comparisons,
    }


@router.get("/gaps", summary="Categories with no competitor data — blind spots in your research")
def pricing_gaps(db: Session = Depends(get_db)) -> Dict[str, Any]:
    tracked_categories = {
        row[0].value
        for row in db.query(CompetitorMenuItem.category).distinct().all()
    }
    all_categories = {c.value for c in MenuCategory}
    missing = all_categories - tracked_categories

    stale_threshold_days = 30
    from datetime import datetime, timedelta
    cutoff = datetime.utcnow() - timedelta(days=stale_threshold_days)
    stale = db.query(Competitor).filter(
        (Competitor.last_surveyed == None) | (Competitor.last_surveyed < cutoff)  # noqa: E711
    ).all()

    return {
        "untracked_categories": sorted(missing),
        "stale_competitors": [
            {
                "id": c.id,
                "name": c.name,
                "last_surveyed": c.last_surveyed,
                "days_since_survey": (
                    (datetime.utcnow() - c.last_surveyed).days if c.last_surveyed else "never"
                ),
            }
            for c in stale
        ],
        "recommendation": (
            f"Re-survey competitors every {stale_threshold_days} days minimum. "
            "Cafe and restaurant pricing shifts with season, ingredient costs, and local events. "
            "Stale data leads to mispriced menus."
        ),
    }


@router.get("/sweet-spot", summary="Suggested price sweet-spot per category to maximise competitiveness")
def sweet_spot(db: Session = Depends(get_db)) -> Dict[str, Any]:
    items = db.query(CompetitorMenuItem).all()
    if not items:
        return {"message": "No competitor data. Add competitors and their menu items first."}

    by_cat: Dict[str, List[float]] = defaultdict(list)
    for item in items:
        by_cat[item.category.value].append(item.price)

    result = {}
    for cat, prices in by_cat.items():
        avg = _avg(prices)
        # Sweet spot = 5% below market avg (attractive) but above cheapest (margin preserved)
        sweet = round(avg * 0.95, 2)
        result[cat] = {
            "market_avg": avg,
            "suggested_sweet_spot": sweet,
            "rationale": (
                f"Pricing at ${sweet} puts you 5% below the ${avg} market average for {cat}. "
                f"This signals value to price-conscious customers without destroying margin. "
                f"Pair with a quality differentiator (locally sourced, larger portion, faster service) "
                f"to justify the positioning."
            ),
        }

    return {"sweet_spot_by_category": result}


def _health_score(above: int, below: int, competitive: int) -> Dict[str, Any]:
    total = above + below + competitive
    if total == 0:
        return {"score": "N/A", "label": "No data"}
    pct_competitive = competitive / total * 100
    if pct_competitive >= 70:
        label = "Healthy"
    elif pct_competitive >= 40:
        label = "Needs attention"
    else:
        label = "Critical — repricing required"
    return {
        "score": f"{pct_competitive:.0f}%",
        "label": label,
        "detail": f"{competitive}/{total} items are competitively priced",
    }
